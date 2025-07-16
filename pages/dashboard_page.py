"""
仪表盘页面组件
根据用户角色显示不同的仪表盘
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_dashboard_page():
    """渲染仪表盘页面"""
    logger.info("渲染仪表盘页面")
    
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("请先登录以访问仪表盘")
        return
    
    user_role = current_user.get('role')
    user_name = current_user.get('name', '用户')
    
    logger.info(f"为用户 {current_user['id']} (角色: {user_role}) 渲染仪表盘")
    
    # 页面标题
    role_icons = {
        'student': '🎓',
        'teacher': '👨‍🏫', 
        'grade_manager': '📊',
        'principal': '🏫'
    }
    
    role_names = {
        'student': '学生',
        'teacher': '教师',
        'grade_manager': '年级主任',
        'principal': '校长'
    }
    
    icon = role_icons.get(user_role, '👤')
    role_name = role_names.get(user_role, '用户')
    
    st.title(f"{icon} {role_name}仪表盘")
    st.markdown(f"欢迎，**{user_name}**！")
    
    # 根据角色渲染不同的仪表盘
    try:
        if user_role == 'student':
            _render_student_dashboard(current_user)
        elif user_role == 'teacher':
            _render_teacher_dashboard(current_user)
        elif user_role == 'grade_manager':
            _render_grade_manager_dashboard(current_user)
        elif user_role == 'principal':
            _render_principal_dashboard(current_user)
        else:
            st.warning(f"未知的用户角色: {user_role}")
            logger.warning(f"未知用户角色: {user_role}")
            
    except Exception as e:
        logger.error(f"渲染 {user_role} 仪表盘时发生错误: {e}")
        st.error(f"仪表盘加载失败: {str(e)}")
        
        # 显示错误详情（仅在调试模式下）
        if st.checkbox("显示错误详情"):
            st.exception(e)

def _render_student_dashboard(user):
    """渲染学生仪表盘"""
    logger.debug(f"渲染学生 {user['id']} 的仪表盘")
    
    try:
        from components.student_dashboard import StudentDashboard
        dashboard = StudentDashboard()
        dashboard.render_student_dashboard(user['id'])
    except ImportError as e:
        logger.error(f"导入学生仪表盘组件失败: {e}")
        st.error("学生仪表盘组件加载失败")
        _render_fallback_dashboard("学生", user)
    except Exception as e:
        logger.error(f"渲染学生仪表盘时发生错误: {e}")
        st.error("学生仪表盘渲染失败")
        _render_fallback_dashboard("学生", user)

def _render_teacher_dashboard(user):
    """渲染教师仪表盘"""
    logger.debug(f"渲染教师 {user['id']} 的仪表盘")
    
    try:
        from components.teacher_dashboard import TeacherDashboard
        dashboard = TeacherDashboard()
        dashboard.render_teacher_dashboard(user['id'])
    except ImportError as e:
        logger.error(f"导入教师仪表盘组件失败: {e}")
        st.error("教师仪表盘组件加载失败")
        _render_fallback_dashboard("教师", user)
    except Exception as e:
        logger.error(f"渲染教师仪表盘时发生错误: {e}")
        st.error("教师仪表盘渲染失败")
        _render_fallback_dashboard("教师", user)

def _render_grade_manager_dashboard(user):
    """渲染年级主任仪表盘"""
    logger.debug(f"渲染年级主任 {user['id']} 的仪表盘")
    
    try:
        from components.grade_manager_dashboard import GradeManagerDashboard
        dashboard = GradeManagerDashboard()
        dashboard.render_grade_manager_dashboard(user['id'])
    except ImportError as e:
        logger.error(f"导入年级主任仪表盘组件失败: {e}")
        st.error("年级主任仪表盘组件加载失败")
        _render_fallback_dashboard("年级主任", user)
    except Exception as e:
        logger.error(f"渲染年级主任仪表盘时发生错误: {e}")
        st.error("年级主任仪表盘渲染失败")
        _render_fallback_dashboard("年级主任", user)

def _render_principal_dashboard(user):
    """渲染校长仪表盘"""
    logger.debug(f"渲染校长 {user['id']} 的仪表盘")
    
    try:
        from components.principal_dashboard import PrincipalDashboard
        dashboard = PrincipalDashboard()
        dashboard.render_principal_dashboard(user['id'])
    except ImportError as e:
        logger.error(f"导入校长仪表盘组件失败: {e}")
        st.error("校长仪表盘组件加载失败")
        _render_fallback_dashboard("校长", user)
    except Exception as e:
        logger.error(f"渲染校长仪表盘时发生错误: {e}")
        st.error("校长仪表盘渲染失败")
        _render_fallback_dashboard("校长", user)

def _render_fallback_dashboard(role_name, user):
    """渲染备用仪表盘（当主仪表盘失败时）"""
    logger.info(f"渲染 {role_name} 的备用仪表盘")
    
    st.markdown("---")
    st.subheader(f"📊 {role_name}概览")
    
    # 基本信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("用户ID", user['id'])
    
    with col2:
        st.metric("角色", role_name)
    
    with col3:
        st.metric("状态", "正常")
    
    # 功能提示
    st.markdown("---")
    st.info(f"""
    🔧 {role_name}仪表盘正在维护中...
    
    您可以使用以下功能：
    - 🧠 智能搜题
    - 📖 答题历史
    - ℹ️ 查看项目信息
    
    如有问题，请联系技术支持。
    """)
    
    # 快速操作按钮
    st.markdown("### 🚀 快速操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧠 开始搜题", use_container_width=True):
            st.session_state.selected_page = "search"
            st.rerun()
    
    with col2:
        if st.button("📖 查看历史", use_container_width=True):
            st.session_state.selected_page = "history"
            st.rerun()
    
    with col3:
        if st.button("ℹ️ 关于系统", use_container_width=True):
            st.session_state.selected_page = "about"
            st.rerun()