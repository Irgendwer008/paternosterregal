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

def reset_screen(heading: str = None):
    print(chr(27) + "[H" + chr(27) + "[J", end="")
    
    print("######################################")
    print("##  Paternosterregal Datenbank CLI  ##")
    print("######################################")
    
    if heading is not None:
        # Print heading
        print("\n  " + heading)
        
        # Print heading underline
        print("\u2558", end="")
        for i in range(0, len(heading) + 2):
            print("\u2550", end="")
        print("\u255B")
    else:
        print("")
            
def menu():
    reset_screen("Menü")
    
    options = ["Datenbank anzeigen",
               "Regal hinzufügen",
               "Regal löschen",
               "Datenbank zurücksetzen",
               "Motor steuern manuell",
               "Motor steuern position",
               "Motorposition zurücksetzen",
               "Fach anfahren",
               "Fach suchen und anfahren",
               "Referenzfahrt",
               "Motorposition ausgeben"]
    
    num_options = len(options)
    
    for i in range(num_options):
        print(f" ({i+1}) " + options[i])
    
    response = input("\n> ")

    try:
        response = int(response)
    except ValueError:
        return
    
    if response not in range(num_options + 1):
        return
    
    match response:
        case 1: print_db()
        case 2: add_shelf()
        case 3: remove_shelf()
        case 4: reset_db()
        case 5: manual_motorcontrol()
        case 6: manual_motorcontrol_position()
        case 7: reset_motor_position()
        case 8: move_to_compartment_known()
        case 9: move_to_compartment_search()
        case 10: homing()
        case 11: print_position()
        
def print_db():
    
    reset_screen("Übersicht")
    
    print(db.to_string())
        
    input("\n> ")
        
def add_shelf():
    reset_screen("Regal hinzufügen")
    
    label = input("Wie lautet die Bezeichnung des Regals?\n> ")
    db.add_shelf(label)
    
def remove_shelf():
    reset_screen("Regal löschen")
    
    label = input("Wie lautet die Bezeichnung des Regals?\n> ")
    
    response = input(f"\nSicher, dass du das Regal {label} löschen willst [y/N]\n> ")
    
    if response not in ["Y", "y"]:
        return
    
    db.cursor.execute("delete from shelves where label = ?", [label])
    db.connection.commit()

def reset_db():
    reset_screen("Zurücksetzen")
    
    response = input("Sicher, dass du die Tabelle zurücksetzen willst? [y/N]\n> ")
    
    if response not in ["Y", "y"]:
        return

    db.reset()

def manual_motorcontrol():
    reset_screen("Motorsteuerung manuel")
    
    print("Gib an, wie viele Schritte der Motor fahren soll. KeyboardInterrupt zum beenden.")
    
    try:
        while True:
            motor.move_step(int(input("> ")))
    except KeyboardInterrupt:
        return
    
def manual_motorcontrol_position():
    reset_screen("Motorsteuerung manuel auf Position")
    
    print("Gib an, zu welcher Position der Motor fahren soll. KeyboardInterrupt zum beenden.")
    
    try:
        while True:
            motor.move_to_position(int(input("> ")))
    except KeyboardInterrupt:
        return
    
def reset_motor_position():
    motor.position = 0

def move_to_compartment_known():
    reset_screen("Fach anfahren")
    shelf_label_input = input("In welchem Regal ist das Fach?\n> ")
    
    db.cursor.execute("select rowid from shelves where label = ?", [shelf_label_input])
    shelf = db.cursor.fetchone()
        
    if shelf is None:
        input("Dieses Regal existiert nicht. Bitte starte den Vorgang erneut!\n> ")
        return
    
    print("Dieses Regal beinhaltet folgende Fächer:\n")
    
    found_compartments = db.cursor.execute("select * from compartments where shelf = ?", shelf).fetchall()
    for compartment in found_compartments:
        print(f"{compartment[0]}: {compartment[2]} ({compartment[3]}-{compartment[3]+compartment[4]})")
        
    compartment_ids = []
    for compartment in found_compartments:
        compartment_ids.append(compartment[0])
    
    try:
        compartment_id = int(input("\nWelches Fach möchtest du anfahren? (ID)\n> "))
        if compartment_id not in compartment_ids:
            raise IndexError
    except IndexError:
        input("Dies ist keine valide Nummer, bitte starte den Vorgang erneut!\n> ")
    
    compartment = db.cursor.execute("select * from compartments where rowid = ?", [compartment_id]).fetchone()
    shelf_position = db.cursor.execute("select position from shelves where rowid = ?", [compartment[1]]).fetchone()[0]
    
    led.highlight(compartment[3], compartment[3] + compartment[4])
    motor.move_to_position(shelf_position)

def move_to_compartment_search():
    reset_screen("Suche")
    
    search = input("Wonach möchtest du suchen?:\n>")
    
    print("Es wurden folgende Fächer zu deiner Suche gefunden:")
    
    found_compartments = db.cursor.execute("select * from compartments where cargo like ?", [f"%{search}%"]).fetchall()
    
    for compartment in found_compartments:
        shelf = db.cursor.execute("select rowid, label from shelves where rowid = ?", [compartment[1]]).fetchone()
        print(f"Fach {compartment[0]} in Regal {shelf[1]}: {compartment[2]} ({compartment[3]}-{compartment[3]+compartment[4]})")
        
    compartment_ids = []
    for compartment in found_compartments:
        compartment_ids.append(compartment[0])
    
    try:
        compartment_id = int(input("\nWelches Fach möchtest du anfahren? (ID)\n> "))
        if compartment_id not in compartment_ids:
            raise IndexError
    except IndexError:
        input("Dies ist keine valide Nummer, bitte starte den Vorgang erneut!\n> ")
    
    compartment = db.cursor.execute("select * from compartments where rowid = ?", [compartment_id]).fetchone()
    shelf_position = db.cursor.execute("select position from shelves where rowid = ?", [compartment[1]]).fetchone()[0]
    
    motor.move_to_position(int(shelf_position))
    led.highlight(compartment[3], compartment[3] + compartment[4])
    
    input("Bestätigen\n> ")
    led.clear()

def homing():
    motor.homing()

def print_position():
    reset_screen("Position")
    
    print(f"\n Motorposition = {motor.position}")
    
    input("\n> ")

try:
    while True:
        menu()   
except KeyboardInterrupt:
    led.clear()
    motor.exit()
    print("Exited cleanly\n")
except Exception:
    print(traceback.format_exc())
    led.clear()
    motor.exit()
    print("Exited cleanly\n")