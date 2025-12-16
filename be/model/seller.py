import json
import logging
from be.model import error
from be.model import db_conn

class Seller(db_conn.DBConn):
    def __init__(self):
        super().__init__()

    def add_book(
        self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int,
    ):
        conn = None
        try:
            # 验证用户和商店存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            
            # 检查书籍是否已存在于商店中
            if self.book_id_exist(store_id, book_id):
                 return error.error_exist_book_id(book_id)

            book_info = json.loads(book_json_str)
            
            # 从 book_info 中获取必要信息
            title = book_info.get("title", "")
            author = book_info.get("author", "")
            publisher = book_info.get("publisher", "")
            original_title = book_info.get("original_title", "")
            translator = book_info.get("translator", "")
            pub_year = book_info.get("pub_year", "")
            pages = book_info.get("pages", 0)
            price = book_info.get("price", 0)
            currency_unit = book_info.get("currency_unit", "")
            binding = book_info.get("binding", "")
            isbn = book_info.get("isbn", "")
            author_intro = book_info.get("author_intro", "")
            book_intro = book_info.get("book_intro", "")
            content = book_info.get("content", "")
            tags = book_info.get("tags", [])
            pictures = book_info.get("pictures", [])

            conn = self.mysql_conn
            cursor = conn.cursor()
            
            # 开始事务
            conn.start_transaction()
            
            # 截断字段以符合数据库长度限制
            book_id = book_id[:255] if book_id else None
            title = title[:500] if title else None
            author = author[:255] if author else None
            publisher = publisher[:255] if publisher else None
            original_title = original_title[:255] if original_title else None
            translator = translator[:255] if translator else None
            pub_year = pub_year[:20] if pub_year else None
            currency_unit = currency_unit[:20] if currency_unit else None
            binding = binding[:50] if binding else None
            isbn = isbn[:20] if isbn else None
            
            # 添加或更新图书基础信息（MySQL）
            cursor.execute("""
                INSERT INTO books (book_id, title, author, publisher, original_title, translator, 
                                   pub_year, pages, price, currency_unit, binding, isbn)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    title = VALUES(title),
                    author = VALUES(author),
                    publisher = VALUES(publisher),
                    original_title = VALUES(original_title),
                    translator = VALUES(translator),
                    pub_year = VALUES(pub_year),
                    pages = VALUES(pages),
                    price = VALUES(price),
                    currency_unit = VALUES(currency_unit),
                    binding = VALUES(binding),
                    isbn = VALUES(isbn)
            """, (book_id, title, author, publisher, original_title, translator, 
                  pub_year, pages, price, currency_unit, binding, isbn))
            
            # 添加库存信息(MySQL)
            cursor.execute("""
                INSERT INTO store_inventory (store_id, book_id, stock_level, store_price)
                VALUES (%s, %s, %s, %s)
            """, (store_id, book_id, stock_level, price))
            
            # 添加BLOB数据到MongoDB（图书详情、介绍、图片等）
            mongo_db = self.mongo_db
            
            # 准备MongoDB文档
            book_detail = {
                "book_intro": book_intro,
                "content": content,
                "tags": tags,
                "pictures": pictures
            }
            
            # 更新或插入图书详细信息到MongoDB
            mongo_db.book_details.update_one(
                {"book_id": book_id},
                {"$set": book_detail},
                upsert=True
            )
            
            conn.commit()
                
        finally:
            if conn:
                conn.close()
                
        return 200, "ok"

    def add_stock_level(
        self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        conn = None
        try:
            # 验证用户、商店和书籍存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)
                
            conn = self.mysql_conn
            cursor = conn.cursor()
            
            # 增加库存
            cursor.execute(
                "UPDATE store_inventory SET stock_level = stock_level + %s "
                "WHERE store_id = %s AND book_id = %s",
                (add_stock_level, store_id, book_id)
            )
            
            # 检查是否真的更新了记录
            if cursor.rowcount == 0:
                return error.error_non_exist_book_id(book_id)
            
            conn.commit()
            
        finally:
            if conn:
                conn.close()
                
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> tuple[int, str]:
        conn = None
        try:
            # 验证用户存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
                
            # 检查商店是否已存在
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
                
            conn = self.mysql_conn
            cursor = conn.cursor()
            
            # 创建商店
            cursor.execute(
                "INSERT INTO stores (store_id, user_id) VALUES (%s, %s)",
                (store_id, user_id)
            )
            conn.commit()
            
        finally:
            if conn:
                conn.close()
                
        return 200, "ok"

    def ship_order(self, user_id: str, order_id: str) -> (int, str):
        """卖家发货"""
        conn = None
        try:
            conn = self.mysql_conn
            cursor = conn.cursor()

            # 检查订单是否存在
            cursor.execute(
                "SELECT store_id, status FROM orders WHERE order_id = %s",
                (order_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return error.error_invalid_order_id(order_id)
            
            store_id, status = result
            
            # 验证是否是该商店的卖家
            cursor.execute(
                "SELECT user_id FROM stores WHERE store_id = %s",
                (store_id,)
            )
            store_result = cursor.fetchone()
            if store_result is None:
                return error.error_non_exist_store_id(store_id)
            
            seller_id = store_result[0]
            if seller_id != user_id:
                return error.error_authorization_fail()
            
            # 检查订单状态是否为已支付
            if status != 'paid':
                return 527, "订单状态不是已支付，无法发货"
            
            # 更新订单状态为已发货
            cursor.execute(
                "UPDATE orders SET status = 'shipped' WHERE order_id = %s",
                (order_id,)
            )
            conn.commit()

        finally:
            if conn:
                conn.close()
        
        return 200, "ok"

    def query_store_orders(self, user_id: str, store_id: str) -> (int, str, list):
        """查询商店的订单"""
        conn = None
        try:
            conn = self.mysql_conn
            cursor = conn.cursor()

            # 验证是否是该商店的卖家
            cursor.execute(
                "SELECT user_id FROM stores WHERE store_id = %s",
                (store_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return error.error_non_exist_store_id(store_id) + ([],)
            
            seller_id = result[0]
            if seller_id != user_id:
                return error.error_authorization_fail() + ([],)
            
            # 查询商店的所有订单
            cursor.execute(
                "SELECT order_id, user_id, total_price, status, created_at "
                "FROM orders WHERE store_id = %s ORDER BY created_at DESC",
                (store_id,)
            )
            results = cursor.fetchall()
            
            orders = []
            for order_id, buyer_id, total_price, status, created_at in results:
                # 查询订单详情
                cursor.execute(
                    "SELECT book_id, quantity, price FROM order_details WHERE order_id = %s",
                    (order_id,)
                )
                details = cursor.fetchall()
                
                order_info = {
                    "order_id": order_id,
                    "buyer_id": buyer_id,
                    "total_price": float(total_price),
                    "status": status,
                    "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "details": [
                        {"book_id": book_id, "quantity": quantity, "price": float(price)}
                        for book_id, quantity, price in details
                    ]
                }
                orders.append(order_info)
            
            return 200, "ok", orders

        finally:
            if conn:
                conn.close()
        
        return 200, "ok", []
