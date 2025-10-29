import helper
import DB
import LED
import Motor

import os
from rich.console import Console
import traceback

if os.getenv("USER") != "root":
    print("Dieses Programm muss mit superuser-Rechten ausgeführt werden!")
    exit(code=1)

filename = "paternosterregal.db"

db = DB.DB(filename=filename)
led = LED.LED(LED_COUNT=65, LED_PIN = 18)
motor = Motor.Motor(STEP_PIN=17, DIR_PIN=27, HALL_PIN=22, PAUSE_TIME=0.005)

is_position_known = False
            
def main_menu():
    
    options = (("Referenzfahrt", homing),
               ("Teile ein- & auslagern", add_remove_parts),
               ("Datenbank anzeigen", print_db),
               ("Datenbank durchsuchen", search_db),
               ("Fach hinzufügen", add_compartment),
               ("Fach bearbeiten / löschen", compartment_menu),
               ("Ware erstellen", add_part),
               ("Ware bearbeiten / löschen", part_menu),
               ("Sicherung...", backup_menu),
               ("=== Testfunktionen ===", helper.nothing),
               ("Datenbank zurücksetzen", reset_db),
               ("Motorposition zurücksetzen", reset_motor_position),
               ("Motor steuern manuell", manual_motorcontrol),
               ("Motor steuern manuell: Position", manual_motorcontrol_position),
               ("LED-Test", led_test))
    
    helper.menu("Menü", options)
   
def homing():
    helper.reset_screen("Referenzfahrt")
    
    motor.homing()
    global is_position_known
    is_position_known = True
        
    input(f"\nReferenzfahrt erfolgreich abgeschlossen\n> ")

def add_remove_parts():
    helper.reset_screen("Teile ein- & auslagern")
    
    if not is_position_known:
        input("Die aktuelle Position ist unbestimmt. Du musst zunächst eine Referenzfahrt ausführen, bevor du diese Funktion nutzen kannst!\n> ")
        return
    
    search = input("Nach welchen Teilen suchst du?\n> ")
    
    results = helper.search("parts", "label", search, db, like=True)
    
    part_id = helper.run_selection(results)
    
    connections = db.cursor.execute("""
        SELECT 
            parts_compartments.id,
            shelves.label,
            compartments.position,
            compartments.length,
            parts_compartments.stock
        FROM parts_compartments
        JOIN compartments ON parts_compartments.compartment = compartments.id
        JOIN shelves ON compartments.shelf = shelves.id
        WHERE parts_compartments.part = ?""", [part_id]).fetchall()
    
    if len(connections) > 1:
        parts_compartments_id = helper.run_selection([[connection[0], # id
                                                       f"Fach {connection[1]}, {connection[2]}-{connection[2] + connection[3]}: {connection[4]} übrig"] # text
                                                      for connection in connections])
        
    else:
        parts_compartments_id = connections[0][0]
    
    shelf = db.cursor.execute("""SELECT 
                                    shelves.position,
                                    shelves.label,
                                    compartments.position,
                                    compartments.length
                                 FROM parts_compartments
                                 JOIN compartments ON parts_compartments.compartment = compartments.id
                                 JOIN shelves ON compartments.shelf = shelves.id
                                 WHERE parts_compartments.id = ?""", [parts_compartments_id]).fetchone()
    
    if motor.position != shelf[0]:
        if not helper.ask_confirm(f"Bewegung zu Regal \"{shelf[1]}\" beginnen?", True):
            return
        motor.move_to_position(shelf[0])
    
    led.highlight(shelf[2], shelf[2] + shelf[3])
    
    change = helper.ask_integer("Wie viele Teile wurden dazugegeben (+) oder abgegeben (-)?")
    
    led.clear()
    
    stock = db.cursor.execute("SELECT stock FROM parts_compartments WHERE id = ?", (parts_compartments_id,)).fetchone()[0]
    
    db.cursor.execute("UPDATE parts_compartments SET stock = ? WHERE id = ?", (stock + change, parts_compartments_id))
    db.connection.commit()

