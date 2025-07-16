"""
首页页面组件
提供项目介绍和导航功能
"""

import streamlit as st
from streamlit_lottie import st_lottie
import requests
import logging

logger = logging.getLogger(__name__)

def load_lottie_animation(url: str):
    """
    加载Lottie动画
    
    Args:
        url: 动画URL
        
    Returns:
        dict: 动画数据，失败时返回None
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logger.debug(f"成功加载Lottie动画: {url}")
            return response.json()
        else:
            logger.warning(f"Lottie动画加载失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Lottie动画请求失败: {e}")
        return None

def render_home_page():
    """渲染首页"""
    logger.info("渲染首页")
    
    st.title("🏠 StudyHelper 智能学习助手")
    st.markdown("## 🎯 欢迎使用 StudyHelper！")
    
    # 加载动画
    lottie_url = "https://lottie.host/embed/a7b5c79a-18c7-4bb9-9a24-9aacb741b330/2Jp4k5t9kM.json"
    lottie_json = load_lottie_animation(lottie_url)
    
    if lottie_json:
        st_lottie(lottie_json, speed=1, width=600, height=300, key="study_lottie")
    else:
        # 动画加载失败时显示静态内容
        st.image("https://via.placeholder.com/600x300/1976D2/FFFFFF?text=StudyHelper", 
                caption="StudyHelper - 您的AI学习伙伴")
    
    # 功能介绍
    st.markdown("""
    ### ✨ 主要功能
    
    **🧠 智能搜题**
    - 上传题目图片，AI将为您提供详细的解题思路
    - 包含知识点分析和易错点提醒
    - 智能缓存，相同题目秒级响应
    
    **📖 答题历史**
    - 自动收录您分析过的所有题目
    - 支持多维度筛选和分组查看
    - 可视化学习数据分析
    
    **👥 多角色支持**
    - 学生：个人学习助手
    - 教师：班级管理工具
    - 管理者：数据分析平台
    
    ### 🚀 开始使用
    
    👈 请从左侧导航栏选择功能开始使用！
    """)
    
    # 用户状态提示
    current_user = st.session_state.get('current_user')
    if current_user:
        st.success(f"欢迎回来，{current_user['name']}！")
    else:
        st.info("💡 提示：请先从左侧边栏登录以使用完整功能")