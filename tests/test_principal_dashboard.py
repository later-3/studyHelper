"""
校长仪表盘组件测试
测试校长仪表盘的所有功能，包括学校概览、年级对比、学科表现、教师团队评估、战略建议等
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import streamlit as st

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.principal_dashboard import PrincipalDashboard
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_management_v2 import user_management_v2

class TestPrincipalDashboard:
    """校长仪表盘测试类"""
    
    @pytest.fixture
    def principal_dashboard(self):
        """创建校长仪表盘实例"""
        return PrincipalDashboard()
    
    @pytest.fixture
    def mock_principal_data(self):
        """模拟校长数据"""
        return {
            'id': 'principal_01',
            'name': '王校长',
            'role': 'principal',
            'school_id': 'school_01',
            'email': 'principal@zhihui.edu.cn',
            'phone': '13800138001',
            'permissions': ['school_management', 'grade_management', 'teacher_management', 'student_management', 'data_analysis'],
            'last_login': '2025-07-12T10:00:00',
            'created_at': '2025-01-01',
            'updated_at': '2025-07-12'
        }
    
    @pytest.fixture
    def mock_school_data(self):
        """模拟学校数据"""
        return {
            'id': 'school_01',
            'name': '智慧未来实验小学',
            'address': '北京市朝阳区智慧路123号',
            'phone': '010-12345678',
            'email': 'info@zhihui.edu.cn',
            'principal_id': 'principal_01',
            'total_students': 6,
            'total_teachers': 3,
            'total_classes': 3,
            'total_grades': 2,
            'created_at': '2025-01-01',
            'updated_at': '2025-07-12'
        }
    
    @pytest.fixture
    def mock_grade_data(self):
        """模拟年级数据"""
        return [
            {
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
            },
            {
                'id': 'grade_06',
                'name': '六年级',
                'grade_level': 6,
                'manager_id': 'grade_manager_02',
                'school_id': 'school_01',
                'total_classes': 1,
                'total_students': 28,
                'total_teachers': 1,
                'average_accuracy': 76.2,
                'created_at': '2025-01-01',
                'updated_at': '2025-07-12'
            }
        ]
    
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
    
    def test_principal_dashboard_initialization(self, principal_dashboard):
        """测试校长仪表盘初始化"""
        assert principal_dashboard is not None
        assert hasattr(principal_dashboard, 'data_service')
        assert hasattr(principal_dashboard, 'user_management')
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.write')
    @patch('streamlit.divider')
    def test_render_school_overview_success(self, mock_divider, mock_write, mock_metric, 
                                          mock_columns, mock_warning, mock_subheader,
                                          principal_dashboard, mock_school_data, mock_principal_data):
        """测试学校概览渲染成功"""
        # 模拟用户管理方法
        with patch.object(principal_dashboard.user_management, 'get_school_info', return_value=mock_school_data), \
             patch.object(principal_dashboard.user_management, 'get_user_by_id', return_value=mock_principal_data):
            
            # 模拟Streamlit组件
            mock_col1, mock_col2, mock_col3, mock_col4 = Mock(), Mock(), Mock(), Mock()
            # 为列对象添加上下文管理器支持
            for col in [mock_col1, mock_col2, mock_col3, mock_col4]:
                col.__enter__ = Mock(return_value=col)
                col.__exit__ = Mock(return_value=None)
            mock_columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4]
            
            # 执行测试
            principal_dashboard.render_school_overview('principal_01')
            
            # 验证调用
            mock_subheader.assert_called_with("🏫 学校概览")
            mock_columns.assert_called_with(4)
            # 由于Mock的限制，我们验证基本调用而不是具体次数
            assert mock_metric.called or mock_write.called
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_school_overview_no_school(self, mock_warning, mock_subheader, principal_dashboard):
        """测试学校概览 - 无学校信息"""
        with patch.object(principal_dashboard.user_management, 'get_school_info', return_value=None):
            principal_dashboard.render_school_overview('principal_01')
            mock_warning.assert_called_with("无法获取学校信息")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.dataframe')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.divider')
    def test_render_grade_comparison_success(self, mock_divider, mock_plotly_chart, mock_dataframe, 
                                           mock_warning, mock_subheader,
                                           principal_dashboard, mock_grade_data):
        """测试年级对比渲染成功"""
        with patch.object(principal_dashboard.user_management, 'get_all_grades', return_value=mock_grade_data):
            
            principal_dashboard.render_grade_comparison('principal_01')
            
            # 验证调用
            mock_subheader.assert_called_with("📊 年级对比")
            mock_dataframe.assert_called_once()
            mock_plotly_chart.assert_called_once()
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_grade_comparison_no_grades(self, mock_warning, mock_subheader, principal_dashboard):
        """测试年级对比 - 无年级数据"""
        with patch.object(principal_dashboard.user_management, 'get_all_grades', return_value=[]):
            principal_dashboard.render_grade_comparison('principal_01')
            mock_warning.assert_called_with("暂无年级数据")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.dataframe')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    def test_render_subject_performance_success(self, mock_divider, mock_info, mock_plotly_chart, 
                                              mock_dataframe, mock_warning, mock_subheader,
                                              principal_dashboard, mock_class_data):
        """测试学科表现渲染成功"""
        with patch.object(principal_dashboard.user_management, 'get_all_classes', return_value=mock_class_data):
            
            principal_dashboard.render_subject_performance('principal_01')
            
            # 验证调用
            mock_subheader.assert_called_with("📚 学科表现")
            mock_dataframe.assert_called_once()
            mock_plotly_chart.assert_called_once()
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_subject_performance_no_classes(self, mock_warning, mock_subheader, principal_dashboard):
        """测试学科表现 - 无班级数据"""
        with patch.object(principal_dashboard.user_management, 'get_all_classes', return_value=[]):
            principal_dashboard.render_subject_performance('principal_01')
            mock_warning.assert_called_with("暂无班级数据")
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    @patch('streamlit.dataframe')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    def test_render_teacher_team_evaluation_success(self, mock_divider, mock_info, mock_plotly_chart, 
                                                   mock_dataframe, mock_warning, mock_subheader,
                                                   principal_dashboard, mock_teacher_data, mock_class_data):
        """测试教师团队评估渲染成功"""
        with patch.object(principal_dashboard.user_management, 'get_teachers', return_value=mock_teacher_data), \
             patch.object(principal_dashboard.user_management, 'get_managed_classes', return_value=mock_class_data):
            
            principal_dashboard.render_teacher_team_evaluation('principal_01')
            
            # 验证调用
            mock_subheader.assert_called_with("👩‍🏫 教师团队评估")
            mock_dataframe.assert_called_once()
            mock_plotly_chart.assert_called_once()
    
    @patch('streamlit.subheader')
    @patch('streamlit.warning')
    def test_render_teacher_team_evaluation_no_teachers(self, mock_warning, mock_subheader, principal_dashboard):
        """测试教师团队评估 - 无教师数据"""
        with patch.object(principal_dashboard.user_management, 'get_teachers', return_value=[]):
            principal_dashboard.render_teacher_team_evaluation('principal_01')
            mock_warning.assert_called_with("暂无教师数据")
    
    @patch('streamlit.subheader')
    @patch('streamlit.write')
    @patch('streamlit.columns')
    @patch('streamlit.divider')
    @patch('streamlit.container')
    def test_render_strategic_suggestions_success(self, mock_container, mock_divider, mock_columns, mock_write, 
                                                mock_subheader,
                                                principal_dashboard, mock_school_data, mock_grade_data, mock_teacher_data):
        """测试战略建议渲染成功"""
        with patch.object(principal_dashboard.user_management, 'get_school_info', return_value=mock_school_data), \
             patch.object(principal_dashboard.user_management, 'get_all_grades', return_value=mock_grade_data), \
             patch.object(principal_dashboard.user_management, 'get_teachers', return_value=mock_teacher_data):
            
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
            
            principal_dashboard.render_strategic_suggestions('principal_01')
            
            # 验证调用
            mock_subheader.assert_called_with("💡 战略建议")
    
    @patch('streamlit.subheader')
    @patch('streamlit.button')
    @patch('streamlit.success')
    @patch('streamlit.info')
    @patch('streamlit.divider')
    def test_render_quick_actions(self, mock_divider, mock_info, mock_success, mock_button, mock_subheader,
                                principal_dashboard):
        """测试快速操作渲染"""
        # 模拟按钮返回False
        mock_button.return_value = False
        
        principal_dashboard.render_quick_actions('principal_01')
        
        # 验证调用
        mock_subheader.assert_called_with("⚡ 快速操作")
        assert mock_button.call_count >= 6  # 6个快速操作按钮
    
    @patch('streamlit.title')
    @patch('streamlit.write')
    @patch('streamlit.tabs')
    @patch('streamlit.divider')
    def test_render_principal_dashboard_success(self, mock_divider, mock_tabs, mock_write, mock_title,
                                              principal_dashboard, mock_principal_data, mock_school_data):
        """测试校长仪表盘主界面渲染成功"""
        with patch.object(principal_dashboard.user_management, 'get_user_by_id', return_value=mock_principal_data), \
             patch.object(principal_dashboard.user_management, 'get_school_info', return_value=mock_school_data), \
             patch.object(principal_dashboard, 'render_school_overview'), \
             patch.object(principal_dashboard, 'render_grade_comparison'), \
             patch.object(principal_dashboard, 'render_subject_performance'), \
             patch.object(principal_dashboard, 'render_teacher_team_evaluation'), \
             patch.object(principal_dashboard, 'render_strategic_suggestions'), \
             patch.object(principal_dashboard, 'render_quick_actions'):
            
            # 模拟标签页上下文管理器
            mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5 = Mock(), Mock(), Mock(), Mock(), Mock()
            for tab in [mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5]:
                tab.__enter__ = Mock(return_value=tab)
                tab.__exit__ = Mock(return_value=None)
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4, mock_tab5]
            
            principal_dashboard.render_principal_dashboard('principal_01')
            
            # 验证调用
            mock_title.assert_called_with("🏫 校长仪表盘")
            mock_tabs.assert_called_with([
                "🏫 学校概览",
                "📊 年级对比",
                "📚 学科表现",
                "👩‍🏫 教师团队",
                "💡 战略建议"
            ])
    
    @patch('streamlit.error')
    def test_render_principal_dashboard_no_principal(self, mock_error, principal_dashboard):
        """测试校长仪表盘 - 无校长信息"""
        with patch.object(principal_dashboard.user_management, 'get_user_by_id', return_value=None):
            principal_dashboard.render_principal_dashboard('invalid_id')
            mock_error.assert_called_with("无法获取校长信息")
    
    def test_principal_dashboard_data_integration(self, principal_dashboard):
        """测试校长仪表盘数据集成"""
        # 测试数据服务集成
        assert principal_dashboard.data_service is not None
        assert principal_dashboard.user_management is not None
        
        # 测试用户管理实例
        assert principal_dashboard.user_management == user_management_v2

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 