def print_db():
    
    helper.reset_screen("Übersicht")
    
    print(db.to_string())
        
    input("\n> ")

def search_db():
    helper.reset_screen("Suche")

    search = input("Nach was möchtest du suchen?\n> ")
    
    parts = helper.search("parts", "label", search, db, True)
    
    if len(parts) == 0:
        print(f"\nZu \"{search}\" konnte leider nichts gefunden werden :/\n")
    else:
        print(f"\nZu \"{search}\" konnte folgendes gefunden werden:\n")
        
        results = []
        
        for part in parts:
            print(f"{part[1]}:")
            results = db.cursor.execute("""SELECT 
                                        parts_compartments.stock,
                                        compartments.position,
                                        compartments.length,
                                        shelves.label
                                    FROM parts_compartments
                                    JOIN compartments ON parts_compartments.compartment = compartments.id
                                    JOIN shelves ON compartments.shelf = shelves.id
                                    WHERE parts_compartments.part = ?
                                    ORDER BY
                                        shelves.id ASC,
                                        compartments.id ASC
                                    """, [part[0]]).fetchall()
            
            for result in results:
                print(f" - {result[0]}x in Fach {result[3]}, {result[1]}-{result[2]}")
        
        
    input("> ")

def add_compartment():
    helper.reset_screen("Fach hinzufügen")
    
    ## Regal ##
    
    print("Zu welchem Regal soll das Fach gehören?\n")
    
    for shelf in db.cursor.execute("SELECT id, label FROM shelves").fetchall():
        print(f" ({shelf[0]}) {shelf[1]}")
        
    while True:
        try:
            shelf_id = int(input("\n > "))
            if shelf_id in range(shelf[0] + 1): # range() is zero-index-based
                break
        except ValueError:
            pass
        
        print("\nKeine Valide Eingabe, bitte versuche es erneut:")
    
    ## Position ##
        
    position = helper.ask_integer("An welcher Position soll das Fach beginnen?")
    
    ## Länge ##
        
    length = helper.ask_integer("Wie lang soll das Fach sein?")
    
    ## Eintrag erstellen ##
    
    db.cursor.execute("insert into compartments (shelf, position, length) values (?, ?, ?)", [shelf_id, position, length])
    db.connection.commit()

def compartment_menu(compartment_id: int | None = None):
    if not compartment_id:
        ## Regal ##
        compartments = db.cursor.execute("SELECT shelf FROM compartments").fetchall()
        used_shelf_ids = [str(compartment[0]) for compartment in compartments]
        string_used_shelf_ids = ",".join(used_shelf_ids)
        
        print("Zu welchem Regal gehört das Fach?\n")
        results = db.cursor.execute(f"SELECT id, label FROM shelves WHERE id IN ({string_used_shelf_ids})").fetchall()
        shelf_id = helper.run_selection(results)
        
        ## Fach ##
        results = db.cursor.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall()
        if len(results) == 1:
            compartment_id = results[0][0]
        else:
            print("Welches Fach möchtest du bearbeiten / löschen?\n")
            compartment_id = helper.run_selection([(result[0], f"{result[1]}-{result[1] + result[2]}") for result in results])
        
    connections = db.cursor.execute("""SELECT 
                                       parts_compartments.stock,
                                       parts.label
                                       FROM parts_compartments
                                       JOIN parts ON parts_compartments.part = parts.id
                                       WHERE parts_compartments.compartment = ?""", [compartment_id])
    
    pretext = "\nDieses Fach beinhaltet:\n " + "\n ".join([f"{connection[0]}x {connection[1]}" for connection in connections])
    
    options = [("Regalzuordnung bearbeiten", edit_compartment_shelf),
               ("Startposition bearbeiten", edit_compartment_startingposition),
               ("Länge bearbeiten", edit_compartment_length),
               ("Fach löschen", delete_compartment)]
        
    if helper.menu(f"Fach #{compartment_id} bearbeiten", options, pretext, compartment_id) == 1:
        return
    
    compartment_menu(compartment_id)

