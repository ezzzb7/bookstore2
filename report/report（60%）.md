## <center> 当代数据管理系统第二次大作业--书店</center>
### 小组成员
10235501452 肖璟仪
10235501435 张凯诚
### 1. 实验要求

**功能**
- 实现一个提供网上购书功能的网站后端。
- 网站支持书商在上面开商店，购买者可以通过网站购买。
- 买家和卖家都可以注册自己的账号。
- 一个卖家可以开一个或多个网上商店，
- 买家可以为自已的账户充值，在任意商店购买图书。
- 支持 下单->付款->发货->收货 流程。
**1.实现对应接口的功能：（60%）**
其中包括：
1)用户权限接口，如注册、登录、登出、注销
2)买家用户接口，如充值、下单、付款
3)卖家用户接口，如创建店铺、填加书籍信息及描述、增加库存
通过对应的功能测试，所有 test case 都 pass 
**2.为项目添加其它功能 ：（40%）**
1)实现后续的流程 ：发货 -> 收货
2)搜索图书 
- 用户可以通过关键字搜索，参数化的搜索方式；
- 如搜索范围包括，题目，标签，目录，内容；全站搜索或是当前店铺搜索。
- 如果显示结果较大，需要分页
- (使用全文索引优化查找)
3)订单状态，订单查询和取消定单
- 用户可以查自已的历史订单，用户也可以取消订单。
- 取消定单可由买家主动地取消定单，或者买家下单后，经过一段时间超时仍未付款，定单也会自动取消。 
### 2. 混合数据库架构设计
#### 2.0 从文档型数据库到混合架构的演进
##### 2.0.1 原始设计（纯MongoDB）
最初的bookstore项目使用纯MongoDB文档数据库，所有数据（用户、订单、库存、图书信息）都存储在MongoDB中。

**存在的问题：**
1. **缺乏事务支持**：MongoDB在4.0之前不支持多文档事务，订单创建、库存扣减、余额变动无法保证原子性
2. **关联查询困难**：用户-订单-商店-图书的多表关联需要多次查询或使用$lookup，性能较差
3. **数据一致性弱**：无外键约束，数据完整性依赖应用层保证
4. **BLOB数据影响性能**：大文本和图片混在业务数据中，导致查询变慢
##### 2.0.2 改进方案（MySQL+MongoDB混合架构）

**改动内容：**
- **MySQL存储核心业务数据**：users, stores, orders, store_inventory等表
- **MongoDB存储BLOB数据**：book_details集合存储图书详细介绍、图片等

**改动理由：**

1. **事务支持**：MySQL的ACID特性保证订单创建、支付、库存扣减的原子性
2. **性能提升**：外键索引、复合索引、全文索引大幅提升查询速度
3. **业务逻辑简化**：SQL的JOIN操作简化多表关联查询，代码更清晰
4. **数据分离**：BLOB数据分离到MongoDB，避免拖慢MySQL查询性能
5. **数据完整性**：外键约束保证引用完整性，级联删除自动维护数据一致性
#### 2.1 架构概述
本项目采用 **MySQL + MongoDB 混合数据库架构**：
- **MySQL（关系型数据库）**：存储核心业务数据（用户、商店、订单、库存）
- **MongoDB（NoSQL数据库）**：存储BLOB数据（图书详细介绍、作者介绍、图片等）

