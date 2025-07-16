"""
测试页面管理器功能
验证页面注册、权限控制和路由功能
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模拟streamlit环境
sys.modules['streamlit'] = Mock()

from components.page_manager import PageManager, PageConfig, UserRole

class TestPageManager(unittest.TestCase):
    """页面管理器测试类""