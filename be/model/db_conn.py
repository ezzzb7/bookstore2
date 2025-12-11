import mysql.connector
from mysql.connector import pooling
from pymongo import MongoClient
import logging
import os

class DBConn:
    # MySQL连接池 (关系型数据库 - 核心业务数据)
    _mysql_pool = None
    # MongoDB连接 (NoSQL数据库 - BLOB数据)
    _mongo_client = None
    _mongo_db = None
    
    def __init__(self):
        self._init_mysql_pool()
        self._init_mongodb()
    
    def _init_mysql_pool(self):
        """初始化MySQL连接池"""
        if DBConn._mysql_pool is None:
            try:
                config = {
                    'host': os.getenv('MYSQL_HOST', 'localhost'),
                    'port': int(os.getenv('MYSQL_PORT', 3306)),
                    'database': os.getenv('MYSQL_DATABASE', 'bookstore'),
                    'user': os.getenv('MYSQL_USER', 'root'),
                    'password': os.getenv('MYSQL_PASSWORD', 'password'),
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci',
                    'autocommit': True,
                    'pool_name': 'bookstore_pool',
                    'pool_size': 10,
                    'pool_reset_session': True
                }
                DBConn._mysql_pool = pooling.MySQLConnectionPool(**config)
                logging.info("MySQL连接池初始化成功")
            except Exception as e:
                logging.error(f"MySQL连接池初始化失败: {e}")
                raise
    
    def _init_mongodb(self):
        """初始化MongoDB连接"""
        if DBConn._mongo_client is None:
            try:
                mongo_host = os.getenv('MONGO_HOST', 'localhost')
                mongo_port = int(os.getenv('MONGO_PORT', 27017))
                DBConn._mongo_client = MongoClient(mongo_host, mongo_port)
                DBConn._mongo_db = DBConn._mongo_client['bookstore_blobs']
                logging.info("MongoDB连接初始化成功")
            except Exception as e:
                logging.error(f"MongoDB连接初始化失败: {e}")
                raise
    
    @property
    def mysql_conn(self):
        """获取MySQL连接"""
        try:
            return DBConn._mysql_pool.get_connection()
        except Exception as e:
            logging.error(f"获取MySQL连接失败: {e}")
            raise
    
    @property 
    def mongo_db(self):
        """获取MongoDB数据库"""
        return DBConn._mongo_db
    
    def user_id_exist(self, user_id):
        """检查用户是否存在"""
        conn = None
        try:
            conn = self.mysql_conn
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result is not None
        finally:
            if conn:
                conn.close()
    
    def store_id_exist(self, store_id):
        """检查商店是否存在"""
        conn = None
        try:
            conn = self.mysql_conn
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM stores WHERE store_id = %s", (store_id,))
            result = cursor.fetchone()
            return result is not None
        finally:
            if conn:
                conn.close()
    
    def book_id_exist(self, store_id, book_id):
        """检查图书在指定商店是否存在"""
        conn = None
        try:
            conn = self.mysql_conn
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM store_inventory WHERE store_id = %s AND book_id = %s",
                (store_id, book_id)
            )
            result = cursor.fetchone()
            return result is not None
        finally:
            if conn:
                conn.close()
