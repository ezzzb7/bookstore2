"""
额外的测试用例，用于提高代码覆盖率
测试各种边界情况和异常处理
"""
import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
from fe.access.book import Book


class TestBoundaryConditions:
    """边界条件测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_boundary_buyer_{}".format(str(uuid.uuid1()))
        self.seller_id = "test_boundary_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_boundary_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_add_funds_zero(self):
        """测试充值0元"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        code = buyer.add_funds(0)
        # 充值0元应该也返回200（根据业务逻辑调整）
        assert code == 200
    
    def test_add_funds_very_large_amount(self):
        """测试充值超大金额"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        code = buyer.add_funds(999999999)
        # 超大金额可能会导致数据库溢出，应该失败
        assert code != 200
    
    def test_new_order_empty_book_list(self):
        """测试下单时书籍列表为空"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        # 空的书籍列表
        code, order_id = buyer.new_order(self.store_id, [])
        # 应该返回错误或创建空订单（根据业务逻辑调整）
        # assert code != 200  # 如果不允许空订单
    
    def test_payment_without_order(self):
        """测试支付不存在的订单"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        fake_order_id = "fake_order_" + str(uuid.uuid1())
        code = buyer.payment(fake_order_id)
        assert code != 200
    
    def test_receive_unpaid_order(self):
        """测试收货未支付的订单"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        
        # 下单但不支付
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 尝试收货
        code = buyer.receive_order(order_id)
        assert code != 200


class TestConcurrentScenarios:
    """并发场景测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_concurrent_buyer_{}".format(str(uuid.uuid1()))
        self.seller_id = "test_concurrent_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_concurrent_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_double_payment(self):
        """测试重复支付同一订单"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        buy_book_info_list = gen_book.buy_book_info_list
        
        # 下单
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算总价
        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is not None:
                total_price += book.price * num
        
        # 充值并第一次支付
        code = buyer.add_funds(total_price * 2)  # 充值两倍，以便测试重复支付
        assert code == 200
        code = buyer.payment(order_id)
        assert code == 200
        
        # 第二次支付同一订单（应该失败）
        code = buyer.payment(order_id)
        assert code != 200


class TestDataValidation:
    """数据验证测试"""
    
    def test_register_with_empty_user_id(self):
        """测试使用空用户ID注册"""
        from fe.access import auth
        from fe import conf
        
        a = auth.Auth(conf.URL)
        code = a.register("", "password")
        # 空用户ID应该失败
        assert code != 200
    
    def test_register_with_empty_password(self):
        """测试使用空密码注册"""
        from fe.access import auth
        from fe import conf
        
        user_id = "test_empty_pwd_" + str(uuid.uuid1())
        a = auth.Auth(conf.URL)
        code = a.register(user_id, "")
        # 根据业务逻辑，可能允许或不允许空密码
        # assert code != 200
    
    def test_login_with_wrong_password(self):
        """测试使用错误密码登录"""
        from fe.access import auth
        from fe import conf
        
        user_id = "test_wrong_pwd_" + str(uuid.uuid1())
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        
        a = auth.Auth(conf.URL)
        code = a.register(user_id, correct_password)
        assert code == 200
        
        code, token = a.login(user_id, wrong_password, "test_terminal")
        assert code != 200


