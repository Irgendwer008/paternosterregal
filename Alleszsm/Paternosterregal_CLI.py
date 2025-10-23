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
               ("Teile Auslagern", helper.nothing),
               ("Teile Einlagern", helper.nothing),
               ("Datenbank anzeigen", print_db),
               ("Datenbank durchsuchen (coming soon)", helper.nothing),
               ("Fach...", compartment_menu),
               ("Ware... (coming soon)", helper.nothing),
               ("=== Testfunktionen ===", helper.nothing),
               ("Datenbank zurücksetzen", reset_db),
               ("Motorposition zurücksetzen", reset_motor_position),
               ("Motor steuern manuell", manual_motorcontrol),
               ("Motor steuern manuell: Position", manual_motorcontrol_position))
    
    helper.menu("Menü", options)
        
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

def homing():
    motor.homing()
    is_position_known = True

def compartment_menu():
    options = [("...hinzufügen", add_compartment),
               ("...bearbeiten", edit_compartment_menu),
               ("...löschen", delete_compartment)]
        
    helper.menu("Fach...", options)

def add_compartment():
    helper.reset_screen("Fach hinzufügen")
    
    ## Regal ##
    
    print("Zu welchem Regal soll das Fach gehören?\n")
    
    for shelf in db.connection.execute("select id, label from shelves").fetchall():
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
    
    compartments = db.connection.execute("select shelf from compartments").fetchall()
    used_shelves = [x[0] for x in compartments]
    
    for shelf in db.connection.execute("select id, label from shelves").fetchall():
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
    
    for compartment in db.connection.execute("select id, position, length from compartments where shelf = ?", [shelf_id]).fetchall():
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
    
    for shelf in db.connection.execute("select id, label from shelves").fetchall():
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
        db.connection.execute("update compartments set shelf = ? where id = ?", (shelf_id, compartment_id))
        db.connection.commit()

def edit_compartment_startingposition(compartment_id: int):
    helper.reset_screen("Fach: Startposition bearbeiten")
    
    position = helper.ask_integer("An welche Startposition soll das Fach verschoben werden?")
    
    if helper.ask_confirm(bias=True):
        db.connection.execute("update compartments set position = ? where id = ?", (position, compartment_id))
        db.connection.commit()

def edit_compartment_length(compartment_id: int):
    helper.reset_screen("Fach: Länge bearbeiten")
    
    length = helper.ask_integer("Wie lang soll das Fach werden?")
    
    if helper.ask_confirm(bias=True):
        db.connection.execute("update compartments set length = ? where id = ?", (length, compartment_id))
        db.connection.commit()

def delete_compartment():
    helper.reset_screen("Fach löschen")
    
    ## Regal ##
    
    print("Zu welchem Regal gehört das Fach?\n")
    
    compartments = db.connection.execute("select shelf from compartments").fetchall()
    used_shelves = [x[0] for x in compartments]
    
    for shelf in db.connection.execute("select id, label from shelves").fetchall():
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
    
    for compartment in db.connection.execute("select id, position, length from compartments where shelf = ?", [shelf_id]).fetchall():
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
        db.cursor.execute("delete from compartments where id = ?", [compartment_id])
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
        
    label = helper.ask_integer("Wie lautet die Bezeichnung dieser Ware?")
    
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