#### 2.2 业务逻辑图
| **1. 用户管理模块<br>(user.py)**                                                             | **2. 买家功能模块<br>(buyer.py)**                                                                                                                                                                      | **3. 卖家功能模块<br>(seller.py)<br>**                                                     | **4. 数据库连接模块<br>(db_conn.py)**                                                                                                                                                       |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **基础功能：**<br>- 注册(register)<br>- 登录(login)<br>- 登出(logout)<br>- 注销(unregister)<br><br> | **基础功能：**<br>- 账户充值(add_funds)<br>- 创建订单(new_order)<br>- 订单付款(payment)<br><br>                                                                                                                   | **基础功能：**<br>- 创建店铺(create_store)<br>- 添加图书(add_book)<br>- 库存管理(add_stock_level)<br> | **全文搜索索引：**(`create_search_indexes`)<br>- 覆盖字段：title/author/tags/content<br>- 核心能力：中文分词、模糊匹配<br>                                                                                     |
| **扩展功能：**<br>- 修改密码(change_password)                                                   | **扩展功能：**<br>- 订单查询(search_order)<br>- 取消订单(cancel_order)<br>- 自动取消(trigger_auto_cancel)<br>- 确认收货(receive_order)<br>- 图书搜索(search_books)<br>- 高级搜索(advanced_search)<br>- 热门图书(search_hot_books) | **扩展功能：**<br>- 订单发货(ship_order)<br>- 资金管理(add_funds)                                 | **数据库管理：**<br>- MySQL连接池管理<br>- MongoDB连接管理<br>- user_id_exist()<br>- store_id_exist()<br>- book_id_exist()<br><br>**索引优化：**<br>- MySQL全文索引(FULLTEXT)<br>- 订单状态和时间复合索引<br>- 外键索引自动创建 |
#### 2.3 ER图设计（全做完再搞）

**实体及属性：**
- **User（用户）**：user_id(PK), password, balance, token, terminal
- **Store（商店）**：store_id(PK), user_id(FK), store_name, description
- **Book（图书）**：book_id(PK), title, author, publisher, price, isbn, tags
- **Order（订单）**：order_id(PK), user_id(FK), store_id(FK), total_price, status
- **StoreInventory（库存）**：id(PK), store_id(FK), book_id(FK), stock_level, store_price
- **OrderDetail（订单详情）**：id(PK), order_id(FK), book_id(FK), quantity, price

**关系：**
- User 1:N Store（一个用户可开多个商店）
- Store 1:N StoreInventory（一个商店有多个库存记录）
- Book 1:N StoreInventory（一本书可在多个商店销售）
- User 1:N Order（一个用户可下多个订单）
- Order 1:N OrderDetail（一个订单包含多个商品）
- Book 1:N OrderDetail（一本书可在多个订单中）
#### 2.4 MySQL表结构设计（核心业务数据）

| 集合名称       | 具体结构                                                                                                                                                       | 主键       |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 用户集合       | user：<br> {<br>    "user_id": 用户ID<br>    "password": 用户密码<br>    "balance": 用户余额<br>    "token": 加密字符串（用户ID为密钥，HS256算法生成）<br>    "terminal": 登录终端信息<br> } | user_id  |
| 商店店家个人信息集合 | user_store：<br> {<br>    "store_id": 商店ID<br>    "user_id": 用户ID<br> }                                                                                     | store_id |
| 商店集合       | store：<br> {<br>    "store_id": 商店ID<br>    "book_stock_info": 书籍库存信息（数组）<br> }                                                                            | store_id |
| 书籍库存信息     | "book_stock_info"：<br> {<br>    "book_id": 书籍ID<br>    "stock_level": 库存信息<br> }                                                                           | book_id  |
| 书籍集合       | book：<br> {<br>    "book_id": 书籍ID<br>    "book_info": 书籍详细信息<br> }                                                                                        | book_id  |
| 订单集合       | new_order：<br> {<br>    "order_id": 订单ID<br>    "user_id": 用户ID<br>    "store_id": 商店ID<br>    "create_time": 创建时间<br> }                                   | order_id |
| 订单信息集合     | new_order_detail：<br> {<br>    "order_id": 订单ID<br>    "each_book_details": 一个订单内购买的书籍的信息（数组）<br> }                                                        | order_id |
| 订单内书籍详情    | each_book_in_order_details：<br> {<br>    "book_id": 书籍ID<br>    "count": 订购数量<br>    "price": 单价<br> }                                                     | book_id  |
#### 2.5 混合架构设计优势

**1. 数据库选型合理，各司其职**

- **MySQL负责核心业务数据**：用户、订单、库存等需要强一致性和事务支持的数据存储在MySQL中，利用其ACID特性保证数据准确性
- **MongoDB负责BLOB数据**：图书详细介绍、作者介绍、目录内容等大文本和图片数据存储在MongoDB中，避免MySQL性能下降

