#!/usr/bin/env python3
"""
数据迁移脚本：从SQLite迁移到MySQL+MongoDB混合架构
从 fe/data/book_lx.db 读取图书数据
将核心业务数据迁移到MySQL关系型数据库
将BLOB数据（图片、长文本）迁移到MongoDB中
"""

import mysql.connector
from pymongo import MongoClient
import sqlite3
import logging
import sys
import os
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLite数据库路径
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'fe', 'data', 'book_lx.db')

def migrate_books_data():
    """迁移图书数据：基础信息到MySQL，BLOB数据到MongoDB"""
    
    # 连接源SQLite数据库
    if not os.path.exists(SQLITE_DB_PATH):
        logging.error(f"SQLite数据库文件不存在: {SQLITE_DB_PATH}")
        raise FileNotFoundError(f"找不到数据库文件: {SQLITE_DB_PATH}")
    
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接目标MySQL
    mysql_conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='bookstore',
        user='root',
        password='123456',
        charset='utf8mb4'
    )
    mysql_cursor = mysql_conn.cursor()
    
    # 连接目标MongoDB (blob数据库)
    mongo_client = MongoClient('localhost', 27017)
    mongo_db = mongo_client['bookstore_blobs']
    
    try:
        # 获取所有图书数据
        sqlite_cursor.execute("SELECT COUNT(*) FROM book")
        total_books = sqlite_cursor.fetchone()[0]
        
        logging.info(f"开始迁移 {total_books} 条图书数据...")
        
        # 查询所有图书
        sqlite_cursor.execute("SELECT * FROM book")
        
        migrated_count = 0
        for row in sqlite_cursor:
            try:
                book_id = row['id']
                if not book_id:
                    continue
                
                # 准备MySQL数据(基础信息)
                # 注意：对字符串字段进行长度限制，防止超出数据库字段定义
                mysql_data = {
                    'book_id': (book_id or '')[:255],
                    'title': (row['title'] or '')[:500],
                    'author': (row['author'] or '')[:255],
                    'publisher': (row['publisher'] or '')[:255],
                    'original_title': (row['original_title'] or '')[:500],
                    'translator': (row['translator'] or '')[:255],
                    'pub_year': str(row['pub_year'] or '')[:100],
                    'pages': int(row['pages']) if row['pages'] else None,
                    'price': float(row['price']) if row['price'] else None,
                    'currency_unit': (row['currency_unit'] or '')[:50],
                    'binding': (row['binding'] or '')[:50],
                    'isbn': (row['isbn'] or '')[:50],
                    'tags': (row['tags'] or '')[:65535]  # TEXT类型，最大65535字节
                }
                
                # 插入到MySQL
                insert_sql = """
                    INSERT INTO books (book_id, title, author, publisher, original_title, 
                                     translator, pub_year, pages, price, currency_unit, 
                                     binding, isbn, tags)
                    VALUES (%(book_id)s, %(title)s, %(author)s, %(publisher)s, %(original_title)s,
                            %(translator)s, %(pub_year)s, %(pages)s, %(price)s, %(currency_unit)s,
                            %(binding)s, %(isbn)s, %(tags)s)
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
                        isbn = VALUES(isbn),
                        tags = VALUES(tags)
                """
                mysql_cursor.execute(insert_sql, mysql_data)
                
                # 准备MongoDB数据（BLOB信息）
                blob_data = {
                    'book_id': book_id,
                    'author_intro': row['author_intro'] or '',
                    'book_intro': row['book_intro'] or '',
                    'content': row['content'] or '',
                    'picture': row['picture'],  # BLOB数据
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                # 插入到MongoDB (upsert)
                mongo_db['book_details'].replace_one(
                    {'book_id': book_id},
                    blob_data,
                    upsert=True
                )
                
                migrated_count += 1
                if migrated_count % 1000 == 0:
                    logging.info(f"已迁移 {migrated_count}/{total_books} 条图书数据...")
                    mysql_conn.commit()
                    
            except Exception as e:
                logging.error(f"迁移图书 {row['id'] if 'id' in row.keys() else 'unknown'} 失败: {e}")
                continue
        
        mysql_conn.commit()
        logging.info(f"图书数据迁移完成，成功迁移 {migrated_count} 条记录")
        
    except Exception as e:
        logging.error(f"图书数据迁移失败: {e}")
        mysql_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        mysql_conn.close()
        mongo_client.close()

def migrate_users_data():
    """
    注意：SQLite中的book.db只包含图书数据，不包含用户数据
    用户数据由系统运行时动态创建
    此函数保留用于从其他数据源迁移用户数据
    """
    logging.info("SQLite数据库中无用户数据，跳过用户数据迁移")
    pass

def migrate_stores_data():
    """
    注意：SQLite中的book.db只包含图书数据，不包含商店数据
    商店数据由系统运行时动态创建
    此函数保留用于从其他数据源迁移商店数据
    """
    logging.info("SQLite数据库中无商店数据，跳过商店数据迁移")
    pass

def main():
    """主函数"""
    try:
        logging.info("="*60)
        logging.info("开始从SQLite迁移数据到MySQL+MongoDB混合架构...")
        logging.info(f"SQLite数据库路径: {SQLITE_DB_PATH}")
        logging.info("="*60)
        
        # 检查SQLite数据库文件是否存在
        if not os.path.exists(SQLITE_DB_PATH):
            logging.error(f"错误：找不到SQLite数据库文件 {SQLITE_DB_PATH}")
            logging.info("请确保 fe/data/book_lx.db 文件存在")
            logging.info("如果没有，请从网盘下载或使用 book.db")
            sys.exit(1)
        
        # 迁移图书数据（唯一需要从SQLite迁移的数据）
        migrate_books_data()
        
        # 用户和商店数据由系统运行时创建，无需迁移
        migrate_users_data()
        migrate_stores_data()
        
        logging.info("="*60)
        logging.info("数据迁移完成！")
        logging.info("图书基础信息已存储到MySQL")
        logging.info("图书BLOB数据（图片、长文本）已存储到MongoDB")
        logging.info("="*60)
        
    except Exception as e:
        logging.error(f"数据迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()