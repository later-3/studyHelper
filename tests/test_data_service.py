#!/usr/bin/env python3
"""
测试数据服务功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_service import DataService

def test_data_service():
    """测试数据服务的基本功能"""
    print("开始测试数据服务...")
    
    try:
        # 创建数据服务实例
        data_service = DataService()
        print("✓ DataService实例创建成功")
        
        # 检查方法是否存在
        if hasattr(data_service, 'get_submissions_by_user'):
            print("✓ get_submissions_by_user方法存在")
            
            # 测试方法调用
            try:
                submissions = data_service.get_submissions_by_user("test_user")
                print(f"✓ get_submissions_by_user调用成功，返回 {len(submissions)} 条记录")
            except Exception as e:
                print(f"✗ get_submissions_by_user调用失败: {e}")
        else:
            print("✗ get_submissions_by_user方法不存在")
            print(f"可用方法: {[method for method in dir(data_service) if not method.startswith('_')]}")
        
        # 检查其他重要方法
        important_methods = [
            'get_user_submissions',
            'get_submissions_by_question',
            'group_submissions_by_question',
            'get_submission_stats'
        ]
        
        for method in important_methods:
            if hasattr(data_service, method):
                print(f"✓ {method}方法存在")
            else:
                print(f"✗ {method}方法不存在")
        
        print("\n测试完成！")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_service() 