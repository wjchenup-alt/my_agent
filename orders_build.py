import sqlite3

conn = sqlite3.connect("shop.db")
cur = conn.cursor()

# 建订单表。user_id 是外键，指向 users 表的 id
cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product TEXT    NOT NULL,
    amount  REAL    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

# 塞几笔订单。executemany 一次插多行
cur.executemany(
    "INSERT INTO orders (user_id, product, amount) VALUES (?, ?, ?)",
    [
        (1, "键盘", 299.0),
        (1, "鼠标", 99.0),
        (2, "显示器", 1299.0),
        (3, "耳机", 499.0),
    ])

conn.commit()
print("订单表建好了")
conn.close()