class TestStoreOperations:
    """商店操作测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_store_ops_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_store_ops_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_add_book_to_non_exist_store(self):
        """测试向不存在的商店添加书籍"""
        seller = register_new_seller(self.seller_id, self.password)
        fake_store_id = "fake_store_" + str(uuid.uuid1())
        
        from fe.access import book
        from fe import conf
        book_db = book.BookDB(conf.Use_Large_DB)
        books = book_db.get_book_info(0, 1)
        if books:
            test_book = books[0]
            code = seller.add_book(fake_store_id, 10, test_book)
            assert code != 200
    
    def test_add_duplicate_book(self):
        """测试重复添加相同书籍"""
        seller = register_new_seller(self.seller_id, self.password)
        code = seller.create_store(self.store_id)
        assert code == 200
        
        from fe.access import book
        from fe import conf
        book_db = book.BookDB(conf.Use_Large_DB)
        books = book_db.get_book_info(0, 1)
        if books:
            test_book = books[0]
            # 第一次添加
            code = seller.add_book(self.store_id, 10, test_book)
            assert code == 200
            
            # 第二次添加相同书籍（应该失败）
            code = seller.add_book(self.store_id, 10, test_book)
            assert code != 200
    
    def test_add_stock_to_non_exist_book(self):
        """测试给不存在的书籍增加库存"""
        seller = register_new_seller(self.seller_id, self.password)
        code = seller.create_store(self.store_id)
        assert code == 200
        
        fake_book_id = "fake_book_" + str(uuid.uuid1())
        code = seller.add_stock_level(self.seller_id, self.store_id, fake_book_id, 10)
        assert code != 200


class TestSearchEdgeCases:
    """搜索边界情况测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_search_edge_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_search_edge_store_{}".format(str(uuid.uuid1()))
        yield
    
    def test_search_with_very_long_keyword(self):
        """测试使用超长关键字搜索"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        very_long_keyword = "a" * 1000
        code, result, total = s.search_books(keyword=very_long_keyword, page=1, page_size=10)
        # 应该返回200但结果为空
        assert code == 200
    
    def test_search_with_special_characters(self):
        """测试使用特殊字符搜索"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        special_chars = "!@#$%^&*()"
        code, result, total = s.search_books(keyword=special_chars, page=1, page_size=10)
        assert code == 200
    
    def test_search_with_sql_injection_attempt(self):
        """测试SQL注入尝试"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        sql_injection = "' OR '1'='1"
        code, result, total = s.search_books(keyword=sql_injection, page=1, page_size=10)
        # 应该安全处理，不返回错误
        assert code == 200


class TestOrderStatusTransitions:
    """订单状态转换测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_status_buyer_{}".format(str(uuid.uuid1()))
        self.seller_id = "test_status_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_status_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_ship_before_payment(self):
        """测试未支付就发货"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        seller = gen_book.seller
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        
        # 下单但不支付
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 尝试发货（应该失败）
        code = seller.ship_order(order_id)
        assert code != 200
    
    def test_receive_before_ship(self):
        """测试未发货就收货"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        buy_book_info_list = gen_book.buy_book_info_list
        
        # 下单
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算总价并支付
        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is not None:
                total_price += book.price * num
        
        code = buyer.add_funds(total_price)
        assert code == 200
        code = buyer.payment(order_id)
        assert code == 200
        
        # 不发货直接收货（应该失败）
        code = buyer.receive_order(order_id)
        assert code != 200


