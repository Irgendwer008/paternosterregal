import DB
import LED
import Motor

import os

if os.getenv("USER") != "root":
    print("Dieses Programm muss mit superuser-Rechten ausgeführt werden!")
    
    exit()

db = DB.DB()
led = LED.LED(LED_COUNT=64)
motor = Motor.Motor(STEP_PIN=17, DIR_PIN=27)

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
               "Motorposition zurücksetzen"]
    
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
            motor.step(int(input("> ")))
    except KeyboardInterrupt:
        return
    
def manual_motorcontrol_position():
    reset_screen("Motorsteuerung manuel auf Position")
    
    print("Gib an, zu welcher Position der Motor fahren soll. KeyboardInterrupt zum beenden.")
    
    try:
        while True:
            motor.move(int(input("> ")))
    except KeyboardInterrupt:
        return
    
def reset_motor_position():
    motor.position = 0

try:
    exit()
    
    print(os.getenv("USER"))
    
    while True:
        menu()   
except:
    led.clear()
    motor.exit()
    print("\n")