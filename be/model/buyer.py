from datetime import datetime, timedelta
import logging
import uuid
import mysql.connector
from be.model import db_conn
from be.model import error

class Buyer(db_conn.DBConn):
    def __init__(self):
        super().__init__()

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        conn = None
        try:
            # 验证用户和商店存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            # 生成订单ID
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            order_id = uid

            conn = self.mysql_conn
            cursor = conn.cursor()

            total_price = 0
            order_books = []
            
            # 检查库存和计算价格
            for book_id, count in id_and_count:
                # 检查商店中是否有此书
                cursor.execute(
                    "SELECT stock_level, store_price FROM store_inventory "
                    "WHERE store_id = %s AND book_id = %s",
                    (store_id, book_id)
                )
                result = cursor.fetchone()
                if result is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                
                stock_level, price = result
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                
                total_price += price * count
                order_books.append((book_id, count, price))

            # 开始事务
            conn.start_transaction()
            
            # 创建订单
            cursor.execute(
                "INSERT INTO orders (order_id, user_id, store_id, total_price, status) "
                "VALUES (%s, %s, %s, %s, %s)",
                (order_id, user_id, store_id, total_price, 'pending')
            )

            # 创建订单详情和减少库存
            for book_id, count, price in order_books:
                cursor.execute(
                    "INSERT INTO order_details (order_id, book_id, quantity, price) "
                    "VALUES (%s, %s, %s, %s)",
                    (order_id, book_id, count, price)
                )
                
                cursor.execute(
                    "UPDATE store_inventory SET stock_level = stock_level - %s "
                    "WHERE store_id = %s AND book_id = %s",
                    (count, store_id, book_id)
                )

            conn.commit()

        finally:
            if conn:
                conn.close()

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        conn = None
        try:
            conn = self.mysql_conn
            cursor = conn.cursor()

            # 检查订单是否存在
            cursor.execute(
                "SELECT user_id, store_id, total_price, status FROM orders WHERE order_id = %s",
                (order_id,)
            )
            order_result = cursor.fetchone()
            buyer_id, store_id, total_price, status = order_result
            
            if status != 'pending':
                return error.error_invalid_order_id(order_id)
            
            # 验证买家身份和密码
            cursor.execute(
                "SELECT password, balance FROM users WHERE user_id = %s",
                (buyer_id,)
            )
            user_result = cursor.fetchone()
            stored_password, balance = user_result
            if password != stored_password:
                return error.error_authorization_fail()
            
            # 检查余额是否足够
            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 查找卖家ID
            cursor.execute(
                "SELECT user_id FROM stores WHERE store_id = %s",
                (store_id,)
            )
            store_result = cursor.fetchone()
            seller_id = store_result[0]

            # 开始事务进行支付
            conn.start_transaction()
            
            # 从买家账户扣款
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE user_id = %s",
                (total_price, buyer_id)
            )
            
            # 向卖家账户加款
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (total_price, seller_id)
            )
            
            # 更新订单状态为已支付
            cursor.execute(
                "UPDATE orders SET status = 'paid' WHERE order_id = %s",
                (order_id,)
            )
            
            conn.commit()

        finally:
            if conn:
                conn.close()
                
        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        conn = None
        try:
            conn = self.mysql_conn
            cursor = conn.cursor()

            # 验证用户身份和密码
            cursor.execute(
                "SELECT password FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return error.error_non_exist_user_id(user_id)
            
            stored_password = result[0]
            if stored_password != password:
                return error.error_authorization_fail()
            
            # 增加余额
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (add_value, user_id)
            )
            conn.commit()

        finally:
            if conn:
                conn.close()
        
        return 200, "ok"