from helper import Helper, color_shelf, color_compartment, color_part, color_part_compartment
import DB
import LED
import Motor

import os
from rich.console import Console
import traceback

#TODO: upon creation: check if things already exist

if os.getenv("USER") != "root":
    print("Dieses Programm muss mit superuser-Rechten ausgeführt werden!")
    exit(code=1)

filename = "paternosterregal.db"

db = DB.DB(filename=filename)
led = LED.LED(LED_COUNT=65, LED_PIN = 18)
motor = Motor.Motor(STEP_PIN=17, DIR_PIN=27, HALL_PIN=22, PAUSE_TIME=0.005)
helper = Helper(db)

is_position_known = False
            
def main_menu():
    
    options = (("Referenzfahrt", homing),
               (f"{color_part()} ein- & auslagern", add_remove_parts),
               ("Datenbank anzeigen", print_db),
               ("Datenbank durchsuchen", search_db),
               (f"{color_compartment()} hinzufügen", add_compartment),
               (f"{color_compartment()} bearbeiten / löschen", compartment_menu),
               (f"{color_part()} erstellen", add_part),
               (f"{color_part()} bearbeiten / löschen", part_menu),
               ("Sicherungen", backup_menu),
               ("Testfunktionen", test_functions))
    
    helper.menu("Menü", options)
   
def homing():
    helper.reset_screen("Referenzfahrt")
    
    motor.homing()
    global is_position_known
    is_position_known = True
    motor.move_to_position(0)
    
        
    input(f"\nReferenzfahrt erfolgreich abgeschlossen\n> ")

def add_remove_parts():
    helper.reset_screen("Teile ein- & auslagern")
    
    if not is_position_known:
        input("Die aktuelle Position ist unbestimmt. Du musst zunächst eine Referenzfahrt ausführen, bevor du diese Funktion nutzen kannst!\n> ")
        return
    
    search = input("Nach welchen Teilen suchst du?\n> ")
    
    print("\n")
    
    results = helper.search("parts", "label", search, like=True)
    
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
                                                       f"Regal {connection[1]}, {connection[2]}-{connection[2] + connection[3]}: {connection[4]} übrig"] # text
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
        
    input("> ")

