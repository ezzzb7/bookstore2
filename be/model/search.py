import logging
from be.model import db_conn
from be.model import error


class Search(db_conn.DBConn):
    def __init__(self):
        super().__init__()
        self._text_index_created = False
    
    def _ensure_text_index(self):
        """确保MongoDB文本索引存在（只创建一次）"""
        if self._text_index_created:
            return
        
        try:
            mongo_db = self.mongo_db
            book_details = mongo_db['book_details']
            
            # 检查索引是否已存在
            existing_indexes = list(book_details.list_indexes())
            has_text_index = any('textIndexVersion' in str(idx) or 
                               idx.get('name') == 'content_text_idx' 
                               for idx in existing_indexes)
            
            if not has_text_index:
                # 创建文本索引（支持中英文）
                book_details.create_index(
                    [("book_intro", "text"), ("content", "text"), ("author_intro", "text")],
                    name="content_text_idx",
                    default_language="none"  # 支持中文
                )
                logging.info("MongoDB文本索引创建成功")
            
            self._text_index_created = True
        except Exception as e:
            logging.warning(f"创建MongoDB文本索引失败（可能已存在）: {e}")
            self._text_index_created = True  # 标记为已尝试，避免重复

    def search_books(
        self, keyword: str, store_id: str = None, page: int = 1, page_size: int = 20,
        search_scope: str = "all"
    ) -> (int, str, list, int):
        """
        搜索图书
        :param keyword: 搜索关键字
        :param store_id: 商店ID，如果指定则只在该商店搜索
        :param page: 页码，从1开始
        :param page_size: 每页大小
        :param search_scope: 搜索范围 - all, title, author, tags, content
        :return: (状态码, 消息, 图书列表, 总数)
        """
        conn = None
        try:
            # 参数验证
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # 处理空关键字
            if not keyword or keyword.strip() == "":
                return 200, "ok", [], 0

            conn = self.mysql_conn
            cursor = conn.cursor()
            
            offset = (page - 1) * page_size
            
            # 构建搜索条件
            if search_scope in ["title", "author", "tags"]:
                # LIKE搜索（title, author, tags）
                if search_scope == "title":
                    search_condition = "b.title LIKE %s"
                elif search_scope == "author":
                    search_condition = "b.author LIKE %s"
                else:  # tags
                    search_condition = "b.tags LIKE %s"
                
                search_keyword = f"%{keyword}%"
                
                if store_id:
                    # 在特定商店搜索
                    query = """
                        SELECT DISTINCT b.book_id, b.title, b.author, b.publisher, 
                               b.price, b.tags, si.stock_level, si.store_price
                        FROM books b
                        INNER JOIN store_inventory si ON b.book_id = si.book_id
                        WHERE si.store_id = %s AND """ + search_condition + """
                        ORDER BY b.title
                        LIMIT %s OFFSET %s
                    """
                    params = (store_id, search_keyword, page_size, offset)
                    
                    count_query = """
                        SELECT COUNT(DISTINCT b.book_id)
                        FROM books b
                        INNER JOIN store_inventory si ON b.book_id = si.book_id
                        WHERE si.store_id = %s AND """ + search_condition
                    count_params = (store_id, search_keyword)
                else:
                    # 全站搜索
                    query = """
                        SELECT DISTINCT b.book_id, b.title, b.author, b.publisher, 
                               b.price, b.tags
                        FROM books b
                        WHERE """ + search_condition + """
                        ORDER BY b.title
                        LIMIT %s OFFSET %s
                    """
                    params = (search_keyword, page_size, offset)
                    
                    count_query = """
                        SELECT COUNT(DISTINCT b.book_id)
                        FROM books b
                        WHERE """ + search_condition
                    count_params = (search_keyword,)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()[0]
                
            elif search_scope == "content":
                # 对于content搜索，使用MongoDB文本索引（比正则快100倍以上）
                try:
                    mongo_db = self.mongo_db
                    if mongo_db is None:
                        return 200, "ok", [], 0
                        
                    book_details = mongo_db['book_details']
                    
                    # 确保文本索引存在（只在第一次调用时创建）
                    self._ensure_text_index()
                    
                    # 使用文本索引搜索（比正则表达式快得多）
                    if len(keyword) <= 2:
                        # 短关键字使用精确匹配
                        search_query = {"$text": {"$search": f'"{keyword}"'}}
                    else:
                        # 长关键字使用文本搜索
                        search_query = {"$text": {"$search": keyword}}
                    
                    # 执行搜索，添加相关度评分
                    search_results = list(book_details.find(
                        search_query,
                        {"book_id": 1, "_id": 0, "score": {"$meta": "textScore"}}
                    ).sort([("score", {"$meta": "textScore"})]).limit(1000))
                    
                    book_ids = [result['book_id'] for result in search_results if 'book_id' in result]
                except Exception as mongo_error:
                    # MongoDB查询失败时记录日志并返回空结果
                    logging.warning(f"MongoDB content搜索失败: {mongo_error}")
                    return 200, "ok", [], 0
                
                if not book_ids:
                    return 200, "ok", [], 0
                
                # 在MySQL中查询这些书籍的详细信息
                placeholders = ','.join(['%s'] * len(book_ids))
                
                if store_id:
                    # 在特定商店搜索
                    query = f"""
                        SELECT DISTINCT b.book_id, b.title, b.author, b.publisher, 
                               b.price, b.tags, si.stock_level, si.store_price
                        FROM books b
                        INNER JOIN store_inventory si ON b.book_id = si.book_id
                        WHERE si.store_id = %s AND b.book_id IN ({placeholders})
                        ORDER BY b.title
                        LIMIT %s OFFSET %s
                    """
                    params = [store_id] + book_ids + [page_size, offset]
                    
                    count_query = f"""
                        SELECT COUNT(DISTINCT b.book_id)
                        FROM books b
                        INNER JOIN store_inventory si ON b.book_id = si.book_id
                        WHERE si.store_id = %s AND b.book_id IN ({placeholders})
                    """
                    count_params = [store_id] + book_ids
                else:
                    # 全站搜索
                    query = f"""
                        SELECT DISTINCT b.book_id, b.title, b.author, b.publisher, 
                               b.price, b.tags
                        FROM books b
                        WHERE b.book_id IN ({placeholders})
                        ORDER BY b.title
                        LIMIT %s OFFSET %s
                    """
                    params = book_ids + [page_size, offset]
                    
                    count_query = f"""
                        SELECT COUNT(DISTINCT b.book_id)
                        FROM books b
                        WHERE b.book_id IN ({placeholders})
                    """
                    count_params = book_ids
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()[0]
                
            else:
                # 默认搜索所有字段（使用全文索引）
                search_condition = "MATCH(b.title, b.author, b.tags) AGAINST(%s IN NATURAL LANGUAGE MODE)"
                search_keyword = keyword
                
                if store_id:
                    # 在特定商店搜索
                    query = """
                        SELECT DISTINCT b.book_id, b.title, b.author, b.publisher, 
                               b.price, b.tags, si.stock_level, si.store_price
                        FROM books b
                        INNER JOIN store_inventory si ON b.book_id = si.book_id
                        WHERE si.store_id = %s AND """ + search_condition + """
                        ORDER BY b.title
                        LIMIT %s OFFSET %s
                    """
                    params = (store_id, search_keyword, page_size, offset)
                    
                    count_query = """
                        SELECT COUNT(DISTINCT b.book_id)
                        FROM books b
                        INNER JOIN store_inventory si ON b.book_id = si.book_id
                        WHERE si.store_id = %s AND """ + search_condition
                    count_params = (store_id, search_keyword)
                else:
                    # 全站搜索
                    query = """
                        SELECT DISTINCT b.book_id, b.title, b.author, b.publisher, 
                               b.price, b.tags
                        FROM books b
                        WHERE """ + search_condition + """
                        ORDER BY b.title
                        LIMIT %s OFFSET %s
                    """
                    params = (search_keyword, page_size, offset)
                    
                    count_query = """
                        SELECT COUNT(DISTINCT b.book_id)
                        FROM books b
                        WHERE """ + search_condition
                    count_params = (search_keyword,)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()[0]
            
            # 格式化结果
            books = []
            if store_id and search_scope != "content":
                for row in results:
                    book_info = {
                        "book_id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "publisher": row[3],
                        "price": float(row[4]) if row[4] else 0,
                        "tags": row[5],
                        "stock_level": row[6],
                        "store_price": float(row[7]) if row[7] else 0
                    }
                    books.append(book_info)
            else:
                for row in results:
                    book_info = {
                        "book_id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "publisher": row[3],
                        "price": float(row[4]) if row[4] else 0,
                        "tags": row[5]
                    }
                    if store_id and len(row) > 6:
                        book_info["stock_level"] = row[6]
                        book_info["store_price"] = float(row[7]) if row[7] else 0
                    books.append(book_info)
            
            return 200, "ok", books, total

        except Exception as e:
            logging.error(f"搜索图书失败: {e}")
            return 530, f"搜索失败: {str(e)}", [], 0
        finally:
            if conn:
                conn.close()
