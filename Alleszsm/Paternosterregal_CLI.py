import helper
import DB
import LED
import Motor

import os
import traceback

if os.getenv("USER") != "root":
    print("Dieses Programm muss mit superuser-Rechten ausgeführt werden!")
    exit()

db = DB.DB(filename="paternosterregal.db")
led = LED.LED(LED_COUNT=64)
motor = Motor.Motor(STEP_PIN=17, DIR_PIN=27, HALL_PIN=22, PAUSE_TIME=0.005)

is_position_known = False
            
def main_menu():
    
    options = (("Referenzfahrt", homing),
               ("Teile ein- & auslagern", add_remove_parts),
               ("Datenbank anzeigen", print_db),
               ("Datenbank durchsuchen (coming soon)", helper.nothing),
               ("Fach...", compartment_menu),
               ("Ware... (coming soon)", helper.nothing),
               ("Sicherung... (coming soon)", helper.nothing),
               ("=== Testfunktionen ===", helper.nothing),
               ("Datenbank zurücksetzen", reset_db),
               ("Motorposition zurücksetzen", reset_motor_position),
               ("Motor steuern manuell", manual_motorcontrol),
               ("Motor steuern manuell: Position", manual_motorcontrol_position))
    
    helper.menu("Menü", options)
   
def homing():
    motor.homing()
    is_position_known = True

def add_remove_parts():
    helper.reset_screen("Teile ein- & auslagern")
    
    search = input("Nach welchen Teilen suchst du?\n> ")
    
    results = helper.search("parts", "label", search, db, like=True)
    
    print("\n" + helper.format_options(results))
    
    while True:
        part_id = helper.ask_integer()
        if part_id in [result[0] for result in results]:
            break
    
    connections = db.cursor.execute("""
        SELECT 
            parts_compartments.id,
            compartments.shelf,
            compartments.position,
            compartments.length,
            parts_compartments.stock
        FROM parts_compartments
        JOIN compartments ON parts_compartments.compartment = compartments.id
        WHERE parts_compartments.part = ?""", (part_id,)).fetchall()
    
    
    
    if len(connections) > 1:
        print(helper.format_options([[connection[0], f"Fach {connection[1]}, {connection[2]}-{connection[2] + connection[3]}: {connection[4]} übrig"] for connection in connections]))
        while True:
            parts_compartments_id = helper.ask_integer()
            print(parts_compartments_id, connections)
            if parts_compartments_id in [connection[0] for connection in connections]:
                break
        
    else:
        parts_compartments_id = connections[0][0]
    
    change = helper.ask_integer("Wie viele Teile wurden dazugegeben (+) oder abgegeben (-)?")
    
    stock = db.cursor.execute("SELECT stock FROM parts_compartments WHERE id = ?", (parts_compartments_id,)).fetchone()[0]
    
    db.cursor.execute("UPDATE parts_compartments SET stock = ? WHERE id = ?", (stock + change, parts_compartments_id))
    db.connection.commit()

def print_db():
    
    helper.reset_screen("Übersicht")
    
    print(db.to_string())
        
    input("\n> ")






def reset_db():
    helper.reset_screen("Zurücksetzen")
    
    response = input("Sicher, dass du die Tabelle zurücksetzen willst? [y/N]\n> ")
    
    if response not in ["Y", "y"]:
        return

    db.reset()

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
    
def reset_motor_position():
    motor.position = 0

def compartment_menu():
    options = [("...hinzufügen", add_compartment),
               ("...bearbeiten", edit_compartment_menu),
               ("...löschen", delete_compartment)]
        
    helper.menu("Fach...", options)

def add_compartment():
    helper.reset_screen("Fach hinzufügen")
    
    ## Regal ##
    
    print("Zu welchem Regal soll das Fach gehören?\n")
    
    for shelf in db.connection.execute("SELECT id, label FROM shelves").fetchall():
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