def search_db():
    helper.reset_screen("Suche")

    search = input("Nach was möchtest du suchen?\n> ")
    
    parts = helper.search("parts", "label", search, True)
    
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
                                               shelves.label,
                                               compartments.id
                                           FROM parts_compartments
                                           JOIN compartments ON parts_compartments.compartment = compartments.id
                                           JOIN shelves ON compartments.shelf = shelves.id
                                           WHERE parts_compartments.part = ?
                                           ORDER BY
                                               shelves.id ASC,
                                               compartments.id ASC
                                           """, [part[0]]).fetchall()
            
            for result in results:
                print(f"  {result[0]}x in Fach #{result[4]} (Regal {result[3]}, {result[1]}-{result[2]})")
        
    input("\n> ")

def add_compartment():
    helper.reset_screen("Fach hinzufügen")
    
    ## Regal ##
    
    print(f"Zu welchem " + color_shelf() + " soll das " + color_compartment() + " gehören?\n")
    
    shelves = db.cursor.execute("SELECT id, label FROM shelves").fetchall()
    shelf_id = helper.run_selection([[shelf[0], color_shelf(shelf[1])] for shelf in shelves])
    
    ## Position ##
        
    position = helper.ask_integer("An welcher Position soll das Fach beginnen?")
    
    ## Länge ##
        
    length = helper.ask_integer("Wie lang soll das Fach sein?")
    
    ## Eintrag erstellen ##
    
    db.cursor.execute("insert into compartments (shelf, position, length) values (?, ?, ?)", [shelf_id, position, length])
    compartment_id = db.cursor.lastrowid
    db.connection.commit()
    
    input("\nInfo: " + helper.compartment(compartment_id) + " erfolgreich erstellt >")

def compartment_menu(compartment_id: int | None = None):
    if not compartment_id:
        helper.reset_screen(color_compartment("Fach") + " bearbeiten")
        
        ## Regal ##
        print(f"Zu welchem {color_shelf()} gehört das {color_compartment()}, das du bearbeiten möchtest?\n")
        results = db.cursor.execute("""SELECT shelves.id, shelves.label FROM shelves
                                   WHERE EXISTS (
                                       SELECT 1
                                       FROM compartments
                                       WHERE compartments.shelf = shelves.id
                                   )""", []).fetchall()
        shelf_id = helper.run_selection([[shelf[0], color_shelf(shelf[1])] for shelf in results])
        
        ## Fach ##
        results = db.cursor.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall()
        if len(results) == 1:
            compartment_id = results[0][0]
        else:
            print("\nWelches Fach möchtest du bearbeiten / löschen?\n")
            compartment_id = helper.run_selection([(result[0], helper.compartment(result[0], show_shelf=False)) for result in results])
        
    connections = db.cursor.execute("""SELECT 
                                       parts_compartments.stock,
                                       parts.label
                                       FROM parts_compartments
                                       JOIN parts ON parts_compartments.part = parts.id
                                       WHERE parts_compartments.compartment = ?""", [compartment_id]).fetchall()
    
    if len(connections) == 0:
        pretext = "\nDieses Fach ist zur Zeit leer."
    else:
        pretext = "\nDieses Fach beinhaltet:\n " + color_part("\n ".join([f"{connection[0]}x {connection[1]}" for connection in connections]))
    
    options = [("Regalzuordnung bearbeiten", edit_compartment_shelf),
               ("Startposition bearbeiten", edit_compartment_startingposition),
               ("Länge bearbeiten", edit_compartment_length),
               ("Fach löschen", delete_compartment)]
    
    result = helper.menu(f"{helper.compartment(compartment_id)} bearbeiten", options, pretext, compartment_id)
    if result == 1:
        return
    
    compartment_menu(compartment_id)

def edit_compartment_shelf(compartment_id: int):
    
    current_shelf = db.cursor.execute("SELECT shelves.id FROM compartments JOIN shelves ON compartments.shelf = shelves.id WHERE compartments.id = ?", [compartment_id]).fetchone()
    
    helper.reset_screen(f"Regalzuordnung bearbeiten (Aktuell: {helper.shelf(current_shelf[0])})")
    
    print("Welchem " + color_shelf() + " soll Fach zugeordnet werden?\n")
    
    shelves = helper.get_shelves()
    shelf_id = helper.run_selection([[shelf[0], color_shelf(shelf[1])] for shelf in shelves])
    
    if helper.ask_confirm(f"Sicher, dass du {helper.compartment(compartment_id)} zu {helper.shelf(shelf_id)} zuordnen möchtest?", bias=True):
        db.cursor.execute("UPDATE compartments SET shelf = ? WHERE id = ?", (shelf_id, compartment_id))
        db.connection.commit()

def edit_compartment_startingposition(compartment_id: int):
    helper.reset_screen("Startposition bearbeiten")
    
    position = helper.ask_integer(f"An welche Startposition soll das {color_compartment()} verschoben werden?")
    
    if helper.ask_confirm(f"Sicher, dass du {helper.compartment(compartment_id)} an Position {position} verschieben willst?", bias=True):
        db.cursor.execute("UPDATE compartments SET position = ? WHERE id = ?", (position, compartment_id))
        db.connection.commit()

def edit_compartment_length(compartment_id: int):
    helper.reset_screen("Länge bearbeiten")
    
    length = helper.ask_integer(f"Wie lang soll das {color_compartment()} werden?")
    
    if helper.ask_confirm(f"Sicher, dass {helper.compartment(compartment_id)} nun {length} lang sein soll?", bias=True):
        db.cursor.execute("UPDATE compartments SET length = ? WHERE id = ?", (length, compartment_id))
        db.connection.commit()

def delete_compartment(compartment_id: int):
    helper.reset_screen("Fach löschen")
    
    ## Eintrag löschen ##
    
    if helper.ask_confirm(f"Sicher, dass du {helper.compartment(compartment_id)} löschen willst?"):
        db.cursor.execute("delete FROM compartments WHERE id = ?", [compartment_id])
        db.connection.commit()
        return 1
    else:
        input("\nInfo: Vorgang abgebrochen. > ")

def add_part():
    helper.reset_screen("Ware hinzufügen")
    
    ## Bezeichnung ##
        
    label = input("Wie lautet die Bezeichnung der neuen " + color_part() + "?\n> ")
    
    ## Eintrag erstellen ##
    
    db.cursor.execute("insert into parts (label) values (?)", [label])
    part_id = db.cursor.lastrowid
    db.connection.commit()
    
    ## Ware einem Fach zuordnen
    
    if helper.ask_confirm(helper.part(label) + " erfolgreich erstellt. Möchtest du diese noch einem " + color_compartment() + " zuordnen?", bias=True):
        
        ## Regal ##
        
        print("\nZu welchem " + color_shelf() + " gehört das " + color_compartment() + "?\n")
        
        results = db.cursor.execute("SELECT shelves.id, shelves.label FROM shelves WHERE EXISTS (SELECT 1 FROM compartments WHERE compartments.shelf = shelves.id)").fetchall()
        shelf_id = helper.run_selection([[result[0], color_shelf(result[1])] for result in results])
        
        ## Fach ##
        
        print("\nWelchem " + color_compartment() + " möchtest du die Ware zuordnen?")
        
        results = db.cursor.execute("SELECT id FROM compartments WHERE shelf = ?", [shelf_id]).fetchall()
        compartment_id = helper.run_selection([[result[0], helper.compartment(result[0], show_shelf=False)] for result in results])
        
        ## Stückzahl
        
        stock = helper.ask_integer("Wie viele Teile werden eingelagert?")
    
        ## Verbindung Herstellen
    
        db.cursor.execute("INSERT INTO parts_compartments (part, compartment, stock) VALUES (?, ?, ?)", [part_id, compartment_id, stock])
        db.connection.commit()
        
        compartment = db.cursor.execute("SELECT shelves.label, compartments.position, compartments.length FROM compartments JOIN shelves ON compartments.shelf = shelves.id WHERE compartments.id = ?", [compartment_id]).fetchone()
        
        input(f"\n{helper.part(label)} erfolgreich {helper.compartment(compartment_id, show_shelf=False)} hinzugefügt\n> ")   

def part_menu(part_id: int | None = None, label: str | None = None):
    if not part_id:
        ## Ware erfragen
        while True:
            helper.reset_screen("Ware bearbeiten / löschen")

            search = input("Welche " + color_part() + " möchtest du bearbeiten?\n> ")
            if search != "":
                break
        
        results = helper.search("parts", "label", search, True)
        
        match len(results):
            case 0:
                input(f"\nZu \"{search}\" konnte leider keine Ware gefunden werden :/\n> ")
                return
            case 1:
                part_id = results[0][0]
            case _:
                print(f"\nZu \"{search}\" konnte folgende Waren gefunden werden:\n")
                part_id = helper.run_selection([(result[0], color_part(result[1])) for result in results])
    
    parts_compartments = db.cursor.execute("""SELECT
                                                  shelves.label,
                                                  compartments.id,
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
        pretext = "\nGelagert in:\n " + "\n ".join([f"{helper.shelf(pc[0])}, {helper.compartment(pc[1], False)}: {pc[2]}x" for pc in parts_compartments])
    else:
        pretext = None
        
    label = db.cursor.execute("SELECT label FROM parts WHERE id = ?", [part_id]).fetchone()[0]
    
    options = [
               ("Bezeichnung ändern", change_label),
               (color_part_compartment() + " hinzufügen", assign_part_to_compartment),
               ("Teil Löschen", delete_part)
              ] if len(parts_compartments) == 0 else [
               ("Bezeichnung ändern", change_label),
               ("Stückzahl bearbeiten", change_stock),
               (color_part_compartment() + " hinzufügen", assign_part_to_compartment),
               (color_part_compartment() + " verschieben", move_part_to_compartment),
               (color_part_compartment() + " löschen", remove_part_from_compartment),
               ("Teil Löschen", delete_part)]
        
        
    if helper.menu(helper.part(label), options, pretext, part_id, label) == 1:
        return
    
    part_menu(part_id, label)
    
