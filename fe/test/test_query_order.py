import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
from fe.access.book import Book


class TestQueryOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_query_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_query_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_query_buyer_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 注册卖家和买家
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成图书数据，使用不同的seller_id避免冲突
        self.gen_book = GenBook(self.seller_id + "_gen", self.store_id)
        
        yield

    def test_query_single_order(self):
        """查询单个订单"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 查询订单
        code, orders = self.buyer.query_order(order_id)
        assert code == 200
        assert len(orders) == 1
        assert orders[0]["order_id"] == order_id
        assert orders[0]["status"] == "pending"

    def test_query_all_orders(self):
        """查询所有订单"""
        # 创建多个订单
        order_ids = []
        for i in range(3):
            ok, buy_book_id_list = self.gen_book.gen(
                non_exist_book_id=False, low_stock_level=False, max_book_count=3
            )
            assert ok
            code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
            assert code == 200
            order_ids.append(order_id)
        
        # 查询所有订单
        code, orders = self.buyer.query_order()
        assert code == 200
        assert len(orders) >= 3
        
        # 验证订单ID都在结果中
        result_order_ids = [order["order_id"] for order in orders]
        for order_id in order_ids:
            assert order_id in result_order_ids

    def test_query_non_exist_order(self):
        """查询不存在的订单"""
        code, orders = self.buyer.query_order("non_exist_order_id")
        assert code != 200

    def test_query_wrong_user(self):
        """查询其他用户的订单"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 另一个用户尝试查询
        another_buyer = register_new_buyer("another_buyer_{}".format(str(uuid.uuid1())), self.password)
        code, orders = another_buyer.query_order(order_id)
        assert code != 200

    def test_query_order_with_different_status(self):
        """查询不同状态的订单"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        buy_book_info_list = self.gen_book.buy_book_info_list
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 查询待支付订单
        code, orders = self.buyer.query_order(order_id)
        assert code == 200
        assert orders[0]["status"] == "pending"
        
        # 计算总价
        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                total_price = total_price + book.price * num
        
        # 支付
        code = self.buyer.add_funds(total_price)
        assert code == 200
        code = self.buyer.payment(order_id)
        assert code == 200
        
        # 查询已支付订单
        code, orders = self.buyer.query_order(order_id)
        assert code == 200
        assert orders[0]["status"] == "paid"
        
        # 发货
        code = self.seller.ship_order(order_id)
        assert code == 200
        
        # 查询已发货订单
        code, orders = self.buyer.query_order(order_id)
        assert code == 200
        assert orders[0]["status"] == "shipped"
        
        # 收货
        code = self.buyer.receive_order(order_id)
        assert code == 200
        
        # 查询已收货订单
        code, orders = self.buyer.query_order(order_id)
        assert code == 200
        assert orders[0]["status"] == "delivered"


class TestQueryStoreOrders:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_store_query_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_store_query_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_store_query_buyer_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 注册卖家和买家
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成图书数据，使用不同的seller_id避免冲突
        self.gen_book = GenBook(self.seller_id + "_gen", self.store_id)
        
        yield

    def test_query_store_orders_ok(self):
        """查询商店订单"""
        # 创建多个订单
        order_ids = []
        for i in range(3):
            ok, buy_book_id_list = self.gen_book.gen(
                non_exist_book_id=False, low_stock_level=False, max_book_count=3
            )
            assert ok
            code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
            assert code == 200
            order_ids.append(order_id)
        
        # 查询商店订单
        code, orders = self.seller.query_store_orders(self.store_id)
        assert code == 200
        assert len(orders) >= 3
        
        # 验证订单ID都在结果中
        result_order_ids = [order["order_id"] for order in orders]
        for order_id in order_ids:
            assert order_id in result_order_ids

    def test_query_non_exist_store(self):
        """查询不存在的商店"""
        code, orders = self.seller.query_store_orders("non_exist_store_id")
        assert code != 200

    def test_query_wrong_seller(self):
        """非商店卖家查询订单"""
        another_seller = register_new_seller("another_seller_{}".format(str(uuid.uuid1())), self.password)
        code, orders = another_seller.query_store_orders(self.store_id)
        assert code != 200
