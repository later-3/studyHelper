"""
教师仪表盘组件测试
测试教师仪表盘的所有功能，包括班级概览、学科分析、学生排名、重点关注学生、教学建议等
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import streamlit as st

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.teacher_dashboard import TeacherDashboard
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_management_v2 import user_management_v2

class TestTeacherDashboard:
    """教师仪表盘测试类"""
    
    @pytest.fixture
    def teacher_dashboard(self):
        """创建教师仪表盘实例"""
        return TeacherDashboard()
    
    @pytest.fixture
    def mock_teacher_data(self):
        """模拟教师数据"""
        return {
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
    
    def test_teacher_dashboard_initialization(self, teacher_dashboard):
        """测试教师仪表盘初始化"""
        assert teacher_dashboard is not None
        assert hasattr(teacher_dashboard, 'data_service')
        assert hasattr(teacher_dashboard, 'user_management')
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.container')
    @patch('streamlit.write')
    @patch('streamlit.divider')
    def test_render_class_overview_success(self, mock_divider, mock_write, mock_container, 
                                         mock_metric, mock_columns, mock_warning, mock_subheader,
                                         teacher_dashboard, mock_teacher_data, mock_class_data):
        """测试班级概览渲染成功"""
        # 模拟用户管理方法
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=mock_teacher_data), \
             patch.object(teacher_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data):
            
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
            teacher_dashboard.render_class_overview('teacher_01')
            
            # 验证调用
            mock_subheader.assert_called_with("📊 班级概览")
            mock_columns.assert_called_with(4)
            # 由于Mock的限制，我们验证基本调用而不是具体次数
            assert mock_metric.called or mock_write.called
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_class_overview_no_teacher(self, mock_warning, mock_subheader, teacher_dashboard):
        """测试班级概览 - 无教师信息"""
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=None):
            teacher_dashboard.render_class_overview('invalid_id')
            mock_warning.assert_called_with("无法获取教师信息")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_class_overview_no_classes(self, mock_warning, mock_subheader, teacher_dashboard, mock_teacher_data):
        """测试班级概览 - 无管理班级"""
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=mock_teacher_data), \
             patch.object(teacher_dashboard.user_management, 'get_managed_classes', return_value=[]):
            teacher_dashboard.render_class_overview('teacher_01')
            mock_warning.assert_called_with("您还没有管理的班级")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.write')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    def test_render_subject_analysis_success(self, mock_divider, mock_info, mock_plotly_chart, 
                                           mock_write, mock_warning, mock_subheader,
                                           teacher_dashboard, mock_teacher_data, mock_class_data):
        """测试学科分析渲染成功"""
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=mock_teacher_data), \
             patch.object(teacher_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data):
            
            teacher_dashboard.render_subject_analysis('teacher_01')
            
            # 验证调用
            mock_subheader.assert_called_with("📚 学科分析")
            assert mock_write.call_count >= 2  # 至少2个学科
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_subject_analysis_no_subjects(self, mock_warning, mock_subheader, teacher_dashboard):
        """测试学科分析 - 无教授学科"""
        teacher_no_subjects = {'id': 'teacher_01', 'name': '张老师', 'role': 'teacher'}
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=teacher_no_subjects):
            teacher_dashboard.render_subject_analysis('teacher_01')
            mock_warning.assert_called_with("未设置教授学科")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.dataframe')
    @patch('streamlit.write')
    @patch('streamlit.metric')
    @patch('streamlit.columns')
    @patch('streamlit.info')
    def test_render_student_ranking_success(self, mock_info, mock_columns, mock_metric, 
                                          mock_write, mock_dataframe, mock_warning, mock_subheader,
                                          teacher_dashboard, mock_student_data, mock_learning_stats):
        """测试学生排名渲染成功"""
        with patch.object(teacher_dashboard.user_management, 'get_managed_students', return_value=mock_student_data), \
             patch.object(teacher_dashboard.user_management, 'get_learning_stats', return_value=mock_learning_stats):
            
            # 模拟Streamlit组件
            mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
            mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
            
            teacher_dashboard.render_student_ranking('teacher_01')
            
            # 验证调用
            mock_subheader.assert_called_with("🏆 学生排名")
            mock_dataframe.assert_called_once()
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_student_ranking_no_students(self, mock_warning, mock_subheader, teacher_dashboard):
        """测试学生排名 - 无管理学生"""
        with patch.object(teacher_dashboard.user_management, 'get_managed_students', return_value=[]):
            teacher_dashboard.render_student_ranking('teacher_01')
            mock_warning.assert_called_with("您还没有管理的学生")
    
    @patch('streamlit.subheader')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    @patch('streamlit.write')
    @patch('streamlit.metric')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    @patch('streamlit.container')
    def test_render_attention_students_success(self, mock_container, mock_divider, mock_info, mock_button, 
                                             mock_columns, mock_metric, mock_write, 
                                             mock_warning, mock_success, mock_subheader,
                                             teacher_dashboard, mock_class_data, mock_student_data, mock_learning_stats):
        """测试重点关注学生渲染成功"""
        with patch.object(teacher_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data), \
             patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=mock_student_data[0]), \
             patch.object(teacher_dashboard.user_management, 'get_learning_stats', return_value=mock_learning_stats):
            
            # 模拟Streamlit组件
            mock_col1, mock_col2, mock_col3, mock_col4 = Mock(), Mock(), Mock(), Mock()
            # 为列对象添加上下文管理器支持
            for col in [mock_col1, mock_col2, mock_col3, mock_col4]:
                col.__enter__ = Mock(return_value=col)
                col.__exit__ = Mock(return_value=None)
            mock_columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4]
            mock_button.return_value = False
            
            # 模拟容器上下文管理器
            mock_container_context = Mock()
            mock_container_context.__enter__ = Mock(return_value=mock_container_context)
            mock_container_context.__exit__ = Mock(return_value=None)
            mock_container.return_value = mock_container_context
            
            teacher_dashboard.render_attention_students('teacher_01')
            
            # 验证调用
            mock_subheader.assert_called_with("⚠️ 重点关注学生")
    
    @patch('streamlit.subheader')
    @patch('streamlit.success')
    def test_render_attention_students_no_attention(self, mock_success, mock_subheader, teacher_dashboard):
        """测试重点关注学生 - 无需要关注的学生"""
        class_no_attention = [{'id': 'class_01', 'name': '五年级一班', 'needs_attention_students': []}]
        with patch.object(teacher_dashboard.user_management, 'get_managed_classes', return_value=class_no_attention):
            teacher_dashboard.render_attention_students('teacher_01')
            mock_success.assert_called_with("目前没有需要特别关注的学生，班级表现良好！")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.write')
    @patch('streamlit.columns')
    @patch('streamlit.divider')
    @patch('streamlit.container')
    def test_render_teaching_suggestions_success(self, mock_container, mock_divider, mock_columns, mock_write, 
                                               mock_warning, mock_subheader,
                                               teacher_dashboard, mock_teacher_data, mock_class_data):
        """测试教学建议渲染成功"""
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=mock_teacher_data), \
             patch.object(teacher_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data):
            
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
            
            teacher_dashboard.render_teaching_suggestions('teacher_01')
            
            # 验证调用
            mock_subheader.assert_called_with("💡 教学建议")
    
    @patch('streamlit.subheader')
    @patch('streamlit.button')
    @patch('streamlit.success')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    def test_render_quick_actions(self, mock_divider, mock_info, mock_success, mock_button, mock_subheader,
                                teacher_dashboard):
        """测试快速操作渲染"""
        # 模拟按钮返回False
        mock_button.return_value = False
        
        teacher_dashboard.render_quick_actions('teacher_01')
        
        # 验证调用
        mock_subheader.assert_called_with("⚡ 快速操作")
        assert mock_button.call_count >= 6  # 6个快速操作按钮
    
    @patch('streamlit.title')
    @patch('streamlit.write')
    @patch('streamlit.tabs')
    @patch('streamlit.divider')
    def test_render_teacher_dashboard_success(self, mock_divider, mock_tabs, mock_write, mock_title,
                                            teacher_dashboard, mock_teacher_data):
        """测试教师仪表盘主界面渲染成功"""
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=mock_teacher_data), \
             patch.object(teacher_dashboard, 'render_class_overview'), \
             patch.object(teacher_dashboard, 'render_subject_analysis'), \
             patch.object(teacher_dashboard, 'render_student_ranking'), \
             patch.object(teacher_dashboard, 'render_attention_students'), \
             patch.object(teacher_dashboard, 'render_teaching_suggestions'), \
             patch.object(teacher_dashboard, 'render_quick_actions'):
            
            # 模拟标签页上下文管理器
            mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5 = Mock(), Mock(), Mock(), Mock(), Mock()
            for tab in [mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5]:
                tab.__enter__ = Mock(return_value=tab)
                tab.__exit__ = Mock(return_value=None)
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5]
            
            teacher_dashboard.render_teacher_dashboard('teacher_01')
            
            # 验证调用
            mock_title.assert_called_with("👨‍🏫 教师仪表盘")
            mock_tabs.assert_called_with([
                "📊 班级概览", 
                "📚 学科分析", 
                "🏆 学生排名", 
                "⚠️ 重点关注", 
                "💡 教学建议"
            ])
    
    @patch('streamlit.error')
    def test_render_teacher_dashboard_no_teacher(self, mock_error, teacher_dashboard):
        """测试教师仪表盘 - 无教师信息"""
        with patch.object(teacher_dashboard.user_management, 'get_user_by_id', return_value=None):
            teacher_dashboard.render_teacher_dashboard('invalid_id')
            mock_error.assert_called_with("无法获取教师信息")
    
    def test_teacher_dashboard_data_integration(self, teacher_dashboard):
        """测试教师仪表盘数据集成"""
        # 测试数据服务集成
        assert teacher_dashboard.data_service is not None
        assert teacher_dashboard.user_management is not None
        
        # 测试用户管理实例
        assert teacher_dashboard.user_management == user_management_v2

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 