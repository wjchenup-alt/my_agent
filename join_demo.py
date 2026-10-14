import sqlite3

conn = sqlite3.connect("shop.db")
conn.row_factory = sqlite3.Row

cur = conn.execute("""
    SELECT users.name, orders.product, orders.amount
    FROM orders JOIN users ON orders.user_id = users.id
    ORDER BY orders.amount DESC
""")

for r in cur:
    print(r["name"], "买了", r["product"], r["amount"], "元")

conn.close()
