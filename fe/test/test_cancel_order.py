import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
from fe.access.book import Book


class TestCancelOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_cancel_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_cancel_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_cancel_buyer_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 注册卖家和买家
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成图书数据，使用不同的seller_id避免冲突
        self.gen_book = GenBook(self.seller_id + "_gen", self.store_id)
        
        yield

    def test_cancel_pending_order(self):
        """取消待支付订单"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 取消订单
        code = self.buyer.cancel_order(order_id)
        assert code == 200

    def test_cancel_paid_order(self):
        """取消已支付订单（退款）"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        buy_book_info_list = self.gen_book.buy_book_info_list
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算总价
        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                total_price = total_price + book.price * num
        
        # 充值并支付
        code = self.buyer.add_funds(total_price)
        assert code == 200
        code = self.buyer.payment(order_id)
        assert code == 200
        
        # 取消订单
        code = self.buyer.cancel_order(order_id)
        assert code == 200

    def test_cancel_non_exist_order(self):
        """取消不存在的订单"""
        code = self.buyer.cancel_order("non_exist_order_id")
        assert code != 200

    def test_cancel_wrong_user(self):
        """非订单买家取消订单"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 另一个用户尝试取消
        another_buyer = register_new_buyer("another_buyer_{}".format(str(uuid.uuid1())), self.password)
        code = another_buyer.cancel_order(order_id)
        assert code != 200

    def test_cancel_shipped_order(self):
        """取消已发货订单（不允许）"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        buy_book_info_list = self.gen_book.buy_book_info_list
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算总价
        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                total_price = total_price + book.price * num
        
        # 充值并支付
        code = self.buyer.add_funds(total_price)
        assert code == 200
        code = self.buyer.payment(order_id)
        assert code == 200
        
        # 发货
        code = self.seller.ship_order(order_id)
        assert code == 200
        
        # 尝试取消订单（已发货，不允许）
        code = self.buyer.cancel_order(order_id)
        assert code != 200

    def test_cancel_twice(self):
        """重复取消订单"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 取消订单
        code = self.buyer.cancel_order(order_id)
        assert code == 200
        
        # 再次取消
        code = self.buyer.cancel_order(order_id)
        assert code != 200
