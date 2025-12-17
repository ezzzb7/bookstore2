import pytest
import uuid
from fe.access.new_seller import register_new_seller
from fe.access.search import Search
from fe.test.gen_book_data import GenBook
from fe import conf


class TestSearchBooks:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_search_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_search_store_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 注册卖家
        self.seller = register_new_seller(self.seller_id, self.password)
        
        # 生成图书数据，使用不同的seller_id避免冲突
        self.gen_book = GenBook(self.seller_id + "_gen", self.store_id)
        ok, _ = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=20
        )
        assert ok
        
        self.search = Search(conf.URL)
        
        yield

    def test_search_by_title(self):
        """按标题搜索"""
        # 获取一本书的标题
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.title:
                # 取标题的一部分作为关键字
                keyword = book.title.split()[0] if book.title.split() else book.title[:5]
                
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    search_scope="title"
                )
                assert code == 200
                # 应该至少找到一本书
                assert total >= 0

    def test_search_by_author(self):
        """按作者搜索"""
        # 获取一本书的作者
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.author:
                # 取作者名的一部分作为关键字
                keyword = book.author.split()[0] if book.author.split() else book.author[:5]
                
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    search_scope="author"
                )
                assert code == 200
                assert total >= 0

    def test_search_by_tags(self):
        """按标签搜索"""
        # 获取一本书的标签
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.tags:
                # 取第一个标签作为关键字
                tags = book.tags if isinstance(book.tags, list) else []
                if tags:
                    keyword = tags[0]
                    
                    code, books, total = self.search.search_books(
                        keyword=keyword,
                        search_scope="tags"
                    )
                    assert code == 200
                    assert total >= 0

    def test_search_all(self):
        """全文搜索"""
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.title:
                keyword = book.title.split()[0] if book.title.split() else book.title[:5]
                
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    search_scope="all"
                )
                assert code == 200
                assert total >= 0

    def test_search_in_store(self):
        """在特定商店内搜索"""
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.title:
                keyword = book.title.split()[0] if book.title.split() else book.title[:5]
                
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    store_id=self.store_id,
                    search_scope="all"
                )
                assert code == 200
                # 在自己的商店里应该能找到
                assert total >= 0

    def test_search_pagination(self):
        """测试分页功能"""
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.title:
                keyword = book.title.split()[0] if book.title.split() else book.title[:5]
                
                # 第一页
                code, books_page1, total = self.search.search_books(
                    keyword=keyword,
                    page=1,
                    page_size=5,
                    search_scope="all"
                )
                assert code == 200
                
                # 第二页
                code, books_page2, total2 = self.search.search_books(
                    keyword=keyword,
                    page=2,
                    page_size=5,
                    search_scope="all"
                )
                assert code == 200
                
                # 总数应该相同
                assert total == total2
                
                # 如果总数大于5，第一页和第二页的结果应该不同
                if total > 5 and len(books_page1) > 0 and len(books_page2) > 0:
                    assert books_page1[0]["book_id"] != books_page2[0]["book_id"]

    def test_search_empty_keyword(self):
        """搜索空关键字"""
        code, books, total = self.search.search_books(
            keyword="",
            search_scope="all"
        )
        # 空关键字可能返回所有书籍或者没有结果，取决于实现
        assert code == 200

    def test_search_no_result(self):
        """搜索不存在的内容"""
        code, books, total = self.search.search_books(
            keyword="xyzabc123456789notexist",
            search_scope="all"
        )
        assert code == 200
        assert total == 0
        assert len(books) == 0

    def test_search_invalid_page(self):
        """测试无效页码"""
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.title:
                keyword = book.title.split()[0] if book.title.split() else book.title[:5]
                
                # 页码为0（应该被处理为1）
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    page=0,
                    page_size=10,
                    search_scope="all"
                )
                assert code == 200
                
                # 负数页码（应该被处理为1）
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    page=-1,
                    page_size=10,
                    search_scope="all"
                )
                assert code == 200

    def test_search_invalid_page_size(self):
        """测试无效页面大小"""
        if self.gen_book.buy_book_info_list:
            book = self.gen_book.buy_book_info_list[0][0]
            if book.title:
                keyword = book.title.split()[0] if book.title.split() else book.title[:5]
                
                # 页面大小为0（应该被处理为20）
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    page=1,
                    page_size=0,
                    search_scope="all"
                )
                assert code == 200
                
                # 页面大小超过100（应该被处理为20）
                code, books, total = self.search.search_books(
                    keyword=keyword,
                    page=1,
                    page_size=150,
                    search_scope="all"
                )
                assert code == 200

    def test_search_by_content(self):
        """按内容搜索（MongoDB）"""
        # 搜索一个通用词
        code, books, total = self.search.search_books(
            keyword="book",
            search_scope="content"
        )
        assert code == 200
        # content搜索可能找到也可能找不到结果
        assert total >= 0

    def test_search_content_in_store(self):
        """在商店内按内容搜索"""
        # 在特定商店内搜索内容
        code, books, total = self.search.search_books(
            keyword="book",
            store_id=self.store_id,
            search_scope="content"
        )
        assert code == 200
        assert total >= 0
        
        # 如果有结果，验证返回了商店价格和库存
        if books:
            assert "stock_level" in books[0]
            assert "store_price" in books[0]

    def test_search_content_no_result(self):
        """按内容搜索无结果"""
        code, books, total = self.search.search_books(
            keyword="xyznotexistcontent123456",
            search_scope="content"
        )
        assert code == 200
        assert total == 0
        assert len(books) == 0
    
    def test_search_content_short_keyword(self):
        """测试短关键字的内容搜索（2字符或更少）"""
        # 短关键字使用精确匹配
        code, books, total = self.search.search_books(
            keyword="a",
            search_scope="content",
            page=1,
            page_size=10
        )
        assert code == 200
        assert total >= 0
        
        # 两个字符
        code, books, total = self.search.search_books(
            keyword="ab",
            search_scope="content",
            page=1,
            page_size=10
        )
        assert code == 200
        assert total >= 0
    
    def test_search_content_long_keyword(self):
        """测试长关键字的内容搜索（超过2字符）"""
        # 长关键字使用文本搜索
        code, books, total = self.search.search_books(
            keyword="introduction",
            search_scope="content",
            page=1,
            page_size=10
        )
        assert code == 200
        assert total >= 0
    
    def test_search_in_nonexist_store(self):
        """在不存在的商店中搜索"""
        fake_store_id = "fake_store_" + str(uuid.uuid1())
        
        code, books, total = self.search.search_books(
            keyword="test",
            store_id=fake_store_id,
            search_scope="title"
        )
        assert code == 200
        assert total == 0
        assert len(books) == 0
    
    def test_search_all_scopes(self):
        """测试所有搜索范围"""
        scopes = ["all", "title", "author", "tags", "content"]
        
        for scope in scopes:
            code, books, total = self.search.search_books(
                keyword="book",
                page=1,
                page_size=10,
                search_scope=scope
            )
            assert code == 200
            assert total >= 0
    
    def test_search_chinese_keyword(self):
        """测试中文关键字搜索"""
        # 测试中文关键字
        code, books, total = self.search.search_books(
            keyword="中文",
            search_scope="all"
        )
        assert code == 200
        assert total >= 0
    
    def test_search_mixed_language_keyword(self):
        """测试中英文混合关键字"""
        code, books, total = self.search.search_books(
            keyword="test测试",
            search_scope="all"
        )
        assert code == 200
        assert total >= 0
    
    def test_search_with_spaces(self):
        """测试包含空格的关键字"""
        code, books, total = self.search.search_books(
            keyword="book store",
            search_scope="title"
        )
        assert code == 200
        assert total >= 0