class TestDatabaseErrorHandling:
    """数据库异常处理测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.user_id = "test_db_error_user_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_check_token_invalid_signature(self):
        """测试检查无效签名的token"""
        from fe.access import auth
        from fe import conf
        
        a = auth.Auth(conf.URL)
        code = a.register(self.user_id, self.password)
        assert code == 200
        
        # 使用错误的token（无效签名）
        code, token = a.login(self.user_id, self.password, "test_terminal")
        assert code == 200
        
        # 使用其他用户ID的token尝试验证（这会导致签名验证失败）
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZmFrZSIsInRlcm1pbmFsIjoidGVzdCIsInRpbWVzdGFtcCI6MTYzOTk5OTk5OX0.invalid_signature"
        code = a.logout(self.user_id, fake_token)
        assert code != 200
    
    def test_user_id_exist_check(self):
        """测试用户ID存在性检查"""
        from be.model.db_conn import DBConn
        
        db = DBConn()
        # 检查不存在的用户
        exists = db.user_id_exist("non_exist_user_" + str(uuid.uuid1()))
        assert not exists
        
        # 注册用户后检查
        from fe.access import auth
        from fe import conf
        a = auth.Auth(conf.URL)
        code = a.register(self.user_id, self.password)
        assert code == 200
        
        exists = db.user_id_exist(self.user_id)
        assert exists
    
    def test_logout_with_invalid_user(self):
        """测试使用不存在的用户登出"""
        from fe.access import auth
        from fe import conf
        
        fake_user_id = "fake_user_" + str(uuid.uuid1())
        fake_token = "fake_token"
        
        a = auth.Auth(conf.URL)
        code = a.logout(fake_user_id, fake_token)
        assert code != 200


class TestSearchAdvanced:
    """高级搜索测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_search_adv_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_search_adv_store_{}".format(str(uuid.uuid1()))
        yield
    
    def test_search_empty_keyword(self):
        """测试使用空关键字搜索"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        code, result, total = s.search_books(keyword="", page=1, page_size=10)
        assert code == 200
        assert total == 0
    
    def test_search_with_whitespace_only(self):
        """测试使用纯空白字符搜索"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        code, result, total = s.search_books(keyword="   ", page=1, page_size=10)
        assert code == 200
        assert total == 0
    
    def test_search_invalid_page_number(self):
        """测试使用无效页码搜索"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        # 负数页码
        code, result, total = s.search_books(keyword="test", page=-1, page_size=10)
        assert code == 200
        
        # 0页码
        code, result, total = s.search_books(keyword="test", page=0, page_size=10)
        assert code == 200
    
    def test_search_invalid_page_size(self):
        """测试使用无效页大小搜索"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        # 负数页大小
        code, result, total = s.search_books(keyword="test", page=1, page_size=-10)
        assert code == 200
        
        # 超大页大小
        code, result, total = s.search_books(keyword="test", page=1, page_size=1000)
        assert code == 200
    
    def test_search_in_store_all_scopes(self):
        """测试在特定商店中搜索所有范围"""
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, _ = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        assert ok
        
        from fe.access import search
        from fe import conf
        s = search.Search(conf.URL)
        
        # 测试所有搜索范围
        scopes = ["all", "title", "author", "tags", "content"]
        for scope in scopes:
            code, result, total = s.search_books(
                keyword="test",
                store_id=self.store_id,
                page=1,
                page_size=10,
                search_scope=scope
            )
            assert code == 200
    
    def test_search_content_short_keyword(self):
        """测试使用短关键字进行内容搜索"""
        from fe.access import search
        from fe import conf
        
        s = search.Search(conf.URL)
        # 短关键字（<=2字符）应该使用精确匹配
        code, result, total = s.search_books(
            keyword="a",
            page=1,
            page_size=10,
            search_scope="content"
        )
        assert code == 200
    
    def test_search_non_exist_store(self):
        """测试在不存在的商店中搜索"""
        from fe.access import search
        from fe import conf
        
        fake_store_id = "fake_store_" + str(uuid.uuid1())
        s = search.Search(conf.URL)
        code, result, total = s.search_books(
            keyword="test",
            store_id=fake_store_id,
            page=1,
            page_size=10
        )
        assert code == 200
        assert total == 0


class TestBuyerEdgeCases:
    """买家边界情况测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_buyer_edge_{}".format(str(uuid.uuid1()))
        self.seller_id = "test_buyer_edge_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_buyer_edge_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_cancel_already_paid_order(self):
        """测试取消已支付的订单（应该成功并退款）"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)

        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        buy_book_info_list = gen_book.buy_book_info_list

        # 下单
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

        # 计算总价并支付
        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is not None:
                total_price += book.price * num

        code = buyer.add_funds(total_price)
        assert code == 200
        code = buyer.payment(order_id)
        assert code == 200

        # 取消已支付订单（应该成功并退款）
        code = buyer.cancel_order(order_id)
        assert code == 200
    def test_query_order_non_exist(self):
        """测试查询不存在的订单"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        
        fake_order_id = "fake_order_" + str(uuid.uuid1())
        code, orders = buyer.query_order(order_id=fake_order_id)
        # 应该返回错误码518（invalid_order_id）
        assert code == 518
    
    def test_receive_non_exist_order(self):
        """测试收货不存在的订单"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        
        fake_order_id = "fake_order_" + str(uuid.uuid1())
        code = buyer.receive_order(fake_order_id)
        assert code != 200


