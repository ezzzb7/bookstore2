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
