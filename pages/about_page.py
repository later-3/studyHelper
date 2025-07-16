"""
关于页面组件
显示项目信息和版本详情
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_about_page():
    """渲染关于页面"""
    logger.info("渲染关于页面")
    
    st.title("ℹ️ 关于 StudyHelper")
    
    # 项目信息
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📖 项目简介
        
        StudyHelper 是一款基于 AI 技术的智能学习辅助工具，旨在帮助学生、教师和学校更高效地进行教与学。
        
        ### 🎯 核心特性
        
        - **智能题目分析**：基于 GPT-4 的深度分析
        - **OCR 文字识别**：支持手写和印刷体识别
        - **多角色权限**：学生、教师、管理者不同视图
        - **数据可视化**：丰富的图表和统计分析
        - **智能缓存**：相同题目秒级响应
        
        ### 🛠️ 技术栈
        
        - **前端**：Streamlit + Python
        - **AI 分析**：OpenAI GPT-4 API
        - **OCR 识别**：PaddleOCR
        - **数据存储**：JSON + 未来支持数据库
        - **容器化**：Docker 支持
        """)
    
    with col2:
        st.markdown("""
        ### 📊 版本信息
        
        **当前版本**：v2.1.0  
        **发布日期**：2025-01-16  
        **构建状态**：✅ 稳定版  
        
        ### 🔗 相关链接
        
        - [项目文档](docs/)
        - [开发日志](devLog/)
        - [测试报告](tests/)
        
        ### 📞 技术支持
        
        如有问题请查看开发日志或联系开发团队。
        """)
    
    # 更新日志
    st.markdown("---")
    st.markdown("### 📝 更新日志")
    
    with st.expander("v2.1.0 - UI重构版本", expanded=True):
        st.markdown("""
        **新增功能：**
        - 🎨 重构UI组件架构
        - 📱 优化页面管理系统
        - 🔧 改进错误处理机制
        - 📊 增强日志记录功能
        
        **性能优化：**
        - ⚡ 提升页面加载速度
        - 🚀 优化缓存策略
        - 💾 减少内存占用
        """)
    
    with st.expander("v2.0.0 - 多角色仪表盘"):
        st.markdown("""
        **新增功能：**
        - 👥 多角色用户系统
        - 📊 角色化仪表盘
        - 📈 数据可视化图表
        - 🔍 高级筛选功能
        """)
    
    # 致谢
    st.markdown("---")
    st.markdown("""
    ### 🙏 致谢
    
    感谢所有开源项目的贡献者，特别是：
    - Streamlit 团队
    - OpenAI 
    - PaddlePaddle 团队
    - 所有测试用户的反馈
    """)