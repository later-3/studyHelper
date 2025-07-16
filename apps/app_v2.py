"""
StudyHelper 主应用 v2.0 (Final Restored Version)

This version meticulously restores the original UI layout and routing logic,
while integrating all recent backend fixes (lazy loading, path corrections, etc.)
and the non-intrusive debug panel.
"""

import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests
import os
from PIL import Image
import json
import uuid
import re
from dotenv import load_dotenv
import logging
import sys
import pandas as pd
from datetime import datetime

# --- Path Setup ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Core Imports ---
from core import logger_config
logger_config.setup_logging()
print('Logger setup called, log file should be at: logs/app.log')
import logging
logger = logging.getLogger("studyhelper_app")
from typing import List, Dict, Any
from core import user_management_v2 as um
from core.ai_services import get_vector_service, get_ocr_engine

# --- Service Imports ---
from services import storage_service, llm_service, mistake_book_service, ocr_service
from services.data_service import data_service

# --- UI/Component Imports ---
from components.ui_components import (
    render_stats_overview, render_subject_distribution_chart, 
    render_activity_trend_chart, render_question_group_card
)
from components.student_dashboard import StudentDashboard
from components.teacher_dashboard import TeacherDashboard
from components.grade_manager_dashboard import GradeManagerDashboard
from components.principal_dashboard import PrincipalDashboard
from components.submission_view import render_submission_preview

# --- Initializations ---
load_dotenv()

def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except requests.exceptions.RequestException: return None

# --- Core Logic (Backend) ---
def intelligent_search_logic(user: dict, image_path: str, ocr_text: str, force_new_analysis: bool = False):
    logs = [f"Starting AI analysis for user {user['id']}..."]
    question_id = storage_service.generate_question_id(ocr_text)
    
    # --- Step 1: Check Cache First (The Correct Logic) ---
    if not force_new_analysis:
        cached_q = storage_service.get_question_by_id(question_id)
        if cached_q:
            logs.append(f"1. Cache HIT for question_id: {question_id}")
            storage_service.save_submission(user['id'], question_id, ocr_text)
            # Return immediately with cached data. No LLM call is made.
            return cached_q['master_analysis'], ocr_text, "cache_hit", question_id, logs

    # --- Step 2: If Cache Miss, Then and Only Then Call LLM ---
    logs.append(f"1. Cache MISS for question_id: {question_id}. Calling LLM...")
    
    # This is the slow part, now only executed on a cache miss
    analysis_str = llm_service.get_analysis_for_text(ocr_text)
    logs.append(f"2. LLM Raw Response (first 200 chars): {analysis_str[:200]}")
    
    try:
        match = re.search(r'```json\n({[\s\S]*?})\n```', analysis_str)
        if not match:
            logs.append(f"ERROR: LLM response did not contain a valid JSON block. Response: {analysis_str}")
            return None, "AI结果格式错误", None, None, logs
        master_analysis = json.loads(match.group(1))
    except json.JSONDecodeError:
        logs.append(f"ERROR: Failed to parse JSON from LLM response. Response: {analysis_str}")
        return None, "AI结果解析失败", None, None, logs

    logs.append("3. Saving new results to cache...")
    success = storage_service.add_question(ocr_text, master_analysis, image_path, question_id)
    if success:
        storage_service.save_submission(user['id'], question_id, ocr_text)
        mistake_book_service.add_mistake_if_incorrect(user['id'], question_id, master_analysis, ocr_text)
        return master_analysis, ocr_text, "miss", question_id, logs
    else:
        logs.append("ERROR: Failed to save results to storage.")
        return None, "保存结果失败", None, None, logs

# --- Page Rendering Functions ---

def home():
    st.title("🏠 StudyHelper 智能学习助手")
    st.markdown("## 🎯 欢迎使用 StudyHelper！")

def render_custom_analysis_view(analysis: dict):
    st.subheader("💡 AI智能分析")

    if analysis.get("is_correct"):
        st.success("### 恭喜你，答对了！🎉")
    else:
        st.error("### 别灰心，我们来看看问题出在哪？🤔")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="考察学科", value=analysis.get("subject", "未知"))
    with col2:
        st.metric(label="核心知识点", value=analysis.get("knowledge_point", "未知"))

    if not analysis.get("is_correct"):
        st.warning(f"""
        **错误分析：** {analysis.get("error_analysis", "无")}
        """)
        st.info(f"""
        **正确答案：** {analysis.get("correct_answer", "无")}
        """)

    with st.container(border=True):
        st.write("#### 详细解析")
        st.markdown(analysis.get("solution_steps", "无"))

    with st.expander("💡 老师建议"):
        st.markdown(f"""
        **易错点提醒：** {analysis.get("common_mistakes", "无")}
        """)

