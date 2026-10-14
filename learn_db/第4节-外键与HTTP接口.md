# 第 4 节：外键 + HTTP 接口（15 分钟打通）

## 【本节目标】

- 让两张表"关联"起来，真正体会"关系型数据库"里的**关系**两个字。
- 把你的 `UserDB` 包成 HTTP 接口，**用浏览器就能查到数据**。

关于 MySQL：密码还没解决，今天跑不了。所以本节末尾我只放了对照说明（2 分钟看一眼），等你密码搞定了喊我。

---

# Part A：外键——让两张表牵上手（4 分钟）

## 【核心概念讲解】

### 比喻：两张 Excel 表怎么对上

现在你有了一张 `users` 表。再加一张 `orders`（订单）表，记录谁买了什么。

笨办法是把用户信息抄进订单表：

| 订单号 | 客户姓名 | 年龄 | 城市 | 商品 |
|---|---|---|---|---|
| 1 | 小明 | 18 | 杭州 | 键盘 |

问题来了：小明搬家了，你得把**所有**提到小明的行都改一遍。改漏一行，数据就自相矛盾了。

聪明办法是**只记编号**：

| 订单号 | 用户编号 | 商品 |
|---|---|---|
| 1 | **1** | 键盘 |

这个"用户编号"就是**外键（foreign key）**。它本身只是个数字，但要拿它去 `users` 表里一查，就知道是"小明，18 岁，杭州"。

**所以"关系型数据库"的"关系"是什么？** 就是**表与表之间的这种引用**。数据不重复存，只存一个指路的编号。

### 怎么把编号"还原"成人名：JOIN

```sql
SELECT users.name, orders.product
FROM orders JOIN users ON orders.user_id = users.id
```

读成大白话：**把 orders 和 users 两张表拼起来，拼接规则是"orders.user_id 等于 users.id"。**

`JOIN` 就是那个"查编号、换成人名"的动作。

---

## 【动手应用】

在 `my_agent` 下新建 `orders_build.py`，自己敲：

```python
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
```

跑：`python orders_build.py`

然后新建 `join_demo.py`，看"关系"是怎么被还原的：

```python
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
```

预期输出：

```
小红 买了 显示器 1299.0 元
老王 买了 耳机 499.0 元
小明 买了 键盘 299.0 元
小明 买了 鼠标 99.0 元
```

> 注意：这里我没有写 `users.name` 而是直接写 `name`，SQLite 会自己找。但表多了以后有两个同名列（比如两张表都有 `id`），就必须写全 `orders.id` / `users.id`，否则会报 `ambiguous column name`。

---

# Part B：包成 HTTP 接口（9 分钟）

## 【核心概念讲解】

### 比喻：从"传菜员"升级成"外卖窗口"

第 3 节的 `client.py` 已经是个传菜员了——别人 `from client import UserDB` 就能取数据。但这有个限制：**必须和你用同一种语言（Python），必须在同一台机器上**。

现在把窗口改成"外卖窗口"（HTTP 接口）：

- 你可以用**浏览器**点单
- 你可以用**手机 App** 点单
- 你同事可以用 **Java** 写的程序点单

因为 HTTP 是通用语言，谁都听得懂。**这就是"用户端调用"最真实的样子**——你的数据库从"一个 Python 类"变成了"一个网络服务"。

### FastAPI 是什么

一个 Python 库，帮你把普通函数变成网址。你写：

```python
@app.get("/users")           # 意思是：访问 /users 这个网址，就跑下面这个函数
def list_users():
    return db.list_users()   # 你的函数返回什么，网址就吐出什么（自动转成 JSON）
```

就这么多。不用管网络协议、不用管 JSON 怎么拼。

---

## 【动手应用】

### 第 1 步：先改 `client.py` 一行（重要！）

打开你第 3 节写的 [client.py](client.py)，把 `__init__` 里那行改成：

```python
self.conn = sqlite3.connect(db_path, check_same_thread=False)
```

**为什么必须改**：FastAPI 会把你的函数丢到"线程池"里跑（为了同时处理多个请求），而 SQLite 的连接默认**不允许跨线程使用**。不改这一行，浏览器一访问就是 `500 Internal Server Error`。我实测踩过这个坑。

> 正经项目里通常每个请求开一条连接、或者用"连接池"，这里只有一个练手用的连接，加这个参数就够了。

### 第 2 步：新建 `api.py`

```python
from fastapi import FastAPI, HTTPException
from client import UserDB

app = FastAPI(title="我的小数据库 API")

# 整个程序共用一条数据库连接
db = UserDB()


@app.get("/users")
def list_users(min_age: int = 0):
    """GET /users        列出所有人
       GET /users?min_age=22   只看 22 岁以上的"""
    return db.list_users(min_age)


@app.get("/users/{user_id}")
def get_user(user_id: int):
    """GET /users/1      按 id 查一个人"""
    u = db.get_user(user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="没有这个人")
    return u
```

