"""
测试be/app.py的入口文件
用于提高代码覆盖率
"""
import pytest
import subprocess
import time
import signal
import os


class TestAppEntry:
    """测试应用入口"""
    
    def test_app_import(self):
        """测试导入be.app模块"""
        # 导入模块应该不会抛出异常
        try:
            from be import app
            assert app is not None
        except Exception as e:
            pytest.fail(f"Failed to import be.app: {e}")
    
    def test_serve_module_exists(self):
        """测试serve模块存在"""
        from be import serve
        assert hasattr(serve, 'be_run')
