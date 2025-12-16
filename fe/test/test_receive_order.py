import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
from fe.access.book import Book


class TestReceiveOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_receive_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_receive_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_receive_buyer_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 注册卖家和买家
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成图书数据，使用不同的seller_id避免冲突
        self.gen_book = GenBook(self.seller_id + "_gen", self.store_id)
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        self.buy_book_info_list = self.gen_book.buy_book_info_list
        
        # 下单
        code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算总价
        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                self.total_price = self.total_price + book.price * num
        
        # 充值并支付
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        
        # 发货
        code = self.seller.ship_order(self.order_id)
        assert code == 200
        
        yield

    def test_receive_ok(self):
        """正常收货"""
        code = self.buyer.receive_order(self.order_id)
        assert code == 200

    def test_receive_non_exist_order(self):
        """收货不存在的订单"""
        code = self.buyer.receive_order(self.order_id + "_x")
        assert code != 200

    def test_receive_wrong_user(self):
        """非订单买家收货"""
        another_buyer = register_new_buyer("another_buyer_{}".format(str(uuid.uuid1())), self.password)
        code = another_buyer.receive_order(self.order_id)
        assert code != 200

    def test_receive_not_shipped(self):
        """订单未发货时收货"""
        # 创建一个新订单，只支付不发货
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算新订单的总价
        new_total_price = 0
        for item in self.gen_book.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                new_total_price = new_total_price + book.price * num
        
        code = self.buyer.add_funds(new_total_price)
        assert code == 200
        code = self.buyer.payment(order_id)
        assert code == 200
        
        # 尝试收货（未发货）
        code = self.buyer.receive_order(order_id)
        assert code != 200

    def test_receive_twice(self):
        """重复收货"""
        code = self.buyer.receive_order(self.order_id)
        assert code == 200
        
        # 再次收货
        code = self.buyer.receive_order(self.order_id)
        assert code != 200

    def test_receive_cancelled_order(self):
        """尝试收货已取消的订单"""
        # 创建新订单
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=3
        )
        assert ok
        
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 取消订单
        code = self.buyer.cancel_order(order_id)
        assert code == 200
        
        # 尝试收货（订单已取消）
        code = self.buyer.receive_order(order_id)
        assert code != 200
