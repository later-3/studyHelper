"""
StudyHelper 主应用 v2.0
集成角色化仪表盘的用户体验升级版本
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
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import logger_config

from typing import List, Dict
from datetime import datetime
import pandas as pd
from components.ui_components import (
    render_stats_overview, render_subject_distribution_chart, 
    render_activity_trend_chart, render_filter_panel,
    render_question_group_card, render_loading_spinner, render_empty_state, COLORS
)

# --- 导入角色仪表盘组件 ---
from components.student_dashboard import StudentDashboard
from components.teacher_dashboard import TeacherDashboard
from components.grade_manager_dashboard import GradeManagerDashboard
from components.principal_dashboard import PrincipalDashboard

# --- 初始化日志 ---
logger_config.setup_logging()
logger = logging.getLogger(__name__)

# --- 只从服务层导入 --- 
from services import storage_service, ocr_service, llm_service
from services.data_service import data_service
from core import user_management_v2 as um

def load_lottieurl(url: str):
    """加载Lottie动画"""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            logger.warning(f"Failed to fetch lottie animation from {url}, status code: {r.status_code}")
            return None
        return r.json()
    except requests.exceptions.RequestException:
        logger.error(f"Could not load Lottie animation from {url}", exc_info=True)
        return None

# --- 核心业务逻辑 (可被独立测试) ---
def intelligent_search_logic(user: dict, image_path: str, force_new_analysis: bool = False):
    """智能搜题核心逻辑"""
    logger.info(f"Starting intelligent_search_logic for user {user['id']}. Image path: {image_path}, Force new: {force_new_analysis}")
    
    # 首先进行OCR识别
    logger.info("Starting OCR process...")
    ocr_text_list = ocr_service.get_text_from_image(image_path)
    logger.info(f"OCR识别结果: {ocr_text_list}")
    ocr_text = '\n'.join(ocr_text_list)
    logger.info(f"OCR识别出的文字如下: {ocr_text}")
    
    # 检查OCR结果是否有效
    if not ocr_text.strip() or ocr_text_list[0] in ["识别失败", "识别异常"]:
        logger.error(f"OCR failed for image: {image_path}, result: {ocr_text}")
        return None, "文字识别失败或图片为空，请确保图片清晰。", None, None
    
    logger.info(f"OCR successful, text: {ocr_text[:100]}...")
    
    # 如果不是强制重新分析，尝试从缓存获取
    if not force_new_analysis:
        # L1缓存：通过图片phash查找
        existing_question = storage_service.get_question_by_phash(image_path)
        if existing_question and existing_question.get('master_analysis'):
            logger.info(f"L1 Cache HIT. Question ID: {existing_question['question_id']}")
            storage_service.save_submission(user['id'], existing_question['question_id'], "(Image match)")
            # 返回新OCR的结果，而不是历史数据中的canonical_text
            return existing_question['master_analysis'], ocr_text, "phash_hit", existing_question['question_id']
        
        # L2缓存：通过文本hash查找
        question_id_from_text = storage_service.generate_question_id(ocr_text)
        existing_question = storage_service.get_question_by_id(question_id_from_text)
        if existing_question and existing_question.get('master_analysis'):
            logger.info(f"L2 Cache HIT based on text hash. Question ID: {question_id_from_text}")
            # 将新图片的phash关联到现有问题
            storage_service.add_question(ocr_text, existing_question['master_analysis'], image_path, question_id_from_text)
            storage_service.save_submission(user['id'], question_id_from_text, ocr_text)
            return existing_question['master_analysis'], ocr_text, "text_hash_hit", question_id_from_text

    # 缓存未命中或强制重新分析，调用大模型
    question_id_from_text = storage_service.generate_question_id(ocr_text)
    logger.info(f"Cache MISS or force new analysis. Calling LLM service for Question ID: {question_id_from_text}")
    
    analysis_str = llm_service.get_analysis_for_text(ocr_text)
    match = re.search(r'```json\n({[\s\S]*?})\n```', analysis_str)
    try:
        master_analysis = json.loads(match.group(1) if match else analysis_str)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM JSON response: {analysis_str}", exc_info=True)
        return None, f"AI分析结果解析失败: {analysis_str}", None, None
    
    # 保存新的分析结果
    success = storage_service.add_question(ocr_text, master_analysis, image_path, question_id_from_text)
    if success:
        storage_service.save_submission(user['id'], question_id_from_text, ocr_text)
        logger.info(f"Successfully added new question to bank: {question_id_from_text}")
        cache_status = "miss"
    else:
        logger.error(f"Failed to save question data: {question_id_from_text}")
        return None, "保存分析结果失败，请重试。", None, None
        
    return master_analysis, ocr_text, cache_status, question_id_from_text

# --- UI 渲染函数 ---
def render_analysis_results(master_analysis, user, question_id, ocr_text):
    """渲染AI分析结果"""
    st.subheader("💡 AI分析结果")
    if master_analysis.get("is_correct"):
        st.success("### 恭喜你，答对了！🎉")
    else:
        st.error("### 别灰心，我们来看看问题出在哪？🤔")
        if master_analysis.get("error_analysis"): st.markdown(f"**错误分析:** {master_analysis['error_analysis']}")
        if master_analysis.get("correct_answer"): st.markdown(f"**正确答案:** `{master_analysis['correct_answer']}`")
    
    past_submissions = storage_service.get_submissions_by_question(user['id'], question_id)
    if len(past_submissions) > 1:
        st.warning("⚠️ 您以前也做过这道题哦！")
        for i, sub in enumerate(past_submissions[1:], 1):
            st.write(f"> 第{i}次提交于: {sub['timestamp']}, 当时提交的内容是: `{sub['submitted_ocr_text']}`")

    st.markdown("---")
    with st.expander("✅ 解题步骤", expanded=True): st.info(master_analysis.get("solution_steps", "暂无提供"))
    with st.expander("🧠 核心知识点"): st.success(master_analysis.get("knowledge_point", "暂无提供"))
    with st.expander("⚠️ 常见易错点"): st.warning(master_analysis.get("common_mistakes", "暂无提供"))

def intelligent_search_page():
    """智能搜题页面"""
    st.title("🧠 智能搜题")
    st.markdown("上传题目照片，AI导师将为您提供独家分析。如果题目已在我们的知识库中，您将直接获得秒级响应！")

    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None

    uploaded_file = st.file_uploader("支持 jpg, png, jpeg 格式的图片", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None and uploaded_file.file_id != st.session_state.get('current_file_id'):
        st.session_state.current_file_id = uploaded_file.file_id
        st.session_state.analysis_results = None
        logger.info(f"New file uploaded: {uploaded_file.name}, File ID: {uploaded_file.file_id}")
        
        user = st.session_state.current_user
        if not user: st.error("发生错误：无法获取当前用户信息，请重新登录。"); return

        submission_dir = f"data/submissions/{user['id']}"
        os.makedirs(submission_dir, exist_ok=True)
        image_path = os.path.join(submission_dir, f"{uuid.uuid4().hex[:12]}.png")
        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logger.info(f"Image saved to persistent path: {image_path}")

        with st.spinner("🤖 AI导师正在分析中...（首次分析可能需要一些时间）"):
            master_analysis, ocr_text, cache_status, question_id = intelligent_search_logic(user, image_path)
        
        st.session_state.analysis_results = {
            "master_analysis": master_analysis,
            "ocr_text": ocr_text,
            "cache_status": cache_status,
            "question_id": question_id,
            "image_path": image_path
        }

    if st.session_state.analysis_results:
        res = st.session_state.analysis_results
        master_analysis = res['master_analysis']
        ocr_text = res['ocr_text']
        cache_status = res['cache_status']
        question_id = res['question_id']
        image_path = res['image_path']
        user = st.session_state.current_user

        if not master_analysis:
            st.error(ocr_text)
            return

        col1, col2 = st.columns(2)
        with col1: st.image(image_path, caption="您上传的题目", use_container_width=True)
        with col2:
            if cache_status == 'phash_hit':
                st.success("⚡️ 图片已识别！我们以前见过这张图。")
                st.info("直接为您展示历史分析结果。")
            elif cache_status == 'text_hash_hit':
                st.success("⚡️ 题目内容已识别！")
                st.info("虽然图片是新的，但我们做过这道题。")
            else:
                st.info("✨ 全新题目！已为您永久存入知识库！")
            
            st.text_area("识别出的文字如下：", ocr_text, height=100)
            logger.info(f"识别出的文字如下：{ocr_text}")

        if st.button("强制使用大模型重新分析", help="如果您认为AI的分析结果不够理想，可以强制使用大模型进行一次全新的分析"):
            with st.spinner("🤖 正在强制调用大模型...请稍候"):
                master_analysis, ocr_text, cache_status, question_id = intelligent_search_logic(user, image_path, force_new_analysis=True)
            st.session_state.analysis_results['master_analysis'] = master_analysis
            st.success("✅ 已获取最新的AI分析结果！")
            st.rerun()

        render_analysis_results(master_analysis, user, question_id, ocr_text)

def home():
    """首页"""
    st.title("🏠 StudyHelper 智能学习助手")
    
    # 加载动画
    lottie_url = "https://assets5.lottiefiles.com/packages/lf20_xyadoh9h.json"
    lottie_json = load_lottieurl(lottie_url)
    
    if lottie_json:
        col1, col2 = st.columns([1, 2])
        with col1:
            st_lottie(lottie_json, height=300, key="home_animation")
        with col2:
            st.markdown("""
            ## 🎯 欢迎使用 StudyHelper！
            
            **StudyHelper** 是一款基于AI的智能学习助手，旨在为学生、教师和管理者提供全方位的教育支持。
            
            ### ✨ 核心功能
            - 🧠 **智能搜题**: AI分析题目，提供详细解答
            - 📊 **学习分析**: 深度分析学习数据，发现薄弱环节
            - 👥 **角色管理**: 支持学生、教师、年级主任、校长多角色
            - 📈 **进度跟踪**: 实时监控学习进度和表现
            
            ### 🎓 适用人群
            - **学生**: 智能解题、错题管理、学习建议
            - **教师**: 班级管理、学生分析、教学指导
            - **年级主任**: 年级管理、教师评估、数据分析
            - **校长**: 学校管理、战略决策、整体规划
            """)
    else:
        st.markdown("""
        ## 🎯 欢迎使用 StudyHelper！
        
        **StudyHelper** 是一款基于AI的智能学习助手，旨在为学生、教师和管理者提供全方位的教育支持。
        """)

def submission_history_page():
    """答题历史页面"""
    st.title("📚 答题历史")
    user = st.session_state.current_user
    if not user: st.warning("请先登录以查看此页面。"); return

    # 获取用户提交历史
    submissions = storage_service.get_submissions_by_user(user['id'])
    if not submissions:
        st.info("您还没有提交过任何题目。")
        return

    # 视图选择
    view_options = ["分组视图", "时间线视图", "统计视图"]
    selected_view = st.radio("选择查看方式", view_options, horizontal=True)

    if selected_view == "分组视图":
        render_grouped_view(submissions)
    elif selected_view == "时间线视图":
        render_timeline_view(submissions)
    else:
        render_stats_view(submissions)

def render_grouped_view(submissions: List[Dict]):
    """渲染分组视图"""
    st.subheader("📊 分组视图")
    
    # 获取详细统计
    stats = data_service.get_submission_stats(submissions)
    
    # 显示概览统计
    render_stats_overview(stats)
    
    # 学科分布图表
    if stats['subject_distribution']:
        render_subject_distribution_chart(stats['subject_distribution'])
    
    # 活动趋势图表
    if stats['recent_activity']:
        render_activity_trend_chart(stats['recent_activity'])
    
    # 按学科分组显示题目
    if stats['subject_distribution']:
        for subject in stats['subject_distribution'].keys():
            subject_submissions = [s for s in submissions if 
                                 (s.get('ai_analysis', {}).get('subject') == subject) or
                                 (data_service.get_question_details(s.get('question_id', '')) or {}).get('subject') == subject]
            
            if subject_submissions:
                render_question_group_card(subject, subject_submissions)

def render_timeline_view(submissions: List[Dict]):
    """渲染时间线视图"""
    st.subheader("⏰ 时间线视图")
    
    # 按时间排序
    sorted_submissions = sorted(submissions, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    for submission in sorted_submissions:
        # 获取题目详情
        question_details = data_service.get_question_details(submission.get('question_id', ''))
        ai_analysis = submission.get('ai_analysis', {})
        
        # 确定学科
        subject = (ai_analysis.get('subject') or 
                  question_details.get('subject') or 
                  "未知学科")
        
        # 确定是否正确
        is_correct = (ai_analysis.get('is_correct') or 
                     question_details.get('master_analysis', {}).get('is_correct'))
        
        # 获取题目文本
        q_text = (submission.get('submitted_ocr_text', '') or 
                 question_details.get('canonical_text', '') or 
                 "题目内容未知")
        
        # 格式化时间
        timestamp = submission.get('timestamp', '')
        if timestamp:
            try:
                date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = date.strftime('%H:%M')
            except:
                time_str = timestamp
        else:
            time_str = '未知时间'
        
        # 状态图标
        status_icon = "✅" if is_correct is True else "❌" if is_correct is False else "❓"
        
        # 显示信息
        col1, col2, col3, col4 = st.columns([1, 1, 2, 6])
        with col1:
            st.write(time_str)
        with col2:
            st.write(status_icon)
        with col3:
            st.write(f"**{subject}**")
        with col4:
            st.write(q_text[:50] + "..." if len(q_text) > 50 else q_text)
        
        st.divider()

def render_stats_view(submissions: List[Dict]):
    """渲染统计视图"""
    st.subheader("📊 详细统计")
    
    # 获取详细统计
    stats = data_service.get_submission_stats(submissions)
    
    # 学科详细统计
    st.write("### 学科表现")
    if stats['subject_distribution']:
        subject_data = []
        for subject, count in stats['subject_distribution'].items():
            # 计算该学科的正确率
            subject_submissions = [s for s in submissions if 
                                 (s.get('ai_analysis', {}).get('subject') == subject) or
                                 (data_service.get_question_details(s.get('question_id', '')) or {}).get('subject') == subject]
            
            correct_count = sum(1 for s in subject_submissions if 
                              (s.get('ai_analysis', {}).get('is_correct') is True) or
                              (data_service.get_question_details(s.get('question_id', '')) or {}).get('master_analysis', {}).get('is_correct') is True)
            
            accuracy = (correct_count / count * 100) if count > 0 else 0
            subject_data.append({
                '学科': subject,
                '题数': count,
                '正确数': correct_count,
                '正确率': f"{accuracy:.1f}%"
            })
        
        # 显示表格
        df = pd.DataFrame(subject_data)
        st.dataframe(df, use_container_width=True)
    
    # 最近活动详细统计
    st.write("### 最近活动")
    if stats['recent_activity']:
        activity_data = []
        for date, count in sorted(stats['recent_activity'].items()):
            activity_data.append({
                '日期': date,
                '提交次数': count
            })
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True)

def about():
    """关于页面"""
    st.title("ℹ️ 关于 StudyHelper")
    st.info(
        """
        **版本:** 2.0.0 (角色化用户体验升级版)
        **项目愿景:** 打造一款懂你的智能学习助手。
        
        ### 🆕 新功能
        - 角色化仪表盘：学生、教师、年级主任、校长专属界面
        - 智能数据分析：基于角色的个性化数据展示
        - 用户体验优化：简洁美观的界面设计
        
        ### 🎯 技术特色
        - AI驱动的智能分析
        - 模块化组件设计
        - 完整的测试覆盖
        - 响应式用户界面
        """
    )

def role_dashboard_page():
    """角色仪表盘页面"""
    user = st.session_state.current_user
    if not user: 
        st.warning("请先登录以查看此页面。")
        return
    
    # 根据用户角色显示对应的仪表盘
    role = user['role']
    
    if role == 'student':
        st.title("🎓 学生仪表盘")
        student_dashboard = StudentDashboard()
        student_dashboard.render_student_dashboard(user['id'])
        
    elif role == 'teacher':
        st.title("👨‍🏫 教师仪表盘")
        teacher_dashboard = TeacherDashboard()
        teacher_dashboard.render_teacher_dashboard(user['id'])
        
    elif role == 'grade_manager':
        st.title("👨‍💼 年级主任仪表盘")
        grade_manager_dashboard = GradeManagerDashboard()
        grade_manager_dashboard.render_grade_manager_dashboard(user['id'])
        
    elif role == 'principal':
        st.title("🏫 校长仪表盘")
        principal_dashboard = PrincipalDashboard()
        principal_dashboard.render_principal_dashboard(user['id'])
        
    else:
        st.error(f"未知的用户角色: {role}")

# --- 主程序 ---
load_dotenv("/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/.env")
st.set_page_config(page_title="StudyHelper v2.0", page_icon="📘", layout="wide")

if 'current_user' not in st.session_state: 
    st.session_state.current_user = None

with st.sidebar:
    if st.session_state.current_user:
        user = st.session_state.current_user
        role_icon = {
            "student": "🎓", 
            "teacher": "👨‍🏫", 
            "grade_manager": "📊", 
            "principal": "🏫"
        }
        
        # 用户信息卡片
        st.markdown(f"### {role_icon.get(user['role'], '👤')} {user['name']}")
        st.markdown(f"**角色**: {user['role']}")
        st.markdown("---")
        
        if st.button("退出登录", use_container_width=True, type="primary"): 
            st.session_state.current_file_id = None
            st.session_state.analysis_results = None
            st.session_state.current_user = None
            st.rerun()
    else:
        st.info("请选择用户登录")
        users = um.get_all_users()
        user_options = {user['id']: f"{user['name']} ({user['role']})" for user in users}
        selected_user_id = st.selectbox("选择用户", options=list(user_options.keys()), format_func=lambda x: user_options[x], index=None, placeholder="请选择...")
        if st.button("登录", use_container_width=True):
            if selected_user_id: 
                st.session_state.current_user = um.get_user_by_id(selected_user_id)
                st.session_state.analysis_results = None
                st.rerun()
            else: 
                st.warning("请先选择一个用户")
        st.markdown("---")

    # 动态菜单选项
    options = ["首页", "关于"]
    icons = ["house", "info-circle"]
    
    if st.session_state.current_user:
        # 添加角色仪表盘
        options.insert(1, "仪表盘")
        icons.insert(1, "speedometer")
        
        # 根据角色添加功能选项
        if st.session_state.current_user['role'] in ['student', 'teacher', 'grade_manager', 'principal']:
            options.insert(2, "答题历史")
            icons.insert(2, "card-checklist")
        
        if st.session_state.current_user['role'] in ['student', 'teacher']:
            options.insert(2, "智能搜题")
            icons.insert(2, "search")

    selected = option_menu(
        menu_title="StudyHelper v2.0", 
        options=options, 
        icons=icons, 
        menu_icon="book", 
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "18px"}, 
            "nav-link": {"color": "#333333", "font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )

# 页面路由
if selected == "首页": 
    home()
elif selected == "仪表盘": 
    role_dashboard_page()
elif selected == "智能搜题":
    if st.session_state.current_user: 
        intelligent_search_page()
    else: 
        st.warning("请从侧边栏登录以使用此功能。")
elif selected == "答题历史":
    if st.session_state.current_user: 
        submission_history_page()
    else: 
        st.warning("请从侧边栏登录以使用此功能。")
elif selected == "关于": 
    about() 