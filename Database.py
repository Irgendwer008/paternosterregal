import sqlite3

connection = sqlite3.connect('paternosterregal.db')
connection.execute("PRAGMA foreign_keys = ON")
cursor = connection.cursor()

# Clear old tables if re-running
cursor.execute("DROP TABLE IF EXISTS shelves")
cursor.execute("DROP TABLE IF EXISTS compartements")

cursor.execute("create table shelves (id integer primary key, label text)")
cursor.execute("create table compartements (id integer primary key, shelf integer, cargo text, position integer, length integer, foreign key (shelf) references shelves(id) on delete cascade)")

shelves = [("A",), ("B",), ("C",)]
compartements = [(1, "M6 Screws"), (1, "M5 Screws"), (2, "Screwdriver"), (3, "M5 Nut"), (3, "M6 Nut"), (3, "M7 Nut")]


for i in range(compartements.__len__()):
    compartements[i] = (compartements[i][0], compartements[i][1], i * 3, 3)
    
print(compartements)

cursor.executemany("insert into shelves (label) values (?)", shelves)
cursor.executemany("insert into compartements (shelf, cargo, position, length) values (?, ?, ?, ?)", compartements)

#print

for row in cursor.execute("select id, * from shelves").fetchall():
    print(row[1], ": ", end="")
    
    for col in cursor.execute("select * from compartements where shelf = ?", (row[0],)).fetchall():
        print(col[0], ": ", col[2], " | ", end="")
    
    print("")


# print specific##
#
#cursor.execute("select * from gta where city=:c", {"c": "Liberty City"})
#gta_search = cursor.fetchall()
#
#print(gta_search)

connection.close()