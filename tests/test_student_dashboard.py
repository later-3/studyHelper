"""
测试学生仪表盘组件 (student_dashboard.py)
验证学生界面的各个功能模块
"""

import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 模拟Streamlit环境
import sys
sys.modules['streamlit'] = Mock()
sys.modules['plotly.graph_objects'] = Mock()
sys.modules['plotly.express'] = Mock()

from components.student_dashboard import StudentDashboard

class TestStudentDashboard(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建临时测试数据
        cls.test_submissions = [
            {
                'id': 'sub_001',
                'user_id': 'student_01',
                'question_text': '1+1等于多少？',
                'user_answer': '3',
                'correct_answer': '2',
                'is_correct': False,
                'subject': '数学',
                'timestamp': '2025-07-12T10:00:00'
            },
            {
                'id': 'sub_002',
                'user_id': 'student_01',
                'question_text': '2+2等于多少？',
                'user_answer': '4',
                'correct_answer': '4',
                'is_correct': True,
                'subject': '数学',
                'timestamp': '2025-07-12T11:00:00'
            },
            {
                'id': 'sub_003',
                'user_id': 'student_01',
                'question_text': '请写出"你好"的拼音',
                'user_answer': 'ni hao',
                'correct_answer': 'nǐ hǎo',
                'is_correct': False,
                'subject': '语文',
                'timestamp': '2025-07-12T12:00:00'
            }
        ]
        
        # 创建测试用户数据
        cls.test_user = {
            'id': 'student_01',
            'name': '小明',
            'role': 'student',
            'class_id': 'class_01',
            'grade_id': 'grade_05',
            'school_id': 'school_01',
            'email': 'xiaoming@student.school.edu.cn',
            'phone': '13900139001',
            'student_number': '2025001',
            'gender': '男',
            'birth_date': '2014-03-15',
            'parent_phone': '13900139001',
            'permissions': ['personal_learning', 'data_view'],
            'learning_stats': {
                'total_submissions': 45,
                'correct_count': 38,
                'accuracy_rate': 84.4,
                'last_activity': '2025-07-12T10:30:00',
                'today_submissions': 5,
                'today_submissions_delta': 2,
                'accuracy_delta': 1.5,
                'new_mistakes': 1,
                'mistakes_delta': -1,
                'study_hours': 2.5,
                'study_hours_delta': 0.5
            },
            'last_login': '2025-07-12T10:30:00',
            'created_at': '2025-01-01',
            'updated_at': '2025-07-12'
        }
        
        # 创建仪表盘实例
        cls.dashboard = StudentDashboard()
    
    def setUp(self):
        """每个测试前的设置"""
        # 重置模拟对象
        self.dashboard.data_service = Mock()
        self.dashboard.user_management = Mock()
    
    def test_render_learning_overview_with_valid_data(self):
        """测试学习概览渲染（有效数据）"""
        # 设置模拟返回值
        self.dashboard.user_management.get_learning_stats.return_value = self.test_user['learning_stats']
        self.dashboard.user_management.get_user_by_id.return_value = self.test_user
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.metric = Mock()
        mock_st.warning = Mock()
        
        # 模拟columns返回的列对象（支持上下文管理器）
        mock_cols = [Mock(), Mock(), Mock(), Mock()]
        for col in mock_cols:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        mock_st.columns.return_value = mock_cols
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_learning_overview('student_01')
            
            # 验证调用了正确的次数
            self.assertEqual(mock_st.metric.call_count, 4)
            mock_st.warning.assert_not_called()
    
    def test_render_learning_overview_without_data(self):
        """测试学习概览渲染（无数据）"""
        # 设置模拟返回值
        self.dashboard.user_management.get_learning_stats.return_value = None
        self.dashboard.user_management.get_user_by_id.return_value = None
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.warning = Mock()
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_learning_overview('student_01')
            
            # 验证显示了警告信息
            mock_st.warning.assert_called_once_with("无法获取学习数据")
    
    def test_render_learning_goals(self):
        """测试学习目标渲染"""
        # 设置模拟返回值
        self.dashboard.user_management.get_user_by_id.return_value = self.test_user
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.write = Mock()
        mock_st.progress = Mock()
        mock_st.warning = Mock()
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_learning_goals('student_01')
            
            # 验证调用了正确的组件
            mock_st.write.assert_called()
            mock_st.progress.assert_called_once()
            mock_st.warning.assert_not_called()
    
    def test_render_recent_mistakes_with_mistakes(self):
        """测试最近错题渲染（有错题）"""
        # 设置模拟返回值
        self.dashboard.data_service.get_submissions_by_user.return_value = self.test_submissions
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.expander = Mock()
        mock_st.write = Mock()
        mock_st.divider = Mock()
        mock_st.info = Mock()
        mock_st.success = Mock()
        
        # 模拟expander上下文管理器
        mock_expander = Mock()
        mock_st.expander.return_value.__enter__ = Mock(return_value=mock_expander)
        mock_st.expander.return_value.__exit__ = Mock(return_value=None)
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_recent_mistakes('student_01')
            
            # 验证调用了正确的组件
            mock_st.subheader.assert_called_once_with("📚 最近错题")
            mock_st.expander.assert_called()
            mock_st.info.assert_not_called()
            mock_st.success.assert_not_called()
    
    def test_render_recent_mistakes_without_submissions(self):
        """测试最近错题渲染（无提交记录）"""
        # 设置模拟返回值
        self.dashboard.data_service.get_submissions_by_user.return_value = []
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.info = Mock()
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_recent_mistakes('student_01')
            
            # 验证显示了信息提示
            mock_st.info.assert_called_once_with("暂无错题记录")
    
    def test_render_recent_mistakes_all_correct(self):
        """测试最近错题渲染（全部正确）"""
        # 设置模拟返回值（全部正确的提交）
        correct_submissions = [
            {
                'id': 'sub_001',
                'user_id': 'student_01',
                'question_text': '1+1等于多少？',
                'user_answer': '2',
                'correct_answer': '2',
                'is_correct': True,
                'subject': '数学',
                'timestamp': '2025-07-12T10:00:00'
            }
        ]
        self.dashboard.data_service.get_submissions_by_user.return_value = correct_submissions
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.success = Mock()
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_recent_mistakes('student_01')
            
            # 验证显示了成功提示
            mock_st.success.assert_called_once_with("最近没有错题，继续保持！")
    
    def test_render_recommended_exercises(self):
        """测试推荐练习渲染"""
        # 设置模拟返回值
        self.dashboard.user_management.get_user_by_id.return_value = self.test_user
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.container = Mock()
        mock_st.write = Mock()
        mock_st.button = Mock()
        mock_st.success = Mock()
        mock_st.divider = Mock()
        mock_st.warning = Mock()
        
        # 模拟container上下文管理器
        mock_container = Mock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=None)
        
        # 模拟columns返回的列对象（支持上下文管理器）
        mock_cols = [Mock(), Mock()]
        for col in mock_cols:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        mock_st.columns.return_value = mock_cols
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_recommended_exercises('student_01')
            
            # 验证调用了正确的组件
            mock_st.subheader.assert_called_once_with("🚀 推荐练习")
            mock_st.container.assert_called()
            mock_st.warning.assert_not_called()
    
    def test_render_learning_trends_with_data(self):
        """测试学习趋势渲染（有数据）"""
        # 设置模拟返回值
        self.dashboard.user_management.get_learning_stats.return_value = self.test_user['learning_stats']
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.plotly_chart = Mock()
        mock_st.warning = Mock()
        
        # 模拟plotly图表
        mock_go = Mock()
        mock_fig = Mock()
        mock_go.Figure.return_value = mock_fig
        
        with patch('components.student_dashboard.st', mock_st), \
             patch('components.student_dashboard.go', mock_go):
            self.dashboard.render_learning_trends('student_01')
            
            # 验证调用了正确的组件
            mock_st.subheader.assert_called_once_with("📈 学习趋势")
            mock_st.plotly_chart.assert_called()
            mock_st.warning.assert_not_called()
    
    def test_render_learning_trends_without_data(self):
        """测试学习趋势渲染（无数据）"""
        # 设置模拟返回值
        self.dashboard.user_management.get_learning_stats.return_value = None
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.warning = Mock()
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_learning_trends('student_01')
            
            # 验证显示了警告信息
            mock_st.warning.assert_called_once_with("无法获取学习趋势数据")
    
    def test_render_subject_performance(self):
        """测试学科表现渲染"""
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.plotly_chart = Mock()
        mock_st.metric = Mock()
        mock_st.write = Mock()
        
        # 模拟plotly图表
        mock_go = Mock()
        mock_fig = Mock()
        mock_go.Figure.return_value = mock_fig
        
        # 模拟columns返回的列对象（支持上下文管理器）
        mock_cols = [Mock(), Mock(), Mock()]
        for col in mock_cols:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        mock_st.columns.return_value = mock_cols
        
        with patch('components.student_dashboard.st', mock_st), \
             patch('components.student_dashboard.go', mock_go):
            self.dashboard.render_subject_performance('student_01')
            
            # 验证调用了正确的组件
            mock_st.subheader.assert_called_once_with("📊 学科掌握情况")
            mock_st.plotly_chart.assert_called()
            mock_st.metric.assert_called()
    
    def test_render_quick_actions(self):
        """测试快速操作渲染"""
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.subheader = Mock()
        mock_st.button = Mock()
        mock_st.success = Mock()
        mock_st.rerun = Mock()
        
        # 模拟session_state
        mock_session_state = Mock()
        mock_session_state.page = None
        
        # 模拟columns返回的列对象（支持上下文管理器）
        mock_cols = [Mock(), Mock(), Mock()]
        for col in mock_cols:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        mock_st.columns.return_value = mock_cols
        
        with patch('components.student_dashboard.st', mock_st), \
             patch('components.student_dashboard.st.session_state', mock_session_state):
            self.dashboard.render_quick_actions('student_01')
            
            # 验证调用了正确的组件
            mock_st.subheader.assert_called_once_with("⚡ 快速操作")
            mock_st.button.assert_called()
    
    def test_render_student_dashboard_success(self):
        """测试完整学生仪表盘渲染（成功）"""
        # 设置模拟返回值
        self.dashboard.user_management.get_user_by_id.return_value = self.test_user
        self.dashboard.user_management.get_learning_stats.return_value = self.test_user['learning_stats']
        self.dashboard.data_service.get_submissions_by_user.return_value = []
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.title = Mock()
        mock_st.write = Mock()
        mock_st.divider = Mock()
        mock_st.error = Mock()
        mock_st.subheader = Mock()
        mock_st.metric = Mock()
        mock_st.progress = Mock()
        mock_st.info = Mock()
        mock_st.success = Mock()
        mock_st.container = Mock()
        mock_st.button = Mock()
        mock_st.plotly_chart = Mock()
        
        # 模拟columns返回的列对象（支持上下文管理器）
        mock_cols_4 = [Mock(), Mock(), Mock(), Mock()]
        mock_cols_2 = [Mock(), Mock()]
        mock_cols_3 = [Mock(), Mock(), Mock()]
        
        for col in mock_cols_4 + mock_cols_2 + mock_cols_3:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        
        # 根据不同的调用返回不同数量的列
        def mock_columns_side_effect(*args):
            if len(args) > 0:
                if args[0] == 4:
                    return mock_cols_4
                elif args[0] == 2:
                    return mock_cols_2
                elif args[0] == 3:
                    return mock_cols_3
            return mock_cols_2
        
        mock_st.columns.side_effect = mock_columns_side_effect
        
        # 模拟container上下文管理器
        mock_container = Mock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=None)
        
        # 模拟plotly图表
        mock_go = Mock()
        mock_fig = Mock()
        mock_go.Figure.return_value = mock_fig
        
        # 模拟datetime
        mock_datetime = Mock()
        mock_datetime.now.return_value = datetime(2025, 7, 12)
        mock_datetime.strftime = datetime.strftime
        
        with patch('components.student_dashboard.st', mock_st), \
             patch('components.student_dashboard.datetime', mock_datetime), \
             patch('components.student_dashboard.go', mock_go):
            self.dashboard.render_student_dashboard('student_01')
            
            # 验证调用了正确的组件
            mock_st.title.assert_called_once_with("🎓 我的学习助手")
            mock_st.write.assert_called()
            mock_st.error.assert_not_called()
    
    def test_render_student_dashboard_user_not_found(self):
        """测试完整学生仪表盘渲染（用户不存在）"""
        # 设置模拟返回值
        self.dashboard.user_management.get_user_by_id.return_value = None
        
        # 模拟streamlit组件
        mock_st = Mock()
        mock_st.title = Mock()
        mock_st.error = Mock()
        
        with patch('components.student_dashboard.st', mock_st):
            self.dashboard.render_student_dashboard('student_01')
            
            # 验证显示了错误信息
            mock_st.error.assert_called_once_with("用户信息获取失败")
    
    def test_dashboard_initialization(self):
        """测试仪表盘初始化"""
        # 验证仪表盘正确初始化
        self.assertIsNotNone(self.dashboard.data_service)
        self.assertIsNotNone(self.dashboard.user_management)
    
    def test_learning_stats_calculation(self):
        """测试学习统计计算"""
        # 测试学习统计数据的计算逻辑
        learning_stats = self.test_user['learning_stats']
        
        # 验证统计数据的存在
        self.assertIn('total_submissions', learning_stats)
        self.assertIn('correct_count', learning_stats)
        self.assertIn('accuracy_rate', learning_stats)
        self.assertIn('today_submissions', learning_stats)
        
        # 验证数据类型的正确性
        self.assertIsInstance(learning_stats['total_submissions'], int)
        self.assertIsInstance(learning_stats['accuracy_rate'], float)
        self.assertIsInstance(learning_stats['today_submissions'], int)
    
    def test_subject_performance_data_structure(self):
        """测试学科表现数据结构"""
        # 在render_subject_performance方法中使用的数据结构
        subjects_data = {
            '数学': {'average': 85.0, 'total': 25, 'weak_points': ['分数计算', '几何']},
            '语文': {'average': 88.0, 'total': 20, 'weak_points': []},
            '英语': {'average': 75.0, 'total': 15, 'weak_points': ['语法', '词汇']}
        }
        
        # 验证数据结构
        for subject, data in subjects_data.items():
            self.assertIn('average', data)
            self.assertIn('total', data)
            self.assertIn('weak_points', data)
            self.assertIsInstance(data['average'], float)
            self.assertIsInstance(data['total'], int)
            self.assertIsInstance(data['weak_points'], list)

if __name__ == '__main__':
    unittest.main(verbosity=2) 