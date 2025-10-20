import sqlite3

class DB:
    def __init__(self, filename: str):
        self.connection = sqlite3.connect(filename)
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
    
    def to_string(self):
        string = ""
        
        for row in self.cursor.execute("select * from shelves").fetchall():
            string += f"{row[1]} || "
            
            for col in self.cursor.execute("select * from compartments where shelf = ?", (row[0],)).fetchall():
                string += f"{col[0]}: {col[2]} | "
            
            string += "\n"
        
        return string
    
    def add_shelf(self, label: str):
        self.cursor.execute("insert into shelves (label) values (?)", [label])
        self.connection.commit()
        
    def reset(self):                
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