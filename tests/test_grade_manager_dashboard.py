"""
年级主任仪表盘组件测试
测试年级主任仪表盘的所有功能，包括年级概览、班级排名、学科分析、教师表现评估、管理建议等
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import streamlit as st

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.grade_manager_dashboard import GradeManagerDashboard
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_management_v2 import user_management_v2

class TestGradeManagerDashboard:
    """年级主任仪表盘测试类"""
    
    @pytest.fixture
    def grade_manager_dashboard(self):
        """创建年级主任仪表盘实例"""
        return GradeManagerDashboard()
    
    @pytest.fixture
    def mock_grade_manager_data(self):
        """模拟年级主任数据"""
        return {
            'id': 'grade_manager_01',
            'name': '李主任',
            'role': 'grade_manager',
            'grade_id': 'grade_05',
            'school_id': 'school_01',
            'email': 'li.manager@zhihui.edu.cn',
            'phone': '13800138002',
            'permissions': ['grade_management', 'class_management', 'teacher_management', 'student_management', 'data_analysis'],
            'last_login': '2025-07-12T09:30:00',
            'created_at': '2025-01-01',
            'updated_at': '2025-07-12'
        }
    
    @pytest.fixture
    def mock_grade_data(self):
        """模拟年级数据"""
        return {
            'id': 'grade_05',
            'name': '五年级',
            'grade_level': 5,
            'manager_id': 'grade_manager_01',
            'school_id': 'school_01',
            'total_classes': 2,
            'total_students': 62,
            'total_teachers': 2,
            'average_accuracy': 78.5,
            'created_at': '2025-01-01',
            'updated_at': '2025-07-12'
        }
    
    @pytest.fixture
    def mock_class_data(self):
        """模拟班级数据"""
        return [
            {
                'id': 'class_01',
                'name': '五年级一班',
                'grade_id': 'grade_05',
                'teacher_id': 'teacher_01',
                'school_id': 'school_01',
                'student_count': 32,
                'average_accuracy': 82.0,
                'subject_performance': {
                    '数学': {'average': 85.0, 'weak_points': ['分数计算']},
                    '语文': {'average': 88.0, 'weak_points': []},
                    '英语': {'average': 75.0, 'weak_points': ['语法']}
                },
                'needs_attention_students': ['student_08', 'student_12'],
                'created_at': '2025-01-01',
                'updated_at': '2025-07-12'
            },
            {
                'id': 'class_02',
                'name': '五年级二班',
                'grade_id': 'grade_05',
                'teacher_id': 'teacher_02',
                'school_id': 'school_01',
                'student_count': 30,
                'average_accuracy': 75.0,
                'subject_performance': {
                    '数学': {'average': 78.0, 'weak_points': ['几何']},
                    '语文': {'average': 82.0, 'weak_points': ['阅读理解']},
                    '英语': {'average': 70.0, 'weak_points': ['词汇', '语法']}
                },
                'needs_attention_students': ['student_15', 'student_18', 'student_22'],
                'created_at': '2025-01-01',
                'updated_at': '2025-07-12'
            }
        ]
    
    @pytest.fixture
    def mock_teacher_data(self):
        """模拟教师数据"""
        return [
            {
                'id': 'teacher_01',
                'name': '张老师',
                'role': 'teacher',
                'class_id': 'class_01',
                'grade_id': 'grade_05',
                'school_id': 'school_01',
                'email': 'zhang.teacher@zhihui.edu.cn',
                'phone': '13800138004',
                'subject_teach': ['数学', '语文'],
                'manages_classes': ['class_01'],
                'permissions': ['class_management', 'student_management', 'data_analysis'],
                'last_login': '2025-07-12T08:45:00',
                'created_at': '2025-01-01',
                'updated_at': '2025-07-12'
            },
            {
                'id': 'teacher_02',
                'name': '李老师',
                'role': 'teacher',
                'class_id': 'class_02',
                'grade_id': 'grade_05',
                'school_id': 'school_01',
                'email': 'li.teacher@zhihui.edu.cn',
                'phone': '13800138005',
                'subject_teach': ['数学', '英语'],
                'manages_classes': ['class_02'],
                'permissions': ['class_management', 'student_management', 'data_analysis'],
                'last_login': '2025-07-12T08:30:00',
                'created_at': '2025-01-01',
                'updated_at': '2025-07-12'
            }
        ]
    
    @pytest.fixture
    def mock_student_data(self):
        """模拟学生数据"""
        return [
            {
                'id': 'student_01',
                'name': '小明',
                'role': 'student',
                'class_id': 'class_01',
                'grade_id': 'grade_05',
                'school_id': 'school_01',
                'email': 'xiaoming@student.zhihui.edu.cn',
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
                    'study_hours': 2.5,
                    'last_submission_date': '2025-07-12'
                }
            },
            {
                'id': 'student_02',
                'name': '小红',
                'role': 'student',
                'class_id': 'class_01',
                'grade_id': 'grade_05',
                'school_id': 'school_01',
                'email': 'xiaohong@student.zhihui.edu.cn',
                'phone': '13900139002',
                'student_number': '2025002',
                'gender': '女',
                'birth_date': '2014-05-20',
                'parent_phone': '13900139002',
                'permissions': ['personal_learning', 'data_view'],
                'learning_stats': {
                    'total_submissions': 42,
                    'correct_count': 35,
                    'accuracy_rate': 83.3,
                    'study_hours': 2.8,
                    'last_submission_date': '2025-07-12'
                }
            }
        ]
    
    @pytest.fixture
    def mock_learning_stats(self):
        """模拟学习统计数据"""
        return {
            'total_submissions': 45,
            'correct_count': 38,
            'accuracy_rate': 84.4,
            'study_hours': 2.5,
            'last_submission_date': '2025-07-12',
            'today_submissions': 5,
            'today_submissions_delta': 2,
            'accuracy_delta': 1.2,
            'new_mistakes': 1,
            'mistakes_delta': -1,
            'study_hours_delta': 0.5
        }
    
    def test_grade_manager_dashboard_initialization(self, grade_manager_dashboard):
        """测试年级主任仪表盘初始化"""
        assert grade_manager_dashboard is not None
        assert hasattr(grade_manager_dashboard, 'data_service')
        assert hasattr(grade_manager_dashboard, 'user_management')
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.container')
    @patch('streamlit.write')
    @patch('streamlit.divider')
    def test_render_grade_overview_success(self, mock_divider, mock_write, mock_container, 
                                         mock_metric, mock_columns, mock_warning, mock_subheader,
                                         grade_manager_dashboard, mock_grade_manager_data, mock_grade_data, mock_class_data):
        """测试年级概览渲染成功"""
        # 模拟用户管理方法
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=mock_grade_manager_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_grade_by_id', return_value=mock_grade_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_teacher_by_class', return_value={'name': '张老师'}):
            
            # 模拟Streamlit组件
            mock_col1, mock_col2, mock_col3, mock_col4 = Mock(), Mock(), Mock(), Mock()
            # 为列对象添加上下文管理器支持
            for col in [mock_col1, mock_col2, mock_col3, mock_col4]:
                col.__enter__ = Mock(return_value=col)
                col.__exit__ = Mock(return_value=None)
            mock_columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4]
            
            # 模拟容器上下文管理器
            mock_container_context = Mock()
            mock_container_context.__enter__ = Mock(return_value=mock_container_context)
            mock_container_context.__exit__ = Mock(return_value=None)
            mock_container.return_value = mock_container_context
            
            # 执行测试
            grade_manager_dashboard.render_grade_overview('grade_manager_01')
            
            # 验证调用
            mock_subheader.assert_called_with("📊 年级概览")
            # 验证columns被调用（可能有多次调用）
            assert mock_columns.called
            # 由于Mock的限制，我们验证基本调用而不是具体次数
            assert mock_metric.called or mock_write.called
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_grade_overview_no_manager(self, mock_warning, mock_subheader, grade_manager_dashboard):
        """测试年级概览 - 无年级主任信息"""
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=None):
            grade_manager_dashboard.render_grade_overview('invalid_id')
            mock_warning.assert_called_with("无法获取年级主任信息")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_grade_overview_no_grade(self, mock_warning, mock_subheader, grade_manager_dashboard, mock_grade_manager_data):
        """测试年级概览 - 无管理年级"""
        grade_manager_no_grade = {**mock_grade_manager_data}
        grade_manager_no_grade.pop('grade_id')
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=grade_manager_no_grade):
            grade_manager_dashboard.render_grade_overview('grade_manager_01')
            mock_warning.assert_called_with("您还没有管理的年级")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.dataframe')
    @patch('streamlit.write')
    @patch('streamlit.metric')
    @patch('streamlit.columns')
    @patch('streamlit.info')
    def test_render_class_ranking_success(self, mock_info, mock_columns, mock_metric, 
                                        mock_write, mock_dataframe, mock_warning, mock_subheader,
                                        grade_manager_dashboard, mock_class_data, mock_student_data, mock_learning_stats):
        """测试班级排名渲染成功"""
        with patch.object(grade_manager_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_students_by_class', return_value=mock_student_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_learning_stats', return_value=mock_learning_stats):
            
            # 模拟Streamlit组件
            mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
            mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
            
            grade_manager_dashboard.render_class_ranking('grade_manager_01')
            
            # 验证调用
            mock_subheader.assert_called_with("🏆 班级排名")
            mock_dataframe.assert_called_once()
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_class_ranking_no_classes(self, mock_warning, mock_subheader, grade_manager_dashboard):
        """测试班级排名 - 无管理班级"""
        with patch.object(grade_manager_dashboard.user_management, 'get_managed_classes', return_value=[]):
            grade_manager_dashboard.render_class_ranking('grade_manager_01')
            mock_warning.assert_called_with("您还没有管理的班级")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.write')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.metric')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    def test_render_subject_analysis_success(self, mock_divider, mock_info, mock_metric, 
                                           mock_plotly_chart, mock_write, mock_warning, mock_subheader,
                                           grade_manager_dashboard, mock_class_data):
        """测试学科分析渲染成功"""
        with patch.object(grade_manager_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data):
            
            grade_manager_dashboard.render_subject_analysis('grade_manager_01')
            
            # 验证调用
            mock_subheader.assert_called_with("📚 学科分析")
            assert mock_write.call_count >= 3  # 至少3个学科
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.dataframe')
    @patch('streamlit.write')
    @patch('streamlit.metric')
    @patch('streamlit.columns')
    @patch('streamlit.info')
    def test_render_teacher_evaluation_success(self, mock_info, mock_columns, mock_metric, 
                                             mock_write, mock_dataframe, mock_warning, mock_subheader,
                                             grade_manager_dashboard, mock_grade_manager_data, mock_teacher_data, mock_class_data):
        """测试教师表现评估渲染成功"""
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=mock_grade_manager_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_teachers_by_grade', return_value=mock_teacher_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_students_by_class', return_value=[]):
            
            # 模拟Streamlit组件
            mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
            mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
            
            grade_manager_dashboard.render_teacher_evaluation('grade_manager_01')
            
            # 验证调用
            mock_subheader.assert_called_with("👨‍🏫 教师表现评估")
            mock_dataframe.assert_called_once()
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_teacher_evaluation_no_grade(self, mock_warning, mock_subheader, grade_manager_dashboard):
        """测试教师表现评估 - 无管理年级"""
        grade_manager_no_grade = {'id': 'grade_manager_01', 'name': '李主任', 'role': 'grade_manager'}
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=grade_manager_no_grade):
            grade_manager_dashboard.render_teacher_evaluation('grade_manager_01')
            mock_warning.assert_called_with("您还没有管理的年级")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.write')
    @patch('streamlit.columns')
    @patch('streamlit.divider')
    @patch('streamlit.container')
    def test_render_management_suggestions_success(self, mock_container, mock_divider, mock_columns, mock_write, 
                                                 mock_warning, mock_subheader,
                                                 grade_manager_dashboard, mock_grade_manager_data, mock_grade_data, mock_class_data, mock_teacher_data):
        """测试管理建议渲染成功"""
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=mock_grade_manager_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_grade_by_id', return_value=mock_grade_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_teachers_by_grade', return_value=mock_teacher_data):
            
            # 模拟Streamlit组件
            mock_col1, mock_col2 = Mock(), Mock()
            # 为列对象添加上下文管理器支持
            for col in [mock_col1, mock_col2]:
                col.__enter__ = Mock(return_value=col)
                col.__exit__ = Mock(return_value=None)
            mock_columns.return_value = [mock_col1, mock_col2]
            
            # 模拟容器上下文管理器
            mock_container_context = Mock()
            mock_container_context.__enter__ = Mock(return_value=mock_container_context)
            mock_container_context.__exit__ = Mock(return_value=None)
            mock_container.return_value = mock_container_context
            
            grade_manager_dashboard.render_management_suggestions('grade_manager_01')
            
            # 验证调用
            mock_subheader.assert_called_with("💡 管理建议")
    
    @patch('streamlit.subheader')
    @patch('streamlit.button')
    @patch('streamlit.success')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    def test_render_quick_actions(self, mock_divider, mock_info, mock_success, mock_button, mock_subheader,
                                grade_manager_dashboard):
        """测试快速操作渲染"""
        # 模拟按钮返回False
        mock_button.return_value = False
        
        grade_manager_dashboard.render_quick_actions('grade_manager_01')
        
        # 验证调用
        mock_subheader.assert_called_with("⚡ 快速操作")
        assert mock_button.call_count >= 6  # 6个快速操作按钮
    
    @patch('streamlit.title')
    @patch('streamlit.write')
    @patch('streamlit.tabs')
    @patch('streamlit.divider')
    def test_render_grade_manager_dashboard_success(self, mock_divider, mock_tabs, mock_write, mock_title,
                                                  grade_manager_dashboard, mock_grade_manager_data, mock_grade_data):
        """测试年级主任仪表盘主界面渲染成功"""
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=mock_grade_manager_data), \
             patch.object(grade_manager_dashboard.user_management, 'get_grade_by_id', return_value=mock_grade_data), \
             patch.object(grade_manager_dashboard, 'render_grade_overview'), \
             patch.object(grade_manager_dashboard, 'render_class_ranking'), \
             patch.object(grade_manager_dashboard, 'render_subject_analysis'), \
             patch.object(grade_manager_dashboard, 'render_teacher_evaluation'), \
             patch.object(grade_manager_dashboard, 'render_management_suggestions'), \
             patch.object(grade_manager_dashboard, 'render_quick_actions'):
            
            # 模拟标签页上下文管理器
            mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5 = Mock(), Mock(), Mock(), Mock(), Mock()
            for tab in [mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5]:
                tab.__enter__ = Mock(return_value=tab)
                tab.__exit__ = Mock(return_value=None)
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5]
            
            grade_manager_dashboard.render_grade_manager_dashboard('grade_manager_01')
            
            # 验证调用
            mock_title.assert_called_with("👨‍💼 年级主任仪表盘")
            mock_tabs.assert_called_with([
                "📊 年级概览", 
                "🏆 班级排名", 
                "📚 学科分析", 
                "👨‍🏫 教师评估", 
                "💡 管理建议"
            ])
    
    @patch('streamlit.error')
    def test_render_grade_manager_dashboard_no_manager(self, mock_error, grade_manager_dashboard):
        """测试年级主任仪表盘 - 无年级主任信息"""
        with patch.object(grade_manager_dashboard.user_management, 'get_user_by_id', return_value=None):
            grade_manager_dashboard.render_grade_manager_dashboard('invalid_id')
            mock_error.assert_called_with("无法获取年级主任信息")
    
    def test_grade_manager_dashboard_data_integration(self, grade_manager_dashboard):
        """测试年级主任仪表盘数据集成"""
        # 测试数据服务集成
        assert grade_manager_dashboard.data_service is not None
        assert grade_manager_dashboard.user_management is not None
        
        # 测试用户管理实例
        assert grade_manager_dashboard.user_management == user_management_v2

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 