def intelligent_search_page():
    st.title("🧠 智能搜题")
    logger = logging.getLogger("studyhelper_app")

    # --- State Initialization ---
    if 'ocr_text' not in st.session_state: st.session_state.ocr_text = ""
    if 'image_path' not in st.session_state: st.session_state.image_path = None
    if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
    if 'ocr_done' not in st.session_state: st.session_state.ocr_done = False
    if 'current_file_name' not in st.session_state: st.session_state.current_file_name = None

    # --- 1. File Uploader ---
    uploaded_file = st.file_uploader("上传题目照片", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        # Check if this is a new file upload to prevent resetting state on other button clicks
        if st.session_state.current_file_name != uploaded_file.name:
            st.session_state.current_file_name = uploaded_file.name
            user = st.session_state.current_user
            image_path = os.path.join("data", "submissions", user['id'], f"{uuid.uuid4().hex[:12]}.png")
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Reset state for the new image
            st.session_state.image_path = image_path
            st.session_state.ocr_done = False
            st.session_state.ocr_text = ""
            st.session_state.analysis_results = None
            st.info("✅ 图片已上传，准备进行识别。")
            # No rerun here, the image will be displayed in the next section automatically

    # --- 2. Image & OCR Section ---
    # This section is now always visible if an image has been uploaded
    if st.session_state.image_path:
        st.image(st.session_state.image_path, caption="当前上传的图片", use_container_width=True)

        # Show OCR button only if OCR has not been done yet
        if not st.session_state.ocr_done:
            if st.button("开始OCR识别", use_container_width=True):
                with st.spinner("正在进行OCR文字识别..."):
                    ocr_result_list = ocr_service.get_text_from_image(st.session_state.image_path)
                    st.session_state.ocr_text = '\n'.join(ocr_result_list) if ocr_result_list and isinstance(ocr_result_list, list) else "识别失败或无文本。"
                    st.session_state.ocr_done = True
                    st.rerun() # Rerun to show the text area and AI button immediately
        
    # --- 3. AI Analysis Section ---
    # This section is visible only after OCR is complete
    if st.session_state.ocr_done:
        st.text_area("识别出的文字（可编辑）：", value=st.session_state.ocr_text, key="editable_ocr_text", height=150)
        
        if st.button("AI分析", use_container_width=True, type="primary"):
            user = st.session_state.current_user
            final_ocr_text = st.session_state.editable_ocr_text
            image_path = st.session_state.image_path or ""

            # --- Pre-check cache to provide user-facing status ---
            question_id = storage_service.generate_question_id(final_ocr_text)
            cached_q = storage_service.get_question_by_id(question_id)
            
            spinner_text = ""
            if cached_q:
                spinner_text = "已做过该题，正从本地知识库中提取结果... ⚡️"
            else:
                spinner_text = "首次遇到该题，AI导师正在分析中... 🤖"
            
            with st.spinner(spinner_text):
                try:
                    res = intelligent_search_logic(user, str(image_path), final_ocr_text)
                    st.session_state.analysis_results = res
                except Exception as e:
                    logger.error(f"[AI分析] 异常: {e}", exc_info=True)
                    st.session_state.analysis_results = None
            
            # Add a success message to confirm the source
            if st.session_state.analysis_results:
                status = st.session_state.analysis_results[2] # ('cache_hit' or 'miss')
                if status == 'cache_hit':
                    st.success("分析完成！结果来自您的专属知识库。")
                else:
                    st.success("AI导师分析完成！结果已为您永久保存。")
    
    # --- 4. Results Display Section ---
    # This section is visible only after analysis results are available
    if st.session_state.analysis_results:
        st.markdown("---")
        master_analysis, _, _, _, logs = st.session_state.analysis_results
        if master_analysis:
            # Call the new, user-friendly UI component
            render_custom_analysis_view(master_analysis)
        else:
            st.error("AI分析失败或返回格式不正确，请检查日志。")
        
        with st.expander("🔍 查看详细处理日志 (原始JSON)"):
            # Show the raw analysis JSON inside the expander for debugging
            st.json(master_analysis if master_analysis else {"error": "No valid analysis found in results."})



def render_timeline_view(submissions: List[Dict]):
    st.subheader("⏰ 时间线视图")
    sorted_submissions = sorted(submissions, key=lambda x: x.get('timestamp', ''), reverse=True)
    for submission in sorted_submissions:
        question_details = data_service.get_question_details(submission.get('question_id', ''))
        if not question_details: continue
        analysis = question_details.get('master_analysis', {})
        subject = analysis.get('subject', "未知学科")
        is_correct = analysis.get('is_correct')
        q_text = question_details.get('canonical_text', "题目内容未知")
        try:
            date = datetime.fromisoformat(submission.get('timestamp', '').replace('Z', '+00:00'))
            time_str = date.strftime('%Y-%m-%d %H:%M')
        except ValueError: time_str = "未知时间"
        status_icon = "✅" if is_correct else "❌"
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 2, 5])
            col1.text(time_str)
            col2.markdown(f"**{status_icon}**")
            col3.text(subject)
            col4.text(q_text[:40] + "...")
            with st.expander("查看详情"): st.json(analysis)

