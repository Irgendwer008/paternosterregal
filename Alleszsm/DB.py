import sqlite3
from xlsxwriter.utility import xl_col_to_name

class DB:
    def __init__(self, filename: str, number_of_shelves: int = 10):
        self.connection = sqlite3.connect(filename)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()
        self.number_of_shelves = number_of_shelves
        
        #self.reset()
    
    def to_string(self):
        string = ""
        
        for row in self.cursor.execute("select * from shelves").fetchall():
            string += f"{row[1]} || "
            
            for col in self.cursor.execute("select * from compartments where shelf = ?", (row[0],)).fetchall():
                string += f"{col[0]} ({col[2]}-{col[2]+col[3]})| "
            
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

        self.cursor.execute("""create table shelves (
                                    id integer primary key,
                                    label text,
                                    position integer)""")
        
        self.cursor.execute("""create table parts (
                                    id integer primary key,
                                    label text)""")
        
        self.cursor.execute("""create table compartments (
                                    id integer primary key,
                                    shelf integer, 
                                    position integer, 
                                    length integer, 
                                    foreign key (shelf) references shelves(id) on delete cascade)""")
        
        self.cursor.execute("""create table parts_compartments (
                                    id integer primary key, 
                                    compartment integer, 
                                    part integer, 
                                    stock integer, 
                                    foreign key (compartment) references compartments(id) on delete cascade,
                                    foreign key (part) references parts(id) on delete cascade)""")
        #self.cursor.execute("create table categories (id integer primary key, label)")


        shelves = [(xl_col_to_name(i), i * 800/3) for i in range(self.number_of_shelves)]
        compartments = [1, 1, 2, 3, 3, 3,]

        for i in range(compartments.__len__()):
            compartments[i] = (compartments[i], i * 6 + 3, 5)

        self.cursor.executemany("insert into shelves (label, position) values (?, ?)", shelves)
        self.cursor.executemany("insert into compartments (shelf, position, length) values (?, ?, ?)", compartments)

        self.connection.commit()