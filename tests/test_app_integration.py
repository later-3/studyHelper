"""
主应用集成测试
测试角色仪表盘在主应用中的集成情况
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入主应用模块
from apps import app_v2

class TestAppIntegration:
    """主应用集成测试类"""
    
    @pytest.fixture
    def mock_user_data(self):
        """模拟用户数据"""
        return {
            'student': {
                'id': 'student_01',
                'name': '张三',
                'role': 'student',
                'class_id': 'class_01',
                'grade_id': 'grade_05',
                'school_id': 'school_01'
            },
            'teacher': {
                'id': 'teacher_01',
                'name': '李老师',
                'role': 'teacher',
                'class_id': 'class_01',
                'grade_id': 'grade_05',
                'school_id': 'school_01'
            },
            'grade_manager': {
                'id': 'grade_manager_01',
                'name': '王主任',
                'role': 'grade_manager',
                'grade_id': 'grade_05',
                'school_id': 'school_01'
            },
            'principal': {
                'id': 'principal_01',
                'name': '陈校长',
                'role': 'principal',
                'school_id': 'school_01'
            }
        }
    
    def test_app_import_success(self):
        """测试主应用导入成功"""
        assert app_v2 is not None
        assert hasattr(app_v2, 'role_dashboard_page')
        assert hasattr(app_v2, 'intelligent_search_page')
        assert hasattr(app_v2, 'submission_history_page')
    
    @patch('streamlit.title')
    @patch('streamlit.warning')
    def test_role_dashboard_page_no_user(self, mock_warning, mock_title):
        """测试角色仪表盘页面 - 无用户"""
        app_v2.role_dashboard_page()
        mock_warning.assert_called_with("请先登录以查看此页面。")
    
    @patch('streamlit.title')
    @patch('streamlit.error')
    @patch('components.student_dashboard.StudentDashboard')
    def test_role_dashboard_page_student(self, mock_student_dashboard, mock_error, mock_title, mock_user_data):
        """测试角色仪表盘页面 - 学生角色"""
        # 模拟session state
        with patch.dict('app_v2.st.session_state', {'current_user': mock_user_data['student']}):
            # 模拟学生仪表盘
            mock_dashboard_instance = Mock()
            mock_student_dashboard.return_value = mock_dashboard_instance
            
            app_v2.role_dashboard_page()
            
            # 验证调用
            mock_title.assert_called_with("🎓 学生仪表盘")
            mock_student_dashboard.assert_called_once()
            mock_dashboard_instance.render_student_dashboard.assert_called_with('student_01')
    
    @patch('streamlit.title')
    @patch('streamlit.error')
    @patch('components.teacher_dashboard.TeacherDashboard')
    def test_role_dashboard_page_teacher(self, mock_teacher_dashboard, mock_error, mock_title, mock_user_data):
        """测试角色仪表盘页面 - 教师角色"""
        # 模拟session state
        with patch.dict('app_v2.st.session_state', {'current_user': mock_user_data['teacher']}):
            # 模拟教师仪表盘
            mock_dashboard_instance = Mock()
            mock_teacher_dashboard.return_value = mock_dashboard_instance
            
            app_v2.role_dashboard_page()
            
            # 验证调用
            mock_title.assert_called_with("👨‍🏫 教师仪表盘")
            mock_teacher_dashboard.assert_called_once()
            mock_dashboard_instance.render_teacher_dashboard.assert_called_with('teacher_01')
    
    @patch('streamlit.title')
    @patch('streamlit.error')
    @patch('components.grade_manager_dashboard.GradeManagerDashboard')
    def test_role_dashboard_page_grade_manager(self, mock_grade_manager_dashboard, mock_error, mock_title, mock_user_data):
        """测试角色仪表盘页面 - 年级主任角色"""
        # 模拟session state
        with patch.dict('app_v2.st.session_state', {'current_user': mock_user_data['grade_manager']}):
            # 模拟年级主任仪表盘
            mock_dashboard_instance = Mock()
            mock_grade_manager_dashboard.return_value = mock_dashboard_instance
            
            app_v2.role_dashboard_page()
            
            # 验证调用
            mock_title.assert_called_with("👨‍💼 年级主任仪表盘")
            mock_grade_manager_dashboard.assert_called_once()
            mock_dashboard_instance.render_grade_manager_dashboard.assert_called_with('grade_manager_01')
    
    @patch('streamlit.title')
    @patch('streamlit.error')
    @patch('components.principal_dashboard.PrincipalDashboard')
    def test_role_dashboard_page_principal(self, mock_principal_dashboard, mock_error, mock_title, mock_user_data):
        """测试角色仪表盘页面 - 校长角色"""
        # 模拟session state
        with patch.dict('app_v2.st.session_state', {'current_user': mock_user_data['principal']}):
            # 模拟校长仪表盘
            mock_dashboard_instance = Mock()
            mock_principal_dashboard.return_value = mock_dashboard_instance
            
            app_v2.role_dashboard_page()
            
            # 验证调用
            mock_title.assert_called_with("🏫 校长仪表盘")
            mock_principal_dashboard.assert_called_once()
            mock_dashboard_instance.render_principal_dashboard.assert_called_with('principal_01')
    
    @patch('streamlit.title')
    @patch('streamlit.error')
    def test_role_dashboard_page_unknown_role(self, mock_error, mock_title):
        """测试角色仪表盘页面 - 未知角色"""
        # 模拟session state
        with patch.dict('app_v2.st.session_state', {'current_user': {'id': 'unknown', 'role': 'unknown'}}):
            app_v2.role_dashboard_page()
            mock_error.assert_called_with("未知的用户角色: unknown")
    
    def test_app_functions_exist(self):
        """测试主应用函数存在"""
        # 测试核心函数存在
        assert hasattr(app_v2, 'home')
        assert hasattr(app_v2, 'about')
        assert hasattr(app_v2, 'intelligent_search_page')
        assert hasattr(app_v2, 'submission_history_page')
        assert hasattr(app_v2, 'role_dashboard_page')
        
        # 测试辅助函数存在
        assert hasattr(app_v2, 'render_analysis_results')
        assert hasattr(app_v2, 'render_grouped_view')
        assert hasattr(app_v2, 'render_timeline_view')
        assert hasattr(app_v2, 'render_stats_view')
    
    def test_app_imports(self):
        """测试主应用导入的模块"""
        # 测试角色仪表盘组件导入
        from components.student_dashboard import StudentDashboard
        from components.teacher_dashboard import TeacherDashboard
        from components.grade_manager_dashboard import GradeManagerDashboard
        from components.principal_dashboard import PrincipalDashboard
        
        assert StudentDashboard is not None
        assert TeacherDashboard is not None
        assert GradeManagerDashboard is not None
        assert PrincipalDashboard is not None
        
        # 测试用户管理模块导入
        from core import user_management_v2
        assert user_management_v2 is not None

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 