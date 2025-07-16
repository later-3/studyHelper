"""
页面管理器 - 统一管理所有页面路由和状态
遵循单一职责原则，提升代码可维护性
"""

import streamlit as st
from typing import Dict, Callable, Any
from dataclasses import dataclass
from enum import Enum

class UserRole(Enum):
    """用户角色枚举"""
    STUDENT = "student"
    TEACHER = "teacher"
    GRADE_MANAGER = "grade_manager"
    PRINCIPAL = "principal"

@dataclass
class PageConfig:
    """页面配置"""
    title: str
    icon: str
    roles: list  # 允许访问的角色
    handler: Callable
    requires_auth: bool = True

class PageManager:
    """页面管理器"""
    
    def __init__(self):
        self.pages: Dict[str, PageConfig] = {}
        self._register_pages()
    
    def _register_pages(self):
        """注册所有页面"""
        # 公共页面
        self.register_page("home", PageConfig(
            title="首页",
            icon="house",
            roles=[],
            handler=self._render_home,
            requires_auth=False
        ))
        
        self.register_page("about", PageConfig(
            title="关于",
            icon="info-circle",
            roles=[],
            handler=self._render_about,
            requires_auth=False
        ))
        
        # 需要登录的页面
        self.register_page("dashboard", PageConfig(
            title="仪表盘",
            icon="speedometer",
            roles=[UserRole.STUDENT.value, UserRole.TEACHER.value, 
                   UserRole.GRADE_MANAGER.value, UserRole.PRINCIPAL.value],
            handler=self._render_dashboard
        ))
        
        self.register_page("search", PageConfig(
            title="智能搜题",
            icon="search",
            roles=[UserRole.STUDENT.value, UserRole.TEACHER.value],
            handler=self._render_search
        ))
        
        self.register_page("history", PageConfig(
            title="答题历史",
            icon="card-checklist",
            roles=[UserRole.STUDENT.value, UserRole.TEACHER.value, 
                   UserRole.GRADE_MANAGER.value, UserRole.PRINCIPAL.value],
            handler=self._render_history
        ))
    
    def register_page(self, key: str, config: PageConfig):
        """注册页面"""
        self.pages[key] = config
    
    def get_available_pages(self, user_role: str = None) -> Dict[str, PageConfig]:
        """获取用户可访问的页面"""
        if not user_role:
            # 未登录用户只能访问公共页面
            return {k: v for k, v in self.pages.items() if not v.requires_auth}
        
        # 已登录用户可访问对应角色的页面
        return {k: v for k, v in self.pages.items() 
                if not v.requires_auth or user_role in v.roles}
    
    def render_page(self, page_key: str):
        """渲染指定页面"""
        if page_key not in self.pages:
            st.error(f"页面 '{page_key}' 不存在")
            return
        
        page_config = self.pages[page_key]
        
        # 检查权限
        if page_config.requires_auth:
            current_user = st.session_state.get('current_user')
            if not current_user:
                st.warning("请先登录以访问此页面")
                return
            
            if current_user['role'] not in page_config.roles:
                st.error("您没有权限访问此页面")
                return
        
        # 渲染页面
        try:
            page_config.handler()
        except Exception as e:
            st.error(f"页面加载失败: {str(e)}")
            st.exception(e)
    
    def _render_home(self):
        """渲染首页"""
        from pages.home_page import render_home_page
        render_home_page()
    
    def _render_about(self):
        """渲染关于页面"""
        from pages.about_page import render_about_page
        render_about_page()
    
    def _render_dashboard(self):
        """渲染仪表盘"""
        from pages.dashboard_page import render_dashboard_page
        render_dashboard_page()
    
    def _render_search(self):
        """渲染智能搜题"""
        from pages.search_page import render_search_page
        render_search_page()
    
    def _render_history(self):
        """渲染答题历史"""
        from pages.history_page import render_history_page
        render_history_page()

# 全局页面管理器实例
page_manager = PageManager()