**2. 索引优化，保障高性能检索**

- **MySQL索引策略**：
  - 主键索引：所有表主键自动创建聚簇索引
  - 外键索引：自动在外键字段创建索引，提高JOIN性能
  - 全文索引：在books表的title、author、tags字段创建FULLTEXT索引，支持中文搜索
  - 复合索引：订单表创建(user_id, status, created_at)复合索引，优化订单查询

- **MongoDB索引**：在book_id字段创建索引，快速关联MySQL中的图书基础信息

**3. 事务支持，保证数据一致性**

MySQL的事务机制确保订单创建、支付、库存扣减等操作的原子性。例如：
- 下单时：同时创建订单记录、订单详情和扣减库存，三个操作要么全成功要么全失败
- 支付时：买家扣款和卖家收款在同一事务中完成，避免资金不一致

**4. 连接池管理，提升并发性能**

采用MySQL连接池技术（pool_size=10），复用数据库连接，减少连接创建销毁开销，支持高并发访问。

**5. 数据分离与解耦**

图书基础信息（标题、作者、价格等）存储在MySQL，详细描述、图片等BLOB数据存储在MongoDB。查询库存和订单时无需加载大字段，提升查询效率。
### 3. 基本功能实现（60%)
#### 3.0 数据库迁移实现
为了创建本地 MongoDB 数据库，并将`bookstore/fe/data/book_lx.db`中的内容以合适的形式存入本地数据库"，我们设计并实现了数据迁移脚本 `migrate_sqlite_to_mongo.py`。
##### 3.0.1 数据源连接
首先，我们要建立与SQLite源数据库和MongoDB目标数据库的连接：
```python
import sqlite3
from pymongo import MongoClient
sqlite_conn = sqlite3.connect('./fe/data/book_lx.db')
sqlite_cursor = sqlite_conn.cursor()
mongo_client = MongoClient('localhost', 27017) 
```
##### 3.0.2 MongoDB环境初始化
然后，我们实现了MongoDB环境的智能初始化。脚本检测是否已存在`bookstore`数据库，如存在则先删除以确保迁移环境的干净性，然后创建新的`bookstore`数据库和`book`集合，保证了迁移过程的幂等性：
```python
db_list = mongo_client.list_database_names()
if 'bookstore' in db_list:
    mongo_client.drop_database('bookstore')
    print("Existing 'bookstore' database found and deleted.")
db = mongo_client['bookstore']  
book_collection = db['book'] 
```
##### 3.0.3数据转换与迁移
这是核心的数据转换逻辑。严格按照README中提供的DDL定义了17个字段的映射关系，确保原有数据结构的完整保留。逐行读取SQLite数据并转换为MongoDB文档格式，完成从关系型数据库到文档型数据库的架构升级，最后妥善关闭连接。
```python
sqlite_cursor.execute("SELECT * FROM book")
rows = sqlite_cursor.fetchall()

columns = [
    "id", "title", "author", "publisher", "original_title", "translator", 
    "pub_year", "pages", "price", "currency_unit", "binding", "isbn", 
    "author_intro", "book_intro", "content", "tags", "picture"
]
for row in rows:
    book_document = {columns[i]: row[i] for i in range(len(columns))}
    book_collection.insert_one(book_document) 

sqlite_conn.close()
mongo_client.close()
print("successfully transfer")
```
##### 迁移效果
![](attachment/36705de4563660b3d0c2fedcd1c71d3b.jpg)
执行脚本后成功将SQLite中的40000+条图书记录完整迁移至MongoDB，实现了要求第1点的核心任务：创建本地MongoDB数据库并将原有数据以合适形式存入。后续系统的所有数据读写操作都将在本地MongoDB数据库中进行。

#### 3.1 用户权限接口
该部分实现在 `/be/model/user.py` 中，提供了 `User` 类：