def edit_compartment_menu():
    helper.reset_screen("Fach löschen")
    
    ## Regal ##
    
    print("Zu welchem Regal gehört das Fach?\n")
    
    compartments = db.connection.execute("SELECT shelf FROM compartments").fetchall()
    used_shelves = [x[0] for x in compartments]
    
    for shelf in db.connection.execute("SELECT id, label FROM shelves").fetchall():
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
    
    print("\n Welches Fach möchtest du bearbeiten?\n")
    
    for compartment in db.connection.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall():
        print(f" ({compartment[0]}) {compartment[1]}-{compartment[2]}")
        
    while True:
        try:
            compartment_id = int(input("\n > "))
            if compartment_id in range(compartment[0] + 1): # range() is zero-index-based
                break
        except ValueError:
            pass
        
        print("\nKeine Valide Eingabe, bitte versuche es erneut:")
    
    
    options = [("Regalzuordnung", edit_compartment_shelf),
               ("Startposition", edit_compartment_startingposition),
               ("Länge", edit_compartment_length)]
        
    helper.menu("Fach bearbeiten", options, compartment_id)

def edit_compartment_shelf(compartment_id: int):
    
    current_shelf = db.connection.execute("SELECT shelves.id, shelves.label FROM compartments JOIN shelves ON compartments.shelf = shelves.id WHERE compartments.id = ?", [compartment_id]).fetchone()
    
    helper.reset_screen(f"Fach: Regalzuordnung bearbeiten (Aktuell: {current_shelf[1]})")
    
    print("Welchem Regal soll Fach zugeordnet werden?\n")
    
    for shelf in db.connection.execute("SELECT id, label FROM shelves").fetchall():
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
        db.connection.execute("UPDATE compartments SET shelf = ? WHERE id = ?", (shelf_id, compartment_id))
        db.connection.commit()

def edit_compartment_startingposition(compartment_id: int):
    helper.reset_screen("Fach: Startposition bearbeiten")
    
    position = helper.ask_integer("An welche Startposition soll das Fach verschoben werden?")
    
    if helper.ask_confirm(bias=True):
        db.connection.execute("UPDATE compartments SET position = ? WHERE id = ?", (position, compartment_id))
        db.connection.commit()

def edit_compartment_length(compartment_id: int):
    helper.reset_screen("Fach: Länge bearbeiten")
    
    length = helper.ask_integer("Wie lang soll das Fach werden?")
    
    if helper.ask_confirm(bias=True):
        db.connection.execute("UPDATE compartments SET length = ? WHERE id = ?", (length, compartment_id))
        db.connection.commit()

def delete_compartment():
    helper.reset_screen("Fach löschen")
    
    ## Regal ##
    
    print("Zu welchem Regal gehört das Fach?\n")
    
    compartments = db.connection.execute("SELECT shelf FROM compartments").fetchall()
    used_shelves = [x[0] for x in compartments]
    
    for shelf in db.connection.execute("SELECT id, label FROM shelves").fetchall():
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
    
    print("Welches Fach möchtest du löschen?")
    
    for compartment in db.connection.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf_id]).fetchall():
        print(f" ({compartment[0]}) {compartment[1]}-{compartment[2]}")
        
    while True:
        try:
            compartment_id = int(input("\n > "))
            if compartment_id in range(compartment[0] + 1): # range() is zero-index-based
                break
        except ValueError:
            pass
        
        print("\nKeine Valide Eingabe, bitte versuche es erneut:")
    
    ## Eintrag löschen ##
    
    if helper.ask_confirm():
        db.cursor.execute("delete FROM compartments WHERE id = ?", [compartment_id])
        db.connection.commit()
    else:
        input("\nInfo: Vorgang abgebrochen. > ")

def part_menu():
    options = [("...erstellen", add_part),
               ("...einem Fach zuordnen (coming soon)", helper.nothing),
               ("...aus einem Fach entfernen (coming soon)", helper.nothing),
               ("...löschen", remove_part)]
        
    helper.menu("Ware...", options)
    
def add_part():
    helper.reset_screen("Ware hinzufügen")
    
    ## Bezeichnung ##
        
    label = helper.ask_integer("Wie lautet die Bezeichnung der Ware?")
    
    ## Eintrag erstellen ##
    
    db.cursor.execute("insert into parts (label) values (?)", [label])
    db.connection.commit()

def remove_part():
    helper.reset_screen("Ware löschen")

try:
    while True:
        main_menu()   
except KeyboardInterrupt:
    led.clear()
    motor.exit()
    print("Exited cleanly\n")
except Exception:
    print(traceback.format_exc())
    led.clear()
    motor.exit()
    print("Exited cleanly\n")