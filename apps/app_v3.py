"""
StudyHelper 主应用 v3.0 - UI重构版本

重构特性：
1. 统一的页面管理系统
2. 优化的组件结构
3. 改进的错误处理
4. 更好的日志记录
5. 清晰的状态管理
"""

import streamlit as st
from streamlit_option_menu import option_menu
import os
import sys
import logging
from dotenv import load_dotenv

# 路径设置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 核心导入
from core import logger_config
from core import user_management_v2 as um
from components.page_manager import page_manager

# 初始化
logger_config.setup_logging()
logger = logging.getLogger(__name__)
load_dotenv()

class StudyHelperApp:
    """StudyHelper主应用类"""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
        logger.info("StudyHelper应用初始化完成")
    
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="StudyHelper v3.0",
            page_icon="📘",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_session_state(self):
        """初始化session state"""
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
            logger.debug("初始化用户session state")
        
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'home'
            logger.debug("初始化页面选择session state")
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            self._render_user_section()
            st.markdown("---")
            self._render_navigation()
    
    def _render_user_section(self):
        """渲染用户区域"""
        current_user = st.session_state.current_user
        
        if current_user:
            self._render_logged_in_user(current_user)
        else:
            self._render_login_section()
    
    def _render_logged_in_user(self, user):
        """渲染已登录用户信息"""
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
        
        icon = role_icons.get(user['role'], '👤')
        role_name = role_names.get(user['role'], '用户')
        
        # 用户信息卡片
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1976D2, #42A5F5);
            padding: 1rem;
            border-radius: 8px;
            color: white;
            margin-bottom: 1rem;
        ">
            <h3 style="margin: 0; color: white;">{icon} {user['name']}</h3>
            <p style="margin: 0; opacity: 0.9;">角色: {role_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 退出登录按钮
        if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
            self._logout_user()
    
    def _render_login_section(self):
        """渲染登录区域"""
        st.markdown("### 👋 欢迎使用")
        st.info("请选择用户登录以使用完整功能")
        
        try:
            users = um.get_all_users()
            if not users:
                st.error("无法加载用户列表")
                logger.error("用户列表为空")
                return
            
            # 用户选择
            user_options = {
                user['id']: f"{user['name']} ({user['role']})" 
                for user in users
            }
            
            selected_user_id = st.selectbox(
                "选择用户",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                index=None,
                placeholder="请选择用户...",
                key="user_selector"
            )
            
            # 登录按钮
            if st.button("🔑 登录", use_container_width=True, type="primary"):
                if selected_user_id:
                    self._login_user(selected_user_id)
                else:
                    st.warning("请先选择一个用户")
                    
        except Exception as e:
            logger.error(f"渲染登录区域时发生错误: {e}")
            st.error("登录功能暂时不可用")
    
    def _login_user(self, user_id):
        """用户登录"""
        try:
            user = um.get_user_by_id(user_id)
            if user:
                st.session_state.current_user = user
                st.session_state.selected_page = 'dashboard'  # 登录后跳转到仪表盘
                logger.info(f"用户 {user['name']} ({user['id']}) 登录成功")
                st.success(f"欢迎，{user['name']}！")
                st.rerun()
            else:
                st.error("用户不存在")
                logger.warning(f"尝试登录不存在的用户: {user_id}")
        except Exception as e:
            logger.error(f"用户登录时发生错误: {e}")
            st.error("登录失败，请重试")
    
    def _logout_user(self):
        """用户退出登录"""
        user_name = st.session_state.current_user.get('name', '用户')
        logger.info(f"用户 {user_name} 退出登录")
        
        # 清理session state
        st.session_state.current_user = None
        st.session_state.selected_page = 'home'
        
        # 清理其他可能的状态
        keys_to_clear = [
            'search_results', 'uploaded_image_path', 'history_view_mode',
            'subject_filter', 'correctness_filter', 'date_filter'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.success("已成功退出登录")
        st.rerun()
    
    def _render_navigation(self):
        """渲染导航菜单"""
        current_user = st.session_state.current_user
        user_role = current_user['role'] if current_user else None
        
        # 获取可用页面
        available_pages = page_manager.get_available_pages(user_role)
        
        # 构建菜单选项
        options = []
        icons = []
        
        for page_key, page_config in available_pages.items():
            options.append(page_config.title)
            icons.append(page_config.icon)
        
        # 渲染菜单
        if options:
            # 确定当前选中的索引
            current_page = st.session_state.get('selected_page', 'home')
            try:
                current_index = list(available_pages.keys()).index(current_page)
            except ValueError:
                current_index = 0
                st.session_state.selected_page = list(available_pages.keys())[0]
            
            selected = option_menu(
                menu_title="StudyHelper",
                options=options,
                icons=icons,
                menu_icon="book-half",
                default_index=current_index,
                styles={
                    "container": {"padding": "5!important", "background-color": "#fafafa"},
                    "icon": {"color": "#1976D2", "font-size": "20px"},
                    "nav-link": {
                        "color": "#333333",
                        "font-size": "14px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#e3f2fd"
                    },
                    "nav-link-selected": {"background-color": "#1976D2"},
                }
            )
            
            # 更新选中的页面
            selected_page_key = list(available_pages.keys())[options.index(selected)]
            if selected_page_key != st.session_state.get('selected_page'):
                st.session_state.selected_page = selected_page_key
                logger.debug(f"页面切换到: {selected_page_key}")
                st.rerun()
    
    def render_main_content(self):
        """渲染主要内容"""
        current_page = st.session_state.get('selected_page', 'home')
        
        try:
            logger.debug(f"渲染页面: {current_page}")
            page_manager.render_page(current_page)
        except Exception as e:
            logger.error(f"渲染页面 {current_page} 时发生错误: {e}")
            st.error(f"页面加载失败: {str(e)}")
            
            # 显示错误详情（仅在调试模式下）
            if st.checkbox("显示错误详情", key="show_error_details"):
                st.exception(e)
            
            # 提供返回首页的选项
            if st.button("🏠 返回首页", key="back_to_home"):
                st.session_state.selected_page = 'home'
                st.rerun()
    
    def run(self):
        """运行应用"""
        try:
            logger.info("开始渲染StudyHelper应用")
            
            # 渲染侧边栏
            self.render_sidebar()
            
            # 渲染主要内容
            self.render_main_content()
            
        except Exception as e:
            logger.critical(f"应用运行时发生严重错误: {e}")
            st.error("应用运行异常，请刷新页面重试")
            st.exception(e)

def main():
    """主函数"""
    try:
        app = StudyHelperApp()
        app.run()
    except Exception as e:
        logger.critical(f"应用启动失败: {e}")
        st.error("应用启动失败")
        st.exception(e)

if __name__ == "__main__":
    main()