```python
class User(db_conn.DBConn):
```
##### 3.1.1 注册 
```python
    def register(self, user_id: str, password: str) -> (int, str):
```
首先，注册函数会检查用户是否已存在。如果已存在，则返回错误信息。
```python
exist = self.db.user.find_one({"user_id": user_id})
if exist is not None:
    return error.error_exist_user_id(user_id)
```
如果用户不存在，则生成一个新的终端标识和 token，并将用户信息插入数据库。插入内容包括用户ID、密码、余额、token 和终端信息。
```python
terminal = "terminal_{}".format(str(time.time()))
token = jwt_encode(user_id, terminal)
self.db.user.insert_one({
    "user_id": user_id,
    "password": password,
    "balance": 0,
    "token": token,
    "terminal": terminal,
})
```

最后，返回注册成功的状态码和信息。

---
##### 3.1.2 注销功能 
```python
    def unregister(self, user_id: str, password: str) -> (int, str):
```
注销时，首先校验用户密码。如果密码错误，则返回错误。
```python
code, message = self.check_password(user_id, password)
if code != 200:
    return code, message
```
如果密码正确，则从数据库中删除该用户文档。
```python
exist = self.db.user.delete_one({"user_id": user_id})
if exist is None:
    return error.error_authorization_fail()
```
最后，返回注销成功的状态码和信息。

---
##### 3.1.3 登录功能 
```python
     def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
```
登录时，首先校验用户密码是否正确。如果密码错误，则直接返回错误。

```python
code, message = self.check_password(user_id, password)
if code != 200:
    return code, message, ""
```

如果密码正确，则生成新的 token，并更新数据库中的 token 和终端信息。

```python
token = jwt_encode(user_id, terminal)
exist = self.db.user.update_one({"user_id": user_id}, {"$set": {"token": token, "terminal": terminal}})
if exist.modified_count == 0:
    return error.error_authorization_fail() + ("",)
```

最后，返回登录成功的状态码、信息和新 token。

---
##### 3.1.4 登出功能 
```python
    def logout(self, user_id: str, token: str) -> bool:
```
登出时，首先校验当前 token 是否有效。如果无效，则返回错误。
```python
code, message = self.check_token(user_id, token)
if code != 200:
    return code, message
```
如果 token 有效，则生成一个新的 dummy token 和终端标识，更新数据库，使原 token 失效。
```python
terminal = "terminal_{}".format(str(time.time()))
dummy_token = jwt_encode(user_id, terminal)
exist = self.db.user.update_one({"user_id": user_id}, {"$set": {"token": dummy_token, "terminal": terminal}})
if exist.modified_count == 0:
    return error.error_authorization_fail() + ("",)
```
最后，返回登出成功的状态码和信息。

---
##### 3.1.5 修改密码功能 

修改密码时，首先校验旧密码。如果旧密码错误，则返回错误。
```python
code, message = self.check_password(user_id, old_password)
if code != 200:
    return code, message
```
如果旧密码正确，则生成新的 token 和终端标识，并将新密码、token 和终端信息更新到数据库。
```python
terminal = "terminal_{}".format(str(time.time()))
token = jwt_encode(user_id, terminal)
exist = self.db.user.update_one({"user_id": user_id},
                         {"$set": {"password": new_password, "token": token, "terminal": terminal}})
if exist.modified_count == 0:
    return error.error_authorization_fail()
```
最后，返回修改密码成功的状态码和信息。

