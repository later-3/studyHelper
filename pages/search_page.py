"""
智能搜题页面组件
处理图片上传、OCR识别和AI分析
"""

import streamlit as st
import os
import uuid
import logging
from PIL import Image

# 导入服务层
from services import ocr_service, storage_service
from core.ai_services import get_ocr_engine

logger = logging.getLogger(__name__)

def render_search_page():
    """渲染智能搜题页面"""
    logger.info("渲染智能搜题页面")
    
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("请先登录以使用此功能")
        return
    
    st.title("🧠 智能搜题")
    st.markdown("上传题目照片，AI导师将为您提供详细分析和解题思路")
    
    # 初始化session state
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'uploaded_image_path' not in st.session_state:
        st.session_state.uploaded_image_path = None
    
    # 文件上传区域
    uploaded_file = st.file_uploader(
        "选择题目图片",
        type=["jpg", "jpeg", "png"],
        help="支持 JPG、JPEG、PNG 格式，建议图片清晰且题目完整"
    )
    
    if uploaded_file is not None:
        # 显示上传的图片
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(uploaded_file, caption="上传的题目图片", use_container_width=True)
        
        with col2:
            st.markdown("### 📋 操作选项")
            
            # 保存图片到临时目录
            if st.button("🔍 开始识别", type="primary", use_container_width=True):
                _process_uploaded_image(uploaded_file, current_user)
            
            if st.session_state.search_results:
                if st.button("🔄 重新分析", use_container_width=True):
                    _force_reanalyze(current_user)
    
    # 显示分析结果
    if st.session_state.search_results:
        _render_analysis_results()

def _process_uploaded_image(uploaded_file, current_user):
    """
    处理上传的图片
    
    Args:
        uploaded_file: Streamlit上传的文件对象
        current_user: 当前用户信息
    """
    try:
        logger.info(f"用户 {current_user['id']} 开始处理上传图片")
        
        # 保存图片到用户目录
        user_dir = f"data/submissions/{current_user['id']}"
        os.makedirs(user_dir, exist_ok=True)
        
        image_filename = f"{uuid.uuid4().hex[:12]}.png"
        image_path = os.path.join(user_dir, image_filename)
        
        # 保存图片
        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state.uploaded_image_path = image_path
        logger.info(f"图片已保存到: {image_path}")
        
        # 开始OCR识别
        with st.spinner("🔍 正在识别图片中的文字..."):
            _perform_ocr_analysis(image_path, current_user)
            
    except Exception as e:
        logger.error(f"处理上传图片时发生错误: {e}")
        st.error(f"图片处理失败: {str(e)}")

def _perform_ocr_analysis(image_path, current_user):
    """
    执行OCR识别和AI分析
    
    Args:
        image_path: 图片路径
        current_user: 当前用户信息
    """
    try:
        # Step 1: OCR识别
        logger.info("开始OCR文字识别")
        ocr_result = ocr_service.get_text_from_image(image_path)
        
        if not ocr_result or ocr_result[0] in ["识别失败", "识别异常"]:
            st.error("❌ 文字识别失败，请确保图片清晰且包含文字内容")
            logger.warning(f"OCR识别失败: {ocr_result}")
            return
        
        ocr_text = '\n'.join(ocr_result)
        logger.info(f"OCR识别成功，文字长度: {len(ocr_text)}")
        
        # Step 2: AI分析
        with st.spinner("🤖 AI正在分析题目..."):
            from apps.app_v2 import intelligent_search_logic
            
            analysis, _, cache_status, question_id, logs = intelligent_search_logic(
                current_user, image_path, ocr_text, force_new_analysis=False
            )
            
            if analysis:
                st.session_state.search_results = {
                    'analysis': analysis,
                    'ocr_text': ocr_text,
                    'cache_status': cache_status,
                    'question_id': question_id,
                    'logs': logs
                }
                logger.info(f"AI分析完成，缓存状态: {cache_status}")
                st.success("✅ 分析完成！")
            else:
                st.error("❌ AI分析失败，请重试")
                logger.error("AI分析返回空结果")
                
    except Exception as e:
        logger.error(f"OCR分析过程中发生错误: {e}")
        st.error(f"分析失败: {str(e)}")

def _force_reanalyze(current_user):
    """强制重新分析"""
    if not st.session_state.uploaded_image_path:
        st.error("没有找到图片，请重新上传")
        return
    
    logger.info(f"用户 {current_user['id']} 请求强制重新分析")
    
    with st.spinner("🔄 正在重新分析..."):
        try:
            # 重新获取OCR文本
            ocr_result = ocr_service.get_text_from_image(st.session_state.uploaded_image_path)
            ocr_text = '\n'.join(ocr_result) if ocr_result else ""
            
            # 强制重新分析
            from apps.app_v2 import intelligent_search_logic
            
            analysis, _, cache_status, question_id, logs = intelligent_search_logic(
                current_user, st.session_state.uploaded_image_path, ocr_text, force_new_analysis=True
            )
            
            if analysis:
                st.session_state.search_results = {
                    'analysis': analysis,
                    'ocr_text': ocr_text,
                    'cache_status': cache_status,
                    'question_id': question_id,
                    'logs': logs
                }
                st.success("✅ 重新分析完成！")
                logger.info("强制重新分析完成")
            else:
                st.error("❌ 重新分析失败")
                logger.error("强制重新分析失败")
                
        except Exception as e:
            logger.error(f"强制重新分析时发生错误: {e}")
            st.error(f"重新分析失败: {str(e)}")

def _render_analysis_results():
    """渲染分析结果"""
    results = st.session_state.search_results
    if not results:
        return
    
    analysis = results['analysis']
    ocr_text = results['ocr_text']
    cache_status = results['cache_status']
    
    st.markdown("---")
    st.subheader("📋 识别结果")
    
    # 显示缓存状态
    if cache_status == "cache_hit":
        st.success("⚡ 缓存命中！从知识库中快速获取结果")
    else:
        st.info("✨ 全新题目！已添加到知识库")
    
    # 显示识别的文字
    with st.expander("📝 识别的文字内容", expanded=True):
        st.text_area("", value=ocr_text, height=100, disabled=True)
    
    # 显示AI分析结果
    st.subheader("🤖 AI分析结果")
    
    # 正确性判断
    if analysis.get('is_correct'):
        st.success("### ✅ 恭喜！答案正确")
    else:
        st.error("### ❌ 答案需要改进")
        
        if analysis.get('error_analysis'):
            st.markdown(f"**错误分析：** {analysis['error_analysis']}")
        
        if analysis.get('correct_answer'):
            st.markdown(f"**正确答案：** `{analysis['correct_answer']}`")
    
    # 详细分析
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("📚 解题步骤", expanded=True):
            st.markdown(analysis.get('solution_steps', '暂无解题步骤'))
    
    with col2:
        with st.expander("🧠 知识点分析", expanded=True):
            st.markdown(f"**核心知识点：** {analysis.get('knowledge_point', '未识别')}")
            
            if analysis.get('common_mistakes'):
                st.markdown(f"**常见易错点：** {analysis.get('common_mistakes')}")
    
    # 调试信息（可选显示）
    if st.checkbox("🔍 显示详细日志", value=False):
        with st.expander("调试日志"):
            for log in results.get('logs', []):
                st.text(log)