def edit_compartment_shelf(compartment_id: int):
    
    current_shelf = db.cursor.execute("SELECT shelves.id, shelves.label FROM compartments JOIN shelves ON compartments.shelf = shelves.id WHERE compartments.id = ?", [compartment_id]).fetchone()
    
    helper.reset_screen(f"Fach: Regalzuordnung bearbeiten (Aktuell: {current_shelf[1]})")
    
    print("Welchem Regal soll Fach zugeordnet werden?\n")
    
    for shelf in db.cursor.execute("SELECT id, label FROM shelves").fetchall():
        if shelf[0] != current_shelf[0]:
            print(f" ({shelf[0]}) {shelf[1]}")
        
    while True:
        try:
            shelf_id = int(input("\n > "))
            if shelf_id in range(shelf[0] + 1): # range() is zero-index-based
                break
        except ValueError:
            pass
        
        print("\nKeine Valide Eingabe, bitte versuche es erneut:")
    
    if helper.ask_confirm(bias=True):
        db.cursor.execute("UPDATE compartments SET shelf = ? WHERE id = ?", (shelf_id, compartment_id))
        db.connection.commit()

def edit_compartment_startingposition(compartment_id: int):
    helper.reset_screen("Fach: Startposition bearbeiten")
    
    position = helper.ask_integer("An welche Startposition soll das Fach verschoben werden?")
    
    if helper.ask_confirm(bias=True):
        db.cursor.execute("UPDATE compartments SET position = ? WHERE id = ?", (position, compartment_id))
        db.connection.commit()

def edit_compartment_length(compartment_id: int):
    helper.reset_screen("Fach: Länge bearbeiten")
    
    length = helper.ask_integer("Wie lang soll das Fach werden?")
    
    if helper.ask_confirm(bias=True):
        db.cursor.execute("UPDATE compartments SET length = ? WHERE id = ?", (length, compartment_id))
        db.connection.commit()

def delete_compartment(compartment_id: int):
    helper.reset_screen("Fach löschen")
    
    ## Eintrag löschen ##
    
    infos = db.cursor.execute("SELECT position, length FROM compartments WHERE id = ?", [compartment_id]).fetchone()
    
    if helper.ask_confirm(f"Sicher, dass du Fach {compartment_id} ({infos[0]}-{infos[0] + infos[1]}) löschen willst?"):
        db.cursor.execute("delete FROM compartments WHERE id = ?", [compartment_id])
        db.connection.commit()
    else:
        input("\nInfo: Vorgang abgebrochen. > ")

def add_part():
    helper.reset_screen("Ware hinzufügen")
    
    ## Bezeichnung ##
        
    label = input("Wie lautet die Bezeichnung der neuen Ware?\n> ")
    
    ## Eintrag erstellen ##
    
    db.cursor.execute("insert into parts (label) values (?)", [label])
    part_id = db.cursor.lastrowid
    db.connection.commit()
    
    ## Ware einem Fach zuordnen
    
    if helper.ask_confirm(f"Ware \"{label}\" erfolgreich erstellt. Möchtest du diese noch einem Fach zuordnen?", bias=True):
        
        ## Regal ##
        
        print("\nZu welchem Regal gehört das Fach?\n")
        
        compartments = db.cursor.execute("SELECT shelf FROM compartments").fetchall()
        used_shelves = [x[0] for x in compartments]
        
        for shelf in db.cursor.execute("SELECT id, label FROM shelves").fetchall():
            if shelf[0] in used_shelves:
                print(f" ({shelf[0]}) {shelf[1]}")
            
        while True:
            try:
                shelf_id = int(input("\n > "))
                if shelf_id in range(shelf[0] + 1): # range() is zero-index-based
                    break
            except ValueError:
                pass
            
            print("\nKeine Valide Eingabe, bitte versuche es erneut:")
        
        ## Fach ##
        
        print("Welchem Fach möchtest du die Ware zuordnen?")
        
        for compartment in db.cursor.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall():
            print(f" ({compartment[0]}) {compartment[1]}-{compartment[2]}")
            
        while True:
            try:
                compartment_id = int(input("\n > "))
                if compartment_id in range(compartment[0] + 1): # range() is zero-index-based
                    break
            except ValueError:
                pass
            
            print("\nKeine Valide Eingabe, bitte versuche es erneut:")
        
        ## Stückzahl
        
        stock = helper.ask_integer("Wie viele Teile werden eingelagert?")
    
        ## Verbindung Herstellen
    
        db.cursor.execute("INSERT INTO parts_compartments (part, compartment, stock) VALUES (?, ?, ?)", [part_id, compartment_id, stock])
        db.connection.commit()
        
        compartment = db.cursor.execute("SELECT shelves.label, compartments.position, compartments.length FROM compartments JOIN shelves ON compartments.shelf = shelves.id WHERE compartments.id = ?", [compartment_id]).fetchone()
        
        input(f"\nWare \"{label}\" erfolgreich Regal {compartment[0]}, ({compartment[1]}-{compartment[1] + compartment[2]}) hinzugefügt\n> ")   

