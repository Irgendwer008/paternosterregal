#from colorama import Fore, Back, Style
import shutil
import sqlite3
from xlsxwriter.utility import xl_col_to_name

class DB:
    def __init__(self, filename: str, number_of_shelves: int = 10):
        self.connection = sqlite3.connect(filename)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()
        self.number_of_shelves = number_of_shelves
    
    def to_string(self):
        #TODO: add unallocated parts overview
        
        terminal_width = shutil.get_terminal_size((80, 20))[0]
        
        string = ""
        
        for shelf in self.cursor.execute("SELECT * FROM shelves").fetchall():
            string += f"╡Regal {shelf[1]}:╞" + "═" * (terminal_width - len(f"╡Regal {shelf[1]}:╞"))
            
            compartments = self.cursor.execute("SELECT id, position, length FROM compartments WHERE shelf = ?", [shelf[0]]).fetchall()
            if len(compartments) == 0:
                string += "\n  <LEER>"
            for compartment in compartments:
                compartment_string = f"\n  Fach {compartment[0]} ({compartment[1]}-{compartment[1]+compartment[2]}): "
                current_widht = len(compartment_string)
            
                parts_compartments_result = self.cursor.execute("""SELECT parts_compartments.stock, parts.label
                                                                   FROM parts_compartments 
                                                                   JOIN parts ON parts_compartments.part = parts.id
                                                                   WHERE parts_compartments.compartment = ?""", [compartment[0]]).fetchall()

                if len(parts_compartments_result) == 0:
                    compartment_string += "<LEER>  "
                else:
                    for parts_compartments in parts_compartments_result:
                        string_to_add = f"{parts_compartments[0]}x \"{parts_compartments[1]}\", "
                        if current_widht + len(string_to_add) > terminal_width:
                            current_widht = 4 + len(string_to_add) # padding
                            compartment_string += f"\n  └ " + string_to_add
                        else:
                            current_widht += len(string_to_add)
                            compartment_string += string_to_add
                
                string = string + compartment_string[:-2]
            
            string += "\n"
        
        return string
        
    def reset(self):              
        self.cursor.execute("PRAGMA foreign_keys = OFF;")  
        self.cursor.execute("DROP TABLE IF EXISTS shelves")
        self.cursor.execute("DROP TABLE IF EXISTS parts")
        self.cursor.execute("DROP TABLE IF EXISTS compartments")
        self.cursor.execute("DROP TABLE IF EXISTS parts_compartments")
        #self.cursor.execute("DROP TABLE IF EXISTS categories")
        self.cursor.execute("PRAGMA foreign_keys = ON;")

        self.cursor.execute("""CREATE TABLE shelves (
                                    id integer primary key,
                                    label text,
                                    position integer)""")
        
        self.cursor.execute("""CREATE TABLE parts (
                                    id integer primary key,
                                    label text)""")
        
        self.cursor.execute("""CREATE TABLE compartments (
                                    id integer primary key,
                                    shelf integer, 
                                    position integer, 
                                    length integer, 
                                    FOREIGN KEY (shelf) REFERENCES shelves(id) ON DELETE CASCADE)""")
        
        self.cursor.execute("""CREATE TABLE parts_compartments (
                                    id integer primary key, 
                                    part integer, 
                                    compartment integer, 
                                    stock integer, 
                                    FOREIGN KEY (compartment) REFERENCES compartments(id) ON DELETE CASCADE,
                                    FOREIGN KEY (part) REFERENCES parts(id) ON DELETE CASCADE)""")
        #self.cursor.execute("CREATE TABLE categories (id integer primary key, label)")


        shelves = [(xl_col_to_name(i), int(i * 800/3)) for i in range(self.number_of_shelves)]
        parts = [["Schrauben M4x10"], ["Schrauben M5x10"], ["Schrauben M6x10"],
                 ["Schrauben M4x16"], ["Schrauben M5x16"], ["Schrauben M6x16"],
                 ["Schrauben M4x20"], ["Schrauben M5x20"], ["Schrauben M6x20"],
                 ["Muttern M4x10"], ["Muttern M5x10"], ["Muttern M6x10"]]
        compartments = [1, 1, 2, 3, 3, 3]
        parts_compartments = [[1, 1, 5], [2, 1, 10], [3, 1, 2],
                              [4, 2, 1], [5, 2, 50], [6, 1, 253],
                              [7, 4, 23], [8, 5, 220], [9, 4, 54],
                              [10, 5, 83], [11, 5, 2], [12, 5, 62],
                              [10, 6, 12], [11, 6, 5], [12, 6, 3]]

        for i in range(compartments.__len__()):
            compartments[i] = (compartments[i], i * 6 + 3, 5)

        self.cursor.executemany("INSERT INTO shelves (label, position) VALUES (?, ?)", shelves)
        self.cursor.executemany("INSERT INTO compartments (shelf, position, length) VALUES (?, ?, ?)", compartments)
        self.cursor.executemany("INSERT INTO parts (label) VALUES (?)", parts)
        self.cursor.executemany("INSERT INTO parts_compartments (part, compartment, stock) VALUES (?, ?, ?)", parts_compartments)

        self.connection.commit()