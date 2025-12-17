## 卖家发货

#### URL：
POST http://[address]/seller/ship_order

#### Request

Body:
```json
{
  "user_id": "seller_id",
  "order_id": "order_id"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
order_id | string | 订单ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 发货成功
5XX | 订单状态不允许发货
401 | 授权失败


## 买家收货

#### URL：
POST http://[address]/buyer/receive_order

#### Request

Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 收货成功
5XX | 订单状态不允许收货
401 | 授权失败


## 买家取消订单

#### URL：
POST http://[address]/buyer/cancel_order

#### Request

Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 取消成功
5XX | 订单状态不允许取消
401 | 授权失败


## 买家查询订单

#### URL：
POST http://[address]/buyer/query_order

#### Request

Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | Y

#### Response

Status Code:

码 | 描述
--- | ---
200 | 查询成功
5XX | 用户ID不存在

Body:
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

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N
orders | array | 订单列表 | N

#### 说明

1.order_id为空时，查询该用户的所有订单

2.订单状态：pending(待支付)、paid(已支付)、shipped(已发货)、delivered(已收货)、cancelled(已取消)


## 卖家查询商店订单

#### URL：
POST http://[address]/seller/query_store_orders

#### Request

Body:
```json
{
  "user_id": "seller_id",
  "store_id": "store_id"
}
```

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
401 | 授权失败

Body:
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

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N
orders | array | 订单列表 | N


## 搜索图书

#### URL：
POST http://[address]/search/books

#### Request

Body:
```json
{
  "keyword": "search_keyword",
  "store_id": "store_id",
  "page": 1,
  "page_size": 20,
  "search_scope": "all"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
keyword | string | 搜索关键字 | N
store_id | string | 商店ID | Y
page | int | 页码，从1开始 | Y
page_size | int | 每页大小，最大100 | Y
search_scope | string | 搜索范围 | Y

#### Response

Status Code:

码 | 描述
--- | ---
200 | 搜索成功
5XX | 搜索失败

Body:
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

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N
books | array | 图书列表 | N
total | int | 搜索结果总数 | N
page | int | 当前页码 | N
page_size | int | 每页大小 | N

#### 说明

1.store_id为空时，全站搜索；指定store_id时，只在该商店内搜索

2.search_scope可选值：all(全部)、title(标题)、author(作者)、tags(标签)、content(内容)，默认为all