def part_menu(part_id: int | None = None, label: str | None = None):
    if not part_id:
        ## Ware erfragen
        while True:
            helper.reset_screen("Ware bearbeiten / löschen")

            search = input("Welche Ware möchtest du bearbeiten?\n> ")
            if search != "":
                break
        
        results = helper.search("parts", "label", search, db, True)
        
        match len(results):
            case 0:
                input(f"\nZu \"{search}\" konnte leider keine Ware gefunden werden :/\n> ")
                return
            case 1:
                part_id = results[0][0]
            case _:
                print(f"\nZu \"{search}\" konnte folgende Waren gefunden werden:\n")
                part_id = helper.run_selection(results)
    
    parts_compartments = db.cursor.execute("""SELECT
                                                  parts_compartments.id,
                                                  shelves.label,
                                                  compartments.id,
                                                  compartments.position,
                                                  compartments.length,
                                                  parts_compartments.stock
                                              FROM parts_compartments 
                                              JOIN compartments ON parts_compartments.compartment = compartments.id
                                              JOIN shelves ON compartments.shelf = shelves.id
                                              WHERE parts_compartments.part = ?
                                              ORDER BY
                                                  shelves.label ASC,
                                                  compartments.id ASC,
                                                  compartments.position ASC""", [part_id]).fetchall()
    
    if len(parts_compartments) > 0:
        pretext = "\nGelagert in:\n " + "\n ".join([f"Regal {pc[1]}, Fach {pc[2]} ({pc[3]}-{pc[3] + pc[4]}): {pc[5]}x" for pc in parts_compartments])
    
    options = [("Bezeichnung ändern", change_label),
               ("Stückzahl bearbeiten", change_stock),
               ("Fachzuordnung hinzufügen", assign_part_to_compartment),
               ("Fachzuordnung verschieben", move_part_to_compartment),
               ("Fachzuordnung löschen", remove_part_from_compartment),
               ("Teil Löschen", remove_part)]
    
    label = db.cursor.execute("SELECT label FROM parts WHERE id = ?", [part_id]).fetchone()[0]
        
    if helper.menu(f"Ware \"{label}\"", options, pretext, part_id, label) == 1:
        return
    
    part_menu(part_id, label)
    
def change_label(part_id: int, old_label: str):
    helper.reset_screen("Warenbezeichnung ändern")
    
    new_label = input(f"Wie soll die Ware \"{old_label}\" in Zukunft heißen?\n> ")
    
    if helper.ask_confirm(f"Sicher, dass du \"{old_label}\" in \"{new_label}\" umbenennen willst?", bias=True):
        db.cursor.execute("UPDATE parts SET label = ? WHERE id = ?", [new_label, part_id])
        db.connection.commit()
    else:
        input("\nInfo: Vorgang abgebrochen. > ")