#### 3.2 买家用户接口
该部分实现在 `/be/model/buyer.py` 中，提供了 `Buyer` 类：
```python
class Buyer(db_conn.DBConn):
```
##### 3.2.1 下单功能 
```python
    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
```
首先，函数会校验用户和商店是否存在。如果用户或商店不存在，则直接返回错误。
```python
user = self.db.user.find_one({"user_id": user_id})
if user is None:
    return error.error_non_exist_user_id(user_id) + (order_id,)

if self.store_id_exist(store_id) is False:
    return error.error_non_exist_store_id(store_id) + (order_id,)
```
接着，为订单生成唯一的 order_id并遍历每本书，校验库存是否充足。如果库存不足或书籍不存在，则返回错误。
```python
uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
each_book_in_order_details = []
for book_id, count in id_and_count:
    result = self.db.store.find_one(
        {"store_id": store_id,"book_stock_info.book_id": book_id},
        {"book_stock_info.$": 1}
    )
    if result is None:
        return error.error_non_exist_book_id(book_id) + (order_id,)
    stock_level = result["book_stock_info"][0]["stock_level"]
    price = self.get_book_price(book_id)
    if stock_level < count:
        return error.error_stock_level_low(book_id) + (order_id,)
```
如果库存充足，则更新库存，并将书籍详情添加到订单详情数组。
```python
condition = {
    "store_id": store_id, 
    "book_stock_info.book_id": book_id, 
    "book_stock_info.stock_level": {'$gte': count}
}
self.db.store.update_one(
    condition, 
    {"$inc": {"book_stock_info.$.stock_level": -1}}
)
each_book_in_order_details.append({
    "book_id": book_id,
    "count": count,
    "price": price
})
```
最后，将订单详情和订单主信息分别插入到new_order_detail 和 new_order集合，并返回订单号。
```python
new_order_detail = {
    "order_id": uid,
    "each_book_details": each_book_in_order_details
}
self.db.new_order_detail.insert_one(new_order_detail)
new_order = {
    "order_id": uid,
    "user_id": user_id,
    "store_id": store_id,
    "create_time": datetime.now(),
}
self.db.new_order.insert_one(new_order)
order_id = uid
```

---
##### 3.2.2 支付功能 
```python
    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
```
首先，函数会校验订单是否存在，并获取订单相关信息。如果订单不存在或用户不匹配，则返回错误。
```python
order_info = self.db.new_order.find_one({"order_id": order_id})
if order_info is None:
    return error.error_invalid_order_id(order_id)
order_id = order_info["order_id"]
buyer_id = order_info["user_id"]
store_id = order_info["store_id"]
if buyer_id != user_id:
    return error.error_authorization_fail()
```
然后，校验买家信息和密码，获取余额，并校验商店和卖家信息。
```python
usr_info = self.db.user.find_one({"user_id": buyer_id})
if usr_info is None:
    return error.error_non_exist_user_id(buyer_id)
balance = usr_info["balance"]
if password != usr_info["password"]:
    return error.error_authorization_fail()
store_info = self.db.user_store.find_one({"store_id": store_id})
if  store_info is None:
    return error.error_non_exist_store_id(store_id)
seller_id = store_info["user_id"]
if not self.user_id_exist(seller_id):
    return error.error_non_exist_user_id(seller_id)
```
接着，计算订单总价，判断余额是否足够。
```python
new_order_details_info = self.db.new_order_detail.find({"order_id": order_id})
total_price = 0
for order_detail in new_order_details_info:
    for book in order_detail["each_book_details"]:
        total_price += book["price"] * book["count"]
if balance < total_price:
    return error.error_not_sufficient_funds(order_id)
```
最后，扣除买家余额，增加卖家余额，并返回支付结果。
```python
result = self.db.user.update_many(
    {"user_id": buyer_id, "balance": {"$gte": total_price}},
    {"$inc": {"balance": -total_price}}
)
if result.modified_count == 0:
    return error.error_not_sufficient_funds(order_id)
result = self.db.user.update_many(
    {"user_id": seller_id},
    {"$inc": {"balance": total_price}}
)
if result.modified_count == 0:
    return error.error_not_sufficient_funds(order_id)
if result.matched_count == 0:
    return error.error_invalid_order_id(order_id)
```
---
### 3.2.3 充值功能
```python
    def add_funds(self, user_id, password, add_value) -> (int, str):
```
首先，校验用户信息和密码是否正确。
```python
user_info = self.db.user.find_one({"user_id": user_id})
if user_info is None:
    return error.error_authorization_fail()
if user_info.get("password") != password:
    return error.error_authorization_fail()
```
然后，更新用户余额，增加充值金额。
```python
exist = self.db.user.update_one({"user_id": user_id}, {"$inc": {"balance": add_value}})
if exist.matched_count == 0:
    return error.error_non_exist_user_id(user_id)
```
最后，返回充值结果。
#### 3.3 卖家用户接口
该部分实现在 `/be/model/seller.py` 中，提供了 `Seller` 类：
```python
class Seller(db_conn.DBConn):
```
##### 3.3.1 添加书籍功能 
```python
    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
```
首先，函数会校验用户、商店是否存在，以及该书籍是否已存在于商店库存。如果有任何一项不存在或书籍已存在，则返回对应错误。
```python
if not self.user_id_exist(user_id):
    return error.error_non_exist_user_id(user_id)
if not self.store_id_exist(store_id):
    return error.error_non_exist_store_id(store_id)
if self.book_id_exist(store_id, book_id):
    return error.error_exist_book_id(book_id)
```
通过后，向指定商店的 `book_stock_info` 数组中添加一本新书及其库存信息。
```python
self.db.store.update_one(
    {"store_id": store_id},
    {
        "$push": {
            "book_stock_info": {
                "book_id": book_id,
                "stock_level": stock_level
            }
        }
    }
)
```
最后，返回添加成功的状态码和信息。

