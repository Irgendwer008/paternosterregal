import sqlite3

class DB():
    def init(self):
        self.connection = sqlite3.connect('paternosterregal.db')
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()
        
        self.cursor.execute("DROP TABLE IF EXISTS shelves")
        self.cursor.execute("DROP TABLE IF EXISTS compartments")
        
        self.cursor.execute("create table shelves (id integer primary key, label text)")
        self.cursor.execute("create table compartments (id integer primary key, shelf integer, cargo text, position integer, length integer, foreign key (shelf) references shelves(id) on delete cascade)")

        shelves = [("A",), ("B",), ("C",)]
        compartments = [(1, "M6 Screws"), (1, "M5 Screws"), (2, "Screwdriver"), (3, "M5 Nut"), (3, "M6 Nut"), (3, "M7 Nut")]


        for i in range(compartments.__len__()):
            compartments[i] = (compartments[i][0], compartments[i][1], i * 3, 3)

        self.cursor.executemany("insert into shelves (label) values (?)", shelves)
        self.cursor.executemany("insert into compartments (shelf, cargo, position, length) values (?, ?, ?, ?)", compartments)

        self.connection.commit()


    def reset_screen(self, heading: str = None):
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
            
    def menu(self):
        self.reset_screen("Menü")
        
        options = ["Datenbank anzeigen", "Regal hinzufügen", "Regal löschen", "Fach hinzufügen", "Fach löschen", "Datenbank zurücksetzen"]
        
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
            case 1: self.print_db()
            case 2: self.add_shelf()
            case 3: self.remove_shelf()
            case 4: self.add_compartment()
            case 5: self.remove_compartment()
            case 6: self.reset_db()
        
    def print_db(self):
        self.reset_screen("Übersicht")
        
        for row in self.cursor.execute("select * from shelves").fetchall():
            print(f"{row[1]} || ", end="")
            
            for col in self.cursor.execute("select * from compartments where shelf = ?", (row[0],)).fetchall():
                print(f"{col[0]}: {col[2]} ({col[3]}-{col[3]+col[4]})| ", end="")
            
            print("")
        
        input("\n> ")
        
    def add_shelf(self):
        self.reset_screen("Regal hinzufügen")
        
        label = input("Wie lautet die Bezeichnung des Regals?\n> ")
        self.cursor.execute("insert into shelves (label) values (?)", [label])
        self.connection.commit()
    
    def remove_shelf(self):
        self.reset_screen("Regal löschen")
        
        label = input("Wie lautet die Bezeichnung des Regals?\n> ")
        
        response = input(f"\nSicher, dass du das Regal {label} löschen willst [y/N]\n> ")
        
        if response not in ["Y", "y"]:
            return
        
        self.cursor.execute("delete from shelves where label = ?", [label])
        self.connection.commit()
        
    def add_compartment(self):
        self.reset_screen("Fach hinzufügen")
        
        shelf_label = input("Zu welchem Regal soll das Fach gehören?\n> ")
        
        self.cursor.execute("select rowid from shelves where label = ?", [shelf_label])
        shelf_id = self.cursor.fetchone()
        
        if shelf_id is None:
            input("Dieses Regal existiert nicht. Bitte starte den Vorgang erneut!\n> ")
            return
        
        cargo_text = input ("\nWas wird in diesem Fach gelagert?\n> ")
        try:
            position = int(input("\nAn welcher position befindet sich das Fach?\n> "))
            length = int(input("\nWie groß ist das Fach?\n> "))
        except:
            print("Dies ist keine valide Nummer, bitte starte den Vorgang erneut!\n> ")
        
        response = input(f"\nHinzufügen eines Fachs für {cargo_text} im Regal \"{shelf_label}\" an Position {position}-{position+length} Bestätigen [Y/n]\n> ")
        
        if response in ["N", "n"]:
            return
        
        self.cursor.execute("insert into compartments (shelf, cargo, position, length) values (?, ?, ?, ?)", [shelf_id[0], cargo_text, position, length])
        self.connection.commit()
    
    def remove_compartment(self):
        self.reset_screen("Fach löschen")
        
        shelf_label = input("In welchem Regal befindet sich das Fach?\n> ")
        
        self.cursor.execute("select rowid from shelves where label = ?", [shelf_label])
        shelf_id = self.cursor.fetchone()
        
        if shelf_id is None:
            input("Dieses Regal existiert nicht. Bitte starte den Vorgang erneut!\n> ")
            return
        
        print("Dieses Regal beinhaltet folgende Fächer:\n")
        
        found_compartments = self.cursor.execute("select * from compartments where shelf = ?", shelf_id).fetchall()
        for compartment in found_compartments:
            print(f"{compartment[0]}: {compartment[2]} ({compartment[3]}-{compartment[4]})")
            
        compartment_ids = []
        for compartment in found_compartments:
            compartment_ids.append(compartment[0])
        
        try:
            shelf_id = int(input("\nWelches Fach möchtest du löschen? (ID)\n> "))
            if shelf_id not in compartment_ids:
                raise IndexError
        except:
            print("Dies ist keine valide Nummer, bitte starte den Vorgang erneut!\n> ")
        
        response = input(f"\nSicher, dass du das Fach für {compartment[2]} im Regal \"{shelf_label}\" an Position {compartment[3]}-{compartment[3]+compartment[4]} löschen willst [y/N]\n> ")
        
        if response not in ["Y", "y"]:
            return
        
        self.cursor.execute("delete from compartments where id = ?", [shelf_id])
        self.connection.commit()
    
    def reset_db(self):
        self.reset_screen("Zurücksetzen")
        
        response = input("Sicher, dass du die Tabelle zurücksetzen willst? [y/N]\n> ")
        
        if response not in ["Y", "y"]:
            return
                
        self.cursor.execute("DROP TABLE IF EXISTS shelves")
        self.cursor.execute("DROP TABLE IF EXISTS compartments")

        self.cursor.execute("create table shelves (id integer primary key, label text)")
        self.cursor.execute("create table compartments (id integer primary key, shelf integer, cargo text, position integer, length integer, foreign key (shelf) references shelves(id) on delete cascade)")

        shelves = [("A",), ("B",), ("C",)]
        compartments = [(1, "M6 Screws"), (1, "M5 Screws"), (2, "Screwdriver"), (3, "M5 Nut"), (3, "M6 Nut"), (3, "M7 Nut")]


        for i in range(compartments.__len__()):
            compartments[i] = (compartments[i][0], compartments[i][1], i * 3, 3)

        self.cursor.executemany("insert into shelves (label) values (?)", shelves)
        self.cursor.executemany("insert into compartments (shelf, cargo, position, length) values (?, ?, ?, ?)", compartments)

        self.connection.commit()
        
    def run(self):
        self.init()
        
        try:
            # Start CLI
            while(True):
                self.menu()
        except KeyboardInterrupt:
            self.connection.close()

    # print specific##
    #
    #self.cursor.execute("select * from gta where city=:c", {"c": "Liberty City"})
    #gta_search = self.cursor.fetchall()
    #
    #print(gta_search)
    
db = DB()
db.run()
    