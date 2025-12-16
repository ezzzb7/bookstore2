import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
from be.model.buyer import Buyer as BuyerModel
import time


class TestTimeoutOrder:
    """测试自动取消超时订单功能"""
    
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_timeout_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_timeout_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_timeout_buyer_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 注册卖家和买家
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成图书数据，使用不同的seller_id避免冲突
        self.gen_book = GenBook(self.seller_id + "_gen", self.store_id)
        
        # 创建后端买家模型实例用于调用check_and_cancel_timeout_orders
        self.buyer_model = BuyerModel()
        
        yield

    def test_check_timeout_orders(self):
        """测试检查超时订单功能（不实际等待30分钟）"""
        # 这个测试只是验证函数可以正常运行，不测试实际超时逻辑
        # 因为实际超时需要等待30分钟，不适合在单元测试中进行
        
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        
        # 下单但不支付
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 调用检查超时订单的函数
        code, message = self.buyer_model.check_and_cancel_timeout_orders()
        assert code == 200
        
        # 订单应该还存在（因为没有超过30分钟）
        code, orders = self.buyer.query_order(order_id)
        assert code == 200
        assert len(orders) == 1
        # 订单状态应该还是pending
        assert orders[0]["status"] == "pending"

    def test_no_timeout_orders(self):
        """测试没有超时订单的情况"""
        # 不创建任何订单，直接调用检查函数
        code, message = self.buyer_model.check_and_cancel_timeout_orders()
        assert code == 200
        
    def test_timeout_with_paid_order(self):
        """测试已支付订单不会被超时取消"""
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        buy_book_info_list = self.gen_book.buy_book_info_list
        
        # 下单
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算总价并充值
        total_price = 0
        for item in buy_book_info_list:
            from fe.access.book import Book
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            total_price = total_price + book.price * num
        
        code = self.buyer.add_funds(total_price)
        assert code == 200
        
        # 支付
        code = self.buyer.payment(order_id)
        assert code == 200
        
        # 调用检查超时订单
        code, message = self.buyer_model.check_and_cancel_timeout_orders()
        assert code == 200
        
        # 已支付订单不应该被取消
        code, orders = self.buyer.query_order(order_id)
        assert code == 200
        assert len(orders) == 1
        assert orders[0]["status"] == "paid"