def change_stock(part_id: int, label: str):
    helper.reset_screen("Stückzahl bearbeiten")
    
    results = db.cursor.execute("""SELECT 
                                           parts_compartments.id,
                                           parts_compartments.stock, 
                                           compartments.id, 
                                           compartments.position, 
                                           compartments.length, 
                                           shelves.label 
                                       FROM parts_compartments 
                                       JOIN compartments ON parts_compartments.compartment = compartments.id 
                                       JOIN shelves ON compartments.shelf = shelves.id 
                                       WHERE parts_compartments.part = ?""", [part_id]).fetchall()
    
    match len(results):
        case 0:
            helper.no_results()
            return
        case 1:
            parts_compartments_id = results[0][0]
        case _:
            print(f"Bei welcher Fachzuordnung möchtest du die Stückzahl von \"{label}\" ändern?\n")
            parts_compartments_id = helper.run_selection([(result[0], f"{result[1]}x in Regal {result[5]}, Fach {result[2]} ({result[3]}-{result[3]+result[4]})") for result in results])
    
    new_stock = helper.ask_integer("Wie viele Teile sollen hier gelagert werden?")
    
    db.cursor.execute("UPDATE parts_compartments SET stock = ? WHERE id = ?", [new_stock, parts_compartments_id])
    db.connection.commit()

def assign_part_to_compartment(part_id: int, label: str):
    helper.reset_screen(f"Ware \"{label}\" einem Fach zuordnen")

    ## Regal ##
    
    print("\nZu welchem Regal gehört das Fach, dem du die Ware zuordnen willst?\n")
    
    compartments = db.cursor.execute("SELECT shelf FROM compartments").fetchall()
    used_shelves = [x[0] for x in compartments]
    
    for shelf in db.cursor.execute("SELECT id, label FROM shelves").fetchall():
        if shelf[0] in used_shelves:
            print(f" ({shelf[0]}) {shelf[1]}")
        
    while True:
        try:
            shelf_id = int(input("\n > "))
            if shelf_id in range(shelf[0] + 1): # range() is zero-index-based
                break
        except ValueError:
            pass
        
        print("\nKeine Valide Eingabe, bitte versuche es erneut:")
    
    ## Fach ##
    
    print("Welchem Fach möchtest du die Ware zuordnen?")
    
    for compartment in db.cursor.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall():
        print(f" ({compartment[0]}) {compartment[1]}-{compartment[2]}")
        
    while True:
        try:
            compartment_id = int(input("\n > "))
            if compartment_id in range(compartment[0] + 1): # range() is zero-index-based
                break
        except ValueError:
            pass
        
        print("\nKeine Valide Eingabe, bitte versuche es erneut:")
    
    ## Stückzahl
    
    stock = helper.ask_integer("Wie viele Teile werden eingelagert?")

    ## Verbindung Herstellen

    db.cursor.execute("INSERT INTO parts_compartments (part, compartment, stock) VALUES (?, ?, ?)", [part_id, compartment_id, stock])
    db.connection.commit()
    
    compartment = db.cursor.execute("SELECT shelves.label, compartments.position, compartments.length FROM compartments JOIN shelves ON compartments.shelf = shelves.id WHERE compartments.id = ?", [compartment_id]).fetchone()
    
    input(f"\n{stock}x Ware \"{label}\" erfolgreich Regal {compartment[0]}, ({compartment[1]}-{compartment[1] + compartment[2]}) hinzugefügt\n> ")