def change_label(part_id: int, old_label: str):
    helper.reset_screen("Warenbezeichnung ändern")
    
    new_label = input("Wie soll die " + helper.part(old_label) + " in Zukunft heißen?\n> ")
    
    if helper.ask_confirm(f"Sicher, dass du {helper.part(old_label)} in {helper.part(new_label)} umbenennen willst?", bias=True):
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
            print("Bei welcher " + color_part_compartment() + " möchtest du die Stückzahl von " + {helper.part(label)} + " ändern?\n")
            parts_compartments_id = helper.run_selection([(result[0], f"{result[1]}x in Regal {result[5]}, Fach {result[2]} ({result[3]}-{result[3]+result[4]})") for result in results])
    
    new_stock = helper.ask_integer("Wie viele Teile sollen hier gelagert werden?")
    
    db.cursor.execute("UPDATE parts_compartments SET stock = ? WHERE id = ?", [new_stock, parts_compartments_id])
    db.connection.commit()

def assign_part_to_compartment(part_id: int, label: str):
    helper.reset_screen(helper.part(label) + " einem " + color_compartment() + " zuordnen")

    ## Regal ##
    compartments = db.cursor.execute("SELECT shelf FROM compartments").fetchall()
    used_shelf_ids = [str(compartment[0]) for compartment in compartments]
    string_used_shelf_ids = ",".join(used_shelf_ids)
    
    print("Zu welchem " + color_shelf() + " gehört das " + color_compartment() + ", dem du die " + color_part() + " zuordnen willst?\n")
    results = db.cursor.execute(f"SELECT id, label FROM shelves WHERE id IN ({string_used_shelf_ids})").fetchall()
    shelf_id = helper.run_selection([(result[0], color_shelf(result[1])) for result in results])
    
    ## Fach ##
    
    print("Welchem " + color_compartment() + " möchtest du die Ware zuordnen?")
    
    results = db.cursor.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall()
    compartment_id = helper.run_selection([(result[0], helper.compartment(result[0], False)) for result in results])
    
    ## Stückzahl
    
    stock = helper.ask_integer("Wie viele Teile werden eingelagert?")

    ## Verbindung Herstellen

    db.cursor.execute("INSERT INTO parts_compartments (part, compartment, stock) VALUES (?, ?, ?)", [part_id, compartment_id, stock])
    db.connection.commit()
        
    input(f"\n{stock}x {helper.part(label)} erfolgreich {helper.compartment(compartment_id)} hinzugefügt\n> ")

