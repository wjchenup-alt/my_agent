import sqlite3


class UserDB:
    """对 users 表的所有操作，全部关在这个类里"""

    def __init__(self, db_path="shop.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row   # 让查询结果能按列名取值
        self.cur = self.conn.cursor()

    def add_user(self, name, age, city):
        """加一个用户，返回他的新 id"""
        self.cur.execute(
            "INSERT INTO users (name, age, city) VALUES (?, ?, ?)",
            (name, age, city))
        self.conn.commit()
        return self.cur.lastrowid

    def get_user(self, user_id):
        """按 id 查一个人，查不到返回 None"""
        self.cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = self.cur.fetchone()
        return dict(row) if row else None

    def list_users(self, min_age=0):
        """列出年龄 >= min_age 的所有人，按年龄排序"""
        self.cur.execute(
            "SELECT * FROM users WHERE age >= ? ORDER BY age", (min_age,))
        return [dict(r) for r in self.cur.fetchall()]

    def delete_user(self, user_id):
        """删一个人，返回实际删掉了几条"""
        self.cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()
        return self.cur.rowcount

    def close(self):
        self.conn.close()


# ================= 下面是"用户端"，它完全不懂 SQL =================
if __name__ == "__main__":
    db = UserDB()

    new_id = db.add_user("小李", 28, "深圳")
    print("新加的用户 id =", new_id)

    print("小李的信息：", db.get_user(new_id))

    print("所有 18 岁以上的人：")
    for u in db.list_users(18):
        print("  ", u["id"], u["name"], u["age"], u["city"])

    n = db.delete_user(new_id)
    print("删掉了", n, "条")

    db.close()