def move_part_to_compartment(part_id: int, label: str):
    helper.reset_screen(f"Fachzuordnung von Ware {label} verschieben")
    
    ## Zuordnung ##
    parts_compartments = db.cursor.execute("""SELECT
                                                  parts_compartments.id,
                                                  shelves.label,
                                                  compartments.id,
                                                  compartments.position,
                                                  compartments.length
                                              FROM parts_compartments 
                                              JOIN compartments ON parts_compartments.compartment = compartments.id
                                              JOIN shelves ON compartments.shelf = shelves.id
                                              WHERE parts_compartments.part = ?""", [part_id]).fetchall()
    
    match len(parts_compartments):
        case 0:
            helper.no_results()
            return
        case 1:
            print(f"Diese Ware befindet sich zur Zeit in Fach {parts_compartments[2]} ({parts_compartments[1]}, {parts_compartments[3]}-{parts_compartments[3] + parts_compartments[4]}.\n")
            parts_compartments_id = parts_compartments[0][0]
        case _:
            print("Welche Zuordnung möchtest du verschieben?")
            parts_compartments_id = helper.run_selection([(pc[0], f"Regal {pc[1]}, Fach {pc[2]} ({pc[3]}-{pc[3] + pc[4]})") for pc in parts_compartments])
    
    ## Regal ##
    compartments = db.cursor.execute("SELECT shelf FROM compartments").fetchall()
    used_shelf_ids = [str(compartment[0]) for compartment in compartments]
    string_used_shelf_ids = ",".join(used_shelf_ids)
    
    print("Zu welchem Regal gehört das Fach, in das du die Ware verschieben willst?\n")
    results = db.cursor.execute(f"SELECT id, label FROM shelves WHERE id IN ({string_used_shelf_ids})").fetchall()
    shelf_id = helper.run_selection(results)
    
    ## Fach ##
    print("In welches Fach möchtest du die Ware verschieben?\n")
    results = db.cursor.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall()
    compartment_id = helper.run_selection([(result[0], f"{result[1]}-{result[1] + result[2]}") for result in results])

    ## Verbindung verschieben ##
    
    old = db.cursor.execute("""SELECT
                                   shelves.label,
                                   compartments.id,
                                   compartments.position,
                                   compartments.length
                               FROM parts_compartments
                               JOIN compartments ON parts_compartments.compartment = compartments.id
                               JOIN shelves ON compartments.shelf = shelves.id
                               WHERE parts_compartments.id = ?""", [parts_compartments_id]).fetchone()
    
    db.cursor.execute("UPDATE parts_compartments SET compartment = ? WHERE id = ?", [compartment_id, parts_compartments_id])
    db.connection.commit()
    
    new = db.cursor.execute("SELECT shelves.label, compartments.id, compartments.position, compartments.length FROM compartments JOIN shelves ON compartments.shelf = shelves.id WHERE compartments.id = ?", [compartment_id]).fetchone()
    
    input(f"\nWare \"{label}\" erfolgreich von\n- Regal {old[0]}, Fach {old[1]} ({old[2]}-{old[2] + old[3]})\nnach\n- Regal {new[0]}, Fach {new[1]} ({new[2]}-{new[2] + new[3]}) verschoben\n> ")

def remove_part_from_compartment(part_id: int, label: str):
    helper.reset_screen(f"Fachzuordnung von Ware \"{label}\" löschen")
    
    ## Zuordnung ##
    parts_compartments = db.cursor.execute("""SELECT
                                                  parts_compartments.id,
                                                  shelves.label,
                                                  compartments.id,
                                                  compartments.position,
                                                  compartments.length,
                                                  parts_compartments.stock
                                              FROM parts_compartments 
                                              JOIN compartments ON parts_compartments.compartment = compartments.id
                                              JOIN shelves ON compartments.shelf = shelves.id
                                              WHERE parts_compartments.part = ?""", [part_id]).fetchall()
    
    match len(parts_compartments):
        case 0:
            helper.no_results()
            return
        case 1:
            print(f"Diese Ware befindet sich zur Zeit in Fach {parts_compartments[2]} ({parts_compartments[1]}, {parts_compartments[3]}-{parts_compartments[3] + parts_compartments[4]}.\n")
            parts_compartments_id = parts_compartments[0][0]
        case _:
            print("Welche Zuordnung möchtest du löschen?")
            parts_compartments_id = helper.run_selection([(pc[0], f"Regal {pc[1]}, Fach {pc[2]} ({pc[3]}-{pc[3] + pc[4]}): {pc[5]}x") for pc in parts_compartments])
    
    connection = db.cursor.execute("""SELECT
                                          parts_compartments.id,
                                          shelves.label,
                                          compartments.id,
                                          compartments.position,
                                          compartments.length,
                                          parts_compartments.stock
                                      FROM parts_compartments 
                                      JOIN compartments ON parts_compartments.compartment = compartments.id
                                      JOIN shelves ON compartments.shelf = shelves.id
                                      WHERE parts_compartments.id = ?""", [parts_compartments_id]).fetchone()
    
    string = f"{connection[5]}x Ware \"{label}\" in Fach {connection[2]} (Regal {connection[1]}, {connection[3]}-{connection[3] + connection[4]})"
    
    if helper.ask_confirm("Sicher, dass du " + string + " löschen willst?"):
        db.cursor.execute("DELETE from parts_compartments WHERE id = ?", [parts_compartments_id])
        input(string + " erfolgreich gelöscht\n> ")
    else:
        input("Info: Vorgang abgebrochen > ")

