import sqlite3

conn=sqlite3.connect("shop.db")
cur=conn.cursor()

cur.execute("SELECT * FROM users")
rows=cur.fetchall()
print("total",len(rows),"rows")
for row in rows:
    print(row)

print("-"*30)

cur.execute("SELECT name,city from users where age>20")
for name,city in cur.fetchall():
    print(name,'live at',city)

cur.execute("select * from users order by age desc")
print('oldest',cur.fetchone())
print(cur.fetchone())

conn.close()