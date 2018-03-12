import sqlite3

conn = sqlite3.connect('test.db')

c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS surveys (id varchar(3), data json)")
c.execute("CREATE TABLE IF NOT EXISTS results (id varchar(3), data json)")