---
##### 3.3.2 增加库存功能 
```python
    def add_stock_level(
        self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
```
首先，校验用户、商店和书籍是否存在。如果有任何一项不存在，则返回对应错误。
```python
if not self.user_id_exist(user_id):
    return error.error_non_exist_user_id(user_id)
if not self.store_id_exist(store_id):
    return error.error_non_exist_store_id(store_id)
if not self.book_id_exist(store_id, book_id):
    return error.error_non_exist_book_id(book_id)
```
校验通过后，更新指定商店和书籍的库存数量，使用 `$inc` 操作符实现库存的增加。
```python
exist = self.db.store.update_one(
    {"store_id": store_id, "book_stock_info.book_id": book_id},
    {"$inc": {"book_stock_info.$.stock_level": add_stock_level}}
)
assert exist.modified_count > 0
```
最后，返回增加库存成功的状态码和信息。

---
##### 3.3.3 创建商店功能 
```python
    def create_store(self, user_id: str, store_id: str) -> (int, str):
```
首先，校验用户是否存在，以及商店ID是否已被占用。如果用户不存在或商店已存在，则返回对应错误。
```python
if not self.user_id_exist(user_id):
    return error.error_non_exist_user_id(user_id)
if self.store_id_exist(store_id):
    return error.error_exist_store_id(store_id)
```
校验通过后，分别在user_store集合和store 集合中插入新商店信息。user_store记录商店与用户的关系，store 集合初始化商店库存为空数组。
```python
self.db.user_store.insert_one({
    "store_id": store_id,
    "user_id": user_id
})

self.db.store.insert_one({
    "store_id":store_id,
    "book_stock_info":[]
})
```
最后，返回创建商店成功的状态码和信息。
##### 3.4 运行测试结果
在终端输入bash script/test.sh：
运行结果如下：
![](attachment/ce79b24b1649046cac9723cd875f7ce5.png)
![](attachment/66360a7e7defa8113533350f976e8e33.png)

如图可见，测试用例全部通过，覆盖率96%。
#### 4. 附加功能实现（40%）


### 5. 项目亮点与优化

#### 5.1 测试代码Bug发现

**Bug: test_repeat_pay() 未真正测试重复支付**

**位置：** `fe/test/test_payment.py` 
**问题：** 测试名称为"重复支付测试"，但只执行了一次支付

**修复建议：**
```python
def test_repeat_pay(self):
    code = self.buyer.add_funds(self.total_price)
    assert code == 200
    code = self.buyer.payment(self.order_id)
    assert code == 200
    # 应添加：重复支付应失败
    code = self.buyer.payment(self.order_id)
    assert code != 200
```

#### 5.2 版本控制实践 
Git使用：

完整的提交历史记录
规范的commit message
分支管理：main（稳定版）、dev（开发版）
关键提交节点：


#### 5.3 高测试覆盖率 