def remove_part(part_id: int, label: str):
    while True:
        helper.reset_screen("Ware löschen")

        search = input("Welche Ware möchtest du löschen?\n> ")
        if search != "":
            break
    
    results = helper.search("parts", "label", search, db, True)
    
    part_id = helper.run_selection(results)
    
    if helper.ask_confirm(f"Bist du dir sicher, dass du die Ware \"{label}\" und all ihre Lagerbestände löschen willst?"):
        db.cursor.execute("DELETE FROM parts WHERE id = ?", [part_id])
        db.connection.commit()
    else:
        input("\nInfo: Vorgang abgebrochen. > ")

def backup_menu():
    options = [("...exportieren", export_backup),
               ("...importieren", import_backup)]
        
    helper.menu("Sicherung...", options)

def export_backup():
    if helper.ask_confirm(f"Sicher, dass du die Datenbank nach /home/pi/Downdloads/ kopieren willst? Evtl. bestehende Dateien mit dem Namen \"{filename}\" werden überschrieben!"):
        cwd = os.getcwd()
        helper.copy_and_replace(cwd + "/" + filename, "/home/pi/Downloads/" + filename)
    else:
        input("Vorgang abgebrochen.\n> ")

def import_backup():
    if helper.ask_confirm(f"Sicher, dass du die Datenbank (\"/home/pi/Downdloads/{filename}\") importieren willst? Alle jetzigen Informationen gehen dabei verloren!"):
        cwd = os.getcwd()
        helper.copy_and_replace("/home/pi/Downloads/" + filename, cwd + "/" + filename)
        
        global db
        db = DB.DB(filename=filename)
    else:
        input("Vorgang abgebrochen.\n> ")

# Unsorted / Test Functions

def reset_db():
    helper.reset_screen("Zurücksetzen")
    
    if not helper.ask_confirm("Sicher, dass du die Tabelle zurücksetzen willst?"):
        return

    if helper.ask_confirm("Willst du die Tabelle danach wieder mit Standartwerten füllen?"):
        db.reset(insert_default_testing_values=True)
    else:
        db.reset(insert_default_testing_values=False)

def manual_motorcontrol():
    helper.reset_screen("Motorsteuerung manuel")
    
    print("Gib an, wie viele Schritte der Motor fahren soll. KeyboardInterrupt zum beenden.")
    
    try:
        while True:
            string = input("> ")
            if string != "":
                motor.move_step(int(string))
    except KeyboardInterrupt:
        return
    
def manual_motorcontrol_position():
    helper.reset_screen("Motorsteuerung manuel auf Position")
    
    print("Gib an, zu welcher Position der Motor fahren soll. KeyboardInterrupt zum beenden.")
    
    try:
        while True:
            string = input("> ")
            if string != "":
                motor.move_to_position(int(string))
    except KeyboardInterrupt:
        return

def print_motor_position():
    helper.reset_screen("Motorposition")
    
    input(str(motor.position) + "\n> ")

def reset_motor_position():
    motor.position = 0
    global is_position_known
    is_position_known = True

def led_test():
    helper.reset_screen("LED testen")
    
    start = helper.ask_integer("Ab welcher LED möchtest du testen?")
    end = helper.ask_integer("Bis welche LED möchtest du testen?")
    
    led.highlight(start, end)
    
    input("\nFertig\n> ")
    
    led.clear()

try:
    while True:
        main_menu()   
except KeyboardInterrupt:
    led.clear()
    motor.exit()
    print("\n\nExited cleanly\n")
except Exception:
    print(traceback.format_exc())
    led.clear()
    motor.exit()
    print("\n\nExited cleanly\n")