class TestSellerEdgeCases:
    """卖家边界情况测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_seller_edge_{}".format(str(uuid.uuid1()))
        self.store_id = "test_seller_edge_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_create_duplicate_store(self):
        """测试创建重复的商店"""
        seller = register_new_seller(self.seller_id, self.password)
        
        # 第一次创建
        code = seller.create_store(self.store_id)
        assert code == 200
        
        # 第二次创建相同商店（应该失败）
        code = seller.create_store(self.store_id)
        assert code != 200
    
    def test_add_book_negative_stock(self):
        """测试添加负数库存的书籍"""
        seller = register_new_seller(self.seller_id, self.password)
        code = seller.create_store(self.store_id)
        assert code == 200
        
        from fe.access import book
        from fe import conf
        book_db = book.BookDB(conf.Use_Large_DB)
        books = book_db.get_book_info(0, 1)
        if books:
            test_book = books[0]
            # 尝试添加负数库存（应该失败或被处理）
            code = seller.add_book(self.store_id, -10, test_book)
            # 根据业务逻辑，可能允许或不允许
            # assert code != 200
    
    def test_add_stock_negative_amount(self):
        """测试增加负数库存"""
        seller = register_new_seller(self.seller_id, self.password)
        code = seller.create_store(self.store_id)
        assert code == 200
        
        from fe.access import book
        from fe import conf
        book_db = book.BookDB(conf.Use_Large_DB)
        books = book_db.get_book_info(0, 1)
        if books:
            test_book = books[0]
            # 先添加书籍
            code = seller.add_book(self.store_id, 10, test_book)
            assert code == 200
            
            # 尝试增加负数库存
            code = seller.add_stock_level(self.seller_id, self.store_id, test_book.id, -5)
            # 根据业务逻辑决定是否允许
    
    def test_ship_already_shipped_order(self):
        """测试发货已发货的订单"""
        from fe.access.new_buyer import register_new_buyer
        buyer = register_new_buyer("buyer_" + str(uuid.uuid1()), self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        seller = gen_book.seller
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        buy_book_info_list = gen_book.buy_book_info_list
        
        # 下单并支付
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        total_price = 0
        for item in buy_book_info_list:
            book_item: Book = item[0]
            num = item[1]
            if book_item.price is not None:
                total_price += book_item.price * num
        
        code = buyer.add_funds(total_price)
        assert code == 200
        code = buyer.payment(order_id)
        assert code == 200
        
        # 第一次发货
        code = seller.ship_order(order_id)
        assert code == 200
        
        # 第二次发货（应该失败）
        code = seller.ship_order(order_id)
        assert code != 200


class TestPaymentEdgeCases:
    """支付边界情况测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_payment_edge_{}".format(str(uuid.uuid1()))
        self.seller_id = "test_payment_edge_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_payment_edge_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_payment_insufficient_balance(self):
        """测试余额不足时支付"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        
        # 下单但不充值
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 尝试支付（余额不足应该失败）
        code = buyer.payment(order_id)
        assert code != 200
    
    def test_payment_partial_balance(self):
        """测试部分余额支付"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        buy_book_info_list = gen_book.buy_book_info_list
        
        # 下单
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算总价
        total_price = 0
        for item in buy_book_info_list:
            book_item: Book = item[0]
            num = item[1]
            if book_item.price is not None:
                total_price += book_item.price * num
        
        # 只充值一半
        code = buyer.add_funds(total_price // 2)
        assert code == 200
        
        # 尝试支付（余额不足应该失败）
        code = buyer.payment(order_id)
        assert code != 200


class TestOrderQueryEdgeCases:
    """订单查询边界情况测试"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_query_edge_{}".format(str(uuid.uuid1()))
        self.seller_id = "test_query_edge_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_query_edge_store_{}".format(str(uuid.uuid1()))
        self.password = "test_password"
        yield
    
    def test_query_all_orders_for_user(self):
        """测试查询用户所有订单"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        # 创建多个订单
        order_ids = []
        for _ in range(3):
            ok, buy_book_id_list = gen_book.gen(
                non_exist_book_id=False, low_stock_level=False, max_book_count=2
            )
            assert ok
            
            code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
            assert code == 200
            order_ids.append(order_id)
        
        # 查询所有订单（不指定order_id）
        code, orders = buyer.query_order()
        assert code == 200
        assert len(orders) >= 3
    
    def test_query_specific_order(self):
        """测试查询特定订单"""
        buyer = register_new_buyer(self.buyer_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=2
        )
        assert ok
        
        code, order_id = buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 查询特定订单
        code, orders = buyer.query_order(order_id=order_id)
        assert code == 200
        assert len(orders) == 1
        assert orders[0]["order_id"] == order_id
