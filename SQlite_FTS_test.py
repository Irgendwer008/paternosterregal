import sqlite3 

conn = sqlite3.connect(':memory:')
conn.execute("""create virtual table fts5test using fts5 (data);""") 
conn.execute("""insert into fts5test (data) 
                values ('this is a test of full-text search');""")
print(conn.execute("""select * from fts5test where data match 'full';""").fetchall())