def move_part_to_compartment(part_id: int, label: str):
    helper.reset_screen(color_part_compartment() + " von " + helper.part(label) + " verschieben")
    
    ## Zuordnung ##
    parts_compartments = db.cursor.execute("""SELECT
                                                  parts_compartments.id,
                                                  compartments.id,
                                                  parts_compartments.stock
                                              FROM parts_compartments 
                                              JOIN compartments ON parts_compartments.compartment = compartments.id
                                              JOIN shelves ON compartments.shelf = shelves.id
                                              WHERE parts_compartments.part = ?
                                              ORDER BY
                                                  shelves.id ASC,
                                                  compartments.id ASC""", [part_id]).fetchall()
    
    match len(parts_compartments):
        case 0:
            helper.no_results()
            return
        case 1:
            print(f"Diese {color_part()} befindet sich zur Zeit in {helper.compartment(parts_compartments[0][1])}.\n")
            parts_compartments_id = parts_compartments[0][0]
        case _:
            print("Welche Zuordnung möchtest du verschieben?")
            parts_compartments_id = helper.run_selection([(pc[0], helper.compartment(pc[1]) + ": " + str(pc[2]) + "x") for pc in parts_compartments])
    
    ## Regal ##
    print("\nZu welchem " + color_shelf() + " gehört das " + color_compartment() + ", in das du die " + color_part() + " verschieben willst?\n")
    results = db.cursor.execute("""SELECT shelves.id, shelves.label
                                   FROM shelves
                                   WHERE EXISTS (
                                       SELECT 1 FROM compartments WHERE compartments.shelf = shelves.id
                                   )
                                   AND (
                                       SELECT COUNT(*) 
                                       FROM compartments
                                       WHERE compartments.shelf = shelves.id
                                   ) >
                                   (
                                       SELECT COUNT(DISTINCT compartments.id)
                                       FROM compartments
                                       JOIN parts_compartments ON parts_compartments.compartment = compartments.id
                                       WHERE compartments.shelf = shelves.id
                                       AND parts_compartments.part = ?
                                   )""", [part_id]).fetchall()

    shelf_id = helper.run_selection([(result[0], color_shelf(result[1])) for result in results])
    
    ## Fach ##
    print("\nIn welches " + color_compartment() + " möchtest du die " + color_part() + " verschieben?\n")
    results = db.cursor.execute("""SELECT compartments.id FROM compartments 
                                       WHERE compartments.shelf = ? 
                                       AND NOT EXISTS (
                                           SELECT 1 FROM parts_compartments
                                           WHERE parts_compartments.compartment = compartments.id
                                           AND parts_compartments.part = ?
                                       )""", [shelf_id, part_id]).fetchall()
    compartment_id = helper.run_selection([(result[0], helper.compartment(result[0], show_shelf=False)) for result in results])

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
    helper.reset_screen(color_part_compartment() + " von " + helper.part(part_id) + " löschen")
    
    ## Zuordnung ##
    parts_compartments = db.cursor.execute("""SELECT
                                                  parts_compartments.id,
                                                  compartments.id,
                                                  parts_compartments.stock
                                              FROM parts_compartments 
                                              JOIN compartments ON parts_compartments.compartment = compartments.id
                                              JOIN shelves ON compartments.shelf = shelves.id
                                              WHERE parts_compartments.part = ?
                                              ORDER BY
                                                  shelves.id ASC,
                                                  compartments.id ASC""", [part_id]).fetchall()
    
    match len(parts_compartments):
        case 0:
            helper.no_results()
            return
        case 1:
            print(f"Diese {color_part()} befindet sich zur Zeit in {helper.compartment(parts_compartments[0][1])}.\n")
            parts_compartments_id = parts_compartments[0][0]
        case _:
            print("Welche Zuordnung möchtest du löschen?")
            parts_compartments_id = helper.run_selection([(pc[0], helper.compartment(pc[1]) + ": " + str(pc[2]) + "x") for pc in parts_compartments])
    
    connection = db.cursor.execute("""SELECT
                                          parts_compartments.part,
                                          parts_compartments.compartment,
                                          parts_compartments.stock
                                      FROM parts_compartments
                                      WHERE parts_compartments.id = ?""", [parts_compartments_id]).fetchone()
        
    if helper.ask_confirm(f"Sicher, dass du {connection[2]}x " + helper.part(connection[0]) + " aus " + helper.compartment(connection[1]) + " löschen willst?"):
        db.cursor.execute("DELETE from parts_compartments WHERE id = ?", [parts_compartments_id])
        db.connection.commit()
        input(helper.part("\n" + connection[0]) + " in " + helper.compartment(connection[1]) + " erfolgreich gelöscht\n> ")
    else:
        input("\nInfo: Vorgang abgebrochen > ")

def delete_part(part_id: int, label: str):    
    if helper.ask_confirm(f"Sicher, dass du " + helper.part(label) + " und all ihre Lagerbestände löschen willst?"):
        db.cursor.execute("DELETE FROM parts WHERE id = ?", [part_id])
        db.connection.commit()
        return 1
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

def test_functions():
    
    options = [("Datenbank zurücksetzen", reset_db),
               ("Motorposition zurücksetzen", reset_motor_position),
               ("Motor steuern manuell", manual_motorcontrol),
               ("Motor steuern manuell: Position", manual_motorcontrol_position),
               ("Motorposition anzeigen", print_motor_position),
               ("LED-Test", led_test)]
    
    helper.menu("Testfunktionen", options)

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
    
    input(f"\n Motorposition = {motor.position}\n> ")

def reset_motor_position():
    motor.position = 0
    global is_position_known
    is_position_known = True

def led_test():
    helper.reset_screen("LED testen")
    
    start = helper.ask_integer("Ab welcher LED möchtest du testen?")
    end = helper.ask_integer("Bis welche LED möchtest du testen?")
    
    led.highlight(start, end)
    
    input("\nBeenden\n> ")
    
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