三个要点：
- `min_age: int = 0` —— FastAPI 会**自动**从网址里把 `?min_age=22` 抠出来转成整数，你不用自己解析。
- `{user_id}` —— 网址里的可变部分，同理自动转成 `int`。
- `HTTPException` —— 查不到时返回 404，而不是返回个空对象，这是接口该有的体面。

### 第 3 步：启动

在 `d:\python\my_agent` 目录下（**必须在这个目录**，否则 `import client` 会失败）：

```bash
python -m uvicorn api:app --reload
```

看到 `Uvicorn running on http://127.0.0.1:8000` 就成了。**这个窗口别关，它就是你数据库的"外卖窗口"。**

### 第 4 步：用浏览器点单

再开一个终端或直接开浏览器，依次访问：

| 网址 | 你会看到 |
|---|---|
| http://127.0.0.1:8000/users | 所有人，JSON 格式 |
| http://127.0.0.1:8000/users?min_age=22 | 只有小红和老王 |
| http://127.0.0.1:8000/users/1 | 小明的信息 |
| http://127.0.0.1:8000/users/99 | `{"detail":"没有这个人"}` |
| **http://127.0.0.1:8000/docs** | **FastAPI 自动生成的接口文档，能直接在页面上点着试** |

最后那个 `/docs` 是我特意让你看的——你一行文档都没写，FastAPI 根据你的函数签名自动生成了一整套可交互的接口文档。这就是"接口"作为"菜单"的完整形态。

**到这一步，你已经完成了本节的全部目标**：浏览器（真正的用户端）→ HTTP → FastAPI → UserDB → SQLite，一条完整的链路。

---

# Part C：MySQL 对照（2 分钟，今天跑不了）

等你密码搞定后，改动量如下：

**`client.py` 只改 `__init__`：**

```python
import pymysql

def __init__(self):
    self.conn = pymysql.connect(
        host="127.0.0.1", port=3306, user="root", password="你的密码",
        database="shop", charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor)   # 让结果直接是字典
    self.cur = self.conn.cursor()
```

**SQL 语句里：**
- 占位符 `?` → `%s`
- `AUTOINCREMENT` → `AUTO_INCREMENT`
- 建表前要先有库：`CREATE DATABASE shop;`

**`api.py` 一行都不用改。** 浏览器那边的网址也一模一样。

这就是分层的价值兑现的时刻——最外面（用户端）完全无感。

---

## 【自测与思考】

1. `orders` 表里为什么存的是 `user_id`（数字），而不是直接存"小明"这个名字？
   > 提示：如果小明改名叫"明哥"，两种方案各要改几处？

2. 浏览器访问 `http://127.0.0.1:8000/users/1` 时，请求背后依次经过了哪几个环节？
   > 提示：浏览器 → ??? → ??? → ??? → shop.db

3. 现在我想加一个"下订单"的接口（`POST /orders`）。需要动 `users` 表吗？需要动 `api.py` 吗？需要动 `client.py` 吗？

---

## 【易错点提醒】

1. **忘了 `check_same_thread=False`** —— 浏览器里看到的是一句干巴巴的 `Internal Server Error`，看不出原因。真正的原因要到**运行 uvicorn 的那个终端**里看报错日志。**以后遇到 500，永远先去看服务端日志。**
2. **`uvicorn` 必须在 `my_agent` 目录下启动**，否则 `from client import UserDB` 会报 `ModuleNotFoundError`。
3. **端口 8000 被占用** —— 报 `address already in use`。换个端口：`python -m uvicorn api:app --port 8001`，网址也跟着换成 8001。
4. **外键只是"约束"，JOIN 才是"取数据"** —— 别把这两个混为一谈。而且 SQLite 的外键约束**默认是关闭的**，想让它真的拦住非法数据，得先执行 `PRAGMA foreign_keys = ON`。今天建表时写 `FOREIGN KEY` 更多是"声明意图"，MySQL 里则会真的强制执行。

---

## 【下一步预告】

本节留了两个自然的下一步（不急，想学再说）：

1. **补上写数据的接口**：`POST /orders`，让浏览器也能往数据库里塞订单。会顺带讲到"请求体（request body）"和 Pydantic 校验。
2. **正经搞定 MySQL**：你把密码找出来，我带你走一遍完整迁移，顺便体会一下 `%s` 和 `?` 的差异、以及 `DictCursor` 和 `row_factory` 的对应关系。
