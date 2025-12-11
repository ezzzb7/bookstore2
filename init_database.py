#!/usr/bin/env python3
"""
数据库初始化脚本
创建MySQL表结构和MongoDB索引
"""

import mysql.connector
from pymongo import MongoClient
import logging
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_mysql_database():
    """初始化MySQL数据库和表结构"""
    try:
        # 连接MySQL服务器（不指定数据库）
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'password'),
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS bookstore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE bookstore")
        
        logging.info("创建用户表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(100) PRIMARY KEY,
                password VARCHAR(255) NOT NULL,
                balance DECIMAL(10,2) DEFAULT 0.00,
                token VARCHAR(500),
                terminal VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_token (token(255)),
                INDEX idx_terminal (terminal)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        logging.info("创建商店表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                store_id VARCHAR(100) PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                store_name VARCHAR(200),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        logging.info("创建图书基本信息表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id VARCHAR(100) PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                author VARCHAR(300),
                publisher VARCHAR(200),
                original_title VARCHAR(500),
                translator VARCHAR(300),
                pub_year VARCHAR(20),
                pages INT,
                price DECIMAL(10,2),
                currency_unit VARCHAR(10),
                binding VARCHAR(50),
                isbn VARCHAR(50),
                tags VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_title (title(255)),
                INDEX idx_author (author(255)),
                INDEX idx_publisher (publisher),
                INDEX idx_isbn (isbn),
                INDEX idx_price (price),
                FULLTEXT idx_search (title, author, tags)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        logging.info("创建商店库存表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS store_inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                store_id VARCHAR(100) NOT NULL,
                book_id VARCHAR(100) NOT NULL,
                stock_level INT NOT NULL DEFAULT 0,
                store_price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                UNIQUE KEY unique_store_book (store_id, book_id),
                INDEX idx_store_id (store_id),
                INDEX idx_book_id (book_id),
                INDEX idx_stock_level (stock_level)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        logging.info("创建订单表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                store_id VARCHAR(100) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                status ENUM('pending', 'paid', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (store_id) REFERENCES stores(store_id),
                INDEX idx_user_id (user_id),
                INDEX idx_store_id (store_id),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        logging.info("创建订单详情表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_details (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id VARCHAR(255) NOT NULL,
                book_id VARCHAR(100) NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES books(book_id),
                INDEX idx_order_id (order_id),
                INDEX idx_book_id (book_id)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        conn.commit()
        logging.info("MySQL数据库初始化完成")
        
    except mysql.connector.Error as e:
        logging.error(f"MySQL初始化失败: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_mongodb():
    """初始化MongoDB数据库和集合"""
    try:
        client = MongoClient('localhost', 27017)
        db = client['bookstore_blobs']
        
        # 创建book_details集合的索引
        book_details = db['book_details']
        book_details.create_index([("book_id", 1)], unique=True)
        book_details.create_index([
            ("author_intro", "text"),
            ("book_intro", "text"),
            ("content", "text")
        ])
        
        # 创建system_logs集合的索引
        system_logs = db['system_logs']
        system_logs.create_index([("timestamp", -1)])
        system_logs.create_index([("level", 1)])
        system_logs.create_index([("user_id", 1)])
        
        client.close()
        logging.info("MongoDB初始化完成")
        
    except Exception as e:
        logging.error(f"MongoDB初始化失败: {e}")
        raise

def main():
    """主函数"""
    try:
        logging.info("开始数据库初始化...")
        
        # 初始化MySQL
        init_mysql_database()
        
        # 初始化MongoDB
        init_mongodb()
        
        logging.info("数据库初始化完成！")
        
    except Exception as e:
        logging.error(f"数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()