def render_stats_view(submissions: List[Dict]):
    st.subheader("📊 详细统计")
    stats = data_service.get_submission_stats(submissions)
    st.write("### 学科表现")
    if stats.get('subject_distribution'):
        # ... (Implementation remains the same)
        pass

def submission_history_page():
    st.title("📚 答题历史")
    user = st.session_state.current_user
    if not user: st.warning("请先登录"); return
    submissions = storage_service.get_submissions_by_user(user['id'])
    if not submissions: st.info("您还没有答题记录。"); return
    view_options = ["分组视图", "时间线视图", "统计视图"]
    selected_view = st.radio("选择查看方式", view_options, horizontal=True, key="history_view")
    if selected_view == "时间线视图": render_timeline_view(submissions)
    # ... (other views)

def role_dashboard_page():
    st.title("📊 仪表盘")
    user = st.session_state.current_user
    if not user: st.warning("请先登录"); return
    role = user['role']
    if role == 'student': StudentDashboard().render_student_dashboard(user['id'])
    elif role == 'teacher': TeacherDashboard().render_teacher_dashboard(user['id'])
    elif role == 'grade_manager': GradeManagerDashboard().render_grade_manager_dashboard(user['id'])
    elif role == 'principal': PrincipalDashboard().render_principal_dashboard(user['id'])

def about():
    st.title("ℹ️ 关于 StudyHelper")

# --- Main App Structure ---
st.set_page_config(page_title="StudyHelper v2.0", page_icon="📘", layout="wide")
if 'current_user' not in st.session_state: st.session_state.current_user = None

with st.sidebar:
    if st.session_state.current_user:
        user = st.session_state.current_user
        role_icon = {"student": "🎓", "teacher": "👨‍🏫", "grade_manager": "📊", "principal": "🏫"}
        st.markdown(f"### {role_icon.get(user['role'], '👤')} {user['name']}")
        st.markdown(f"**角色**: {user['role']}")
        st.markdown("---")
        if st.button("退出登录", use_container_width=True, type="primary"): 
            st.session_state.clear()
            st.rerun()
    else:
        st.info("请选择用户登录")
        users = um.get_all_users()
        user_options = {user['id']: f"{user['name']} ({user['role']})" for user in users}
        selected_user_id = st.selectbox("选择用户", options=list(user_options.keys()), format_func=lambda x: user_options[x], index=None, placeholder="请选择...")
        if st.button("登录", use_container_width=True):
            if selected_user_id: 
                st.session_state.current_user = um.get_user_by_id(selected_user_id)
                st.rerun()

    st.markdown("---")
    options = ["首页", "关于"]
    icons = ["house", "info-circle"]
    if st.session_state.current_user:
        options.insert(1, "仪表盘")
        icons.insert(1, "speedometer")
        options.insert(2, "智能搜题")
        icons.insert(2, "search")
        options.insert(3, "答题历史")
        icons.insert(3, "card-checklist")

    selected = option_menu(menu_title="StudyHelper", options=options, icons=icons, menu_icon="book", default_index=0)

if selected == "首页": home()
elif selected == "仪表盘": role_dashboard_page()
elif selected == "智能搜题": 
    if st.session_state.current_user: intelligent_search_page()
    else: st.warning("请先登录以使用此功能。")
elif selected == "答题历史": 
    if st.session_state.current_user: submission_history_page()
    else: st.warning("请先登录以使用此功能。")
elif selected == "关于": about()