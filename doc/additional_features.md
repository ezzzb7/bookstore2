# 后40%功能API文档

## 1. 订单流程相关接口

### 1.1 卖家发货

#### URL
POST http://[address]/seller/ship_order

#### Request

##### Headers:
key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "seller_id",
  "order_id": "order_id"
}
```

##### 属性说明:
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
order_id | string | 订单ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 发货成功
527 | 订单状态不是已支付，无法发货
5XX | 订单ID不存在
5XX | 商店ID不存在
401 | 授权失败（非该商店的卖家）

---

### 1.2 买家收货

#### URL
POST http://[address]/buyer/receive_order

#### Request

##### Headers:
key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

##### 属性说明:
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 收货成功
528 | 订单状态不是已发货，无法收货
5XX | 订单ID不存在
401 | 授权失败（非该订单的买家）

---

## 2. 订单查询与取消

### 2.1 买家查询订单

#### URL
POST http://[address]/buyer/query_order

#### Request

##### Headers:
key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

或查询所有订单（不指定order_id）:
```json
{
  "user_id": "buyer_id"
}
```

##### 属性说明:
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID（不指定则查询所有） | Y

#### Response

Status Code:

码 | 描述
--- | ---
200 | 查询成功
5XX | 用户ID不存在
5XX | 订单ID不存在

##### Body:
```json
{
  "message": "ok",
  "orders": [
    {
      "order_id": "order_id",
      "store_id": "store_id",
      "total_price": 100.00,
      "status": "pending",
      "created_at": "2025-12-15 10:00:00",
      "details": [
        {
          "book_id": "book_id",
          "quantity": 2,
          "price": 50.00
        }
      ]
    }
  ]
}
```

##### 订单状态说明:
- `pending`: 待支付
- `paid`: 已支付
- `shipped`: 已发货
- `delivered`: 已收货
- `cancelled`: 已取消

---

### 2.2 买家取消订单

#### URL
POST http://[address]/buyer/cancel_order

#### Request

##### Headers:
key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

##### 属性说明:
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 取消成功（如果已支付会自动退款）
529 | 订单状态不允许取消（已发货或已收货）
5XX | 订单ID不存在
401 | 授权失败（非该订单的买家）

---

### 2.3 卖家查询商店订单

#### URL
POST http://[address]/seller/query_store_orders

#### Request

##### Headers:
key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "seller_id",
  "store_id": "store_id"
}
```

##### 属性说明:
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
store_id | string | 商店ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 查询成功
5XX | 商店ID不存在
401 | 授权失败（非该商店的卖家）

##### Body:
```json
{
  "message": "ok",
  "orders": [
    {
      "order_id": "order_id",
      "buyer_id": "buyer_id",
      "total_price": 100.00,
      "status": "paid",
      "created_at": "2025-12-15 10:00:00",
      "details": [
        {
          "book_id": "book_id",
          "quantity": 2,
          "price": 50.00
        }
      ]
    }
  ]
}
```

---

## 3. 图书搜索

### 3.1 搜索图书

#### URL
POST http://[address]/search/books

#### Request

##### Body:
```json
{
  "keyword": "search_keyword",
  "store_id": "store_id",
  "page": 1,
  "page_size": 20,
  "search_scope": "all"
}
```

##### 属性说明:
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
keyword | string | 搜索关键字 | N
store_id | string | 商店ID（指定则只在该商店搜索，不指定则全站搜索） | Y
page | int | 页码，从1开始，默认1 | Y
page_size | int | 每页大小，默认20，最大100 | Y
search_scope | string | 搜索范围：all（全部）、title（标题）、author（作者）、tags（标签）、content（内容） | Y

#### Response

Status Code:

码 | 描述
--- | ---
200 | 搜索成功
530 | 搜索失败

##### Body:
```json
{
  "message": "ok",
  "books": [
    {
      "book_id": "book_id",
      "title": "book_title",
      "author": "author_name",
      "publisher": "publisher_name",
      "price": 50.00,
      "tags": "tag1,tag2,tag3",
      "stock_level": 10,
      "store_price": 50.00
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

##### 属性说明:
- 如果指定了`store_id`，返回的结果会包含`stock_level`和`store_price`字段
- `total`表示搜索结果的总数
- 支持分页，可以通过`page`和`page_size`控制

---

## 4. 自动取消超时订单

系统会自动检查并取消超过30分钟未支付的订单，恢复相应的库存。

该功能在后端自动运行，无需前端调用。

---

## 功能特性总结

### 完整的订单流程
1. **下单** (已有) → **支付** (已有) → **发货** (新增) → **收货** (新增)

### 订单管理
- **查询订单**: 买家可以查询自己的历史订单，卖家可以查询商店的订单
- **取消订单**: 买家可以主动取消待支付或已支付的订单
- **自动取消**: 系统自动取消超过30分钟未支付的订单
- **退款机制**: 取消已支付订单时自动退款

### 图书搜索
- **多范围搜索**: 支持按标题、作者、标签、内容搜索
- **全文索引**: 使用MySQL全文索引优化搜索性能
- **分页支持**: 搜索结果支持分页显示
- **商店内搜索**: 支持在特定商店内搜索
- **全站搜索**: 支持在所有图书中搜索

### 订单状态流转
```
pending (待支付) → paid (已支付) → shipped (已发货) → delivered (已收货)
                ↓                  ↓
           cancelled         cancelled
```
