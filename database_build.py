import sqlite3

conn=sqlite3.connect("shop.db")
cur=conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT   NOT NULL,
    age INTEGER,
    city TEXT
)
""")
cur.execute("INSERT INTO users (name, age, city) VALUES (?, ?, ?)", ("小明", 18, "杭州"))
cur.execute("INSERT INTO users (name, age, city) VALUES (?, ?, ?)", ("小红", 22, "上海"))
cur.execute("INSERT INTO users (name, age, city) VALUES (?, ?, ?)", ("老王", 35, "北京"))
conn.commit()

print("建库建表完成")
conn.close()