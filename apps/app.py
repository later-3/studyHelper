import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import json
import uuid
import re
from dotenv import load_dotenv
import logging
from core import logger_config
from streamlit_elements import elements, mui, html
from typing import List, Dict
from datetime import datetime
import pandas as pd
from components.ui_components import (
    render_stats_overview, render_subject_distribution_chart, 
    render_activity_trend_chart, render_filter_panel,
    render_question_group_card, render_loading_spinner, render_empty_state, COLORS
)

# --- 初始化日志 ---
logger_config.setup_logging()
logger = logging.getLogger(__name__)

# --- 只从服务层导入 --- 
from services import storage_service, ocr_service, llm_service
from services.data_service import data_service
from core import user_management as um

def load_lottieurl(url: str):
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

# ... (home, about, user_management_page, etc. remain the same)

def home():
    st.title("欢迎使用 StudyHelper 智能学习助手 👋")
    st.subheader("您身边的AI学习伙伴")
    lottie_url = "https://lottie.host/embed/a7b5c79a-18c7-4bb9-9a24-9aacb741b330/2Jp4k5t9kM.json"
    lottie_json = load_lottieurl(lottie_url)
    if lottie_json:
        st_lottie(lottie_json, speed=1, width=600, height=300, key="study_lottie")
    st.markdown(
        """
        **本应用致力于通过AI技术，帮助您更高效地学习：**
        - **`智能搜题`**: 上传题目图片，AI将为您提供详细的解题思路、知识点和易错点分析。
        - **`答题历史`**: 自动收录您分析过的所有题目，方便随时回顾复习。
        - **`举一反三`**: (即将推出) 根据您的问题，为您推荐同类型的练习题。

        👈 请从左侧导航栏选择功能开始使用！
        """
    )

def submission_history_page():
    """优化的答题历史页面"""
    st.title("📖 答题历史")
    
    user = st.session_state.current_user
    if not user:
        st.error("请先登录")
        return
    
    # 初始化session state
    if 'history_view_mode' not in st.session_state:
        st.session_state.history_view_mode = 'grouped'  # grouped, timeline, stats
    
    # 获取用户提交记录
    with st.spinner("加载数据中..."):
        submissions = data_service.get_user_submissions(user['id'], user['role'])
    
    if not submissions:
        render_empty_state("暂无答题记录", "📝")
        return
    
    # 获取统计信息
    stats = data_service.get_submission_stats(submissions)
    
    # 页面布局
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("📊 学习概览")
        render_stats_overview(stats)
    
    with col2:
        st.subheader("📈 学科分布")
        render_subject_distribution_chart(stats)
    
    with col3:
        st.subheader("📅 活动趋势")
        render_activity_trend_chart(stats)
    
    st.markdown("---")
    
    # 视图模式切换
    view_mode = st.radio(
        "查看模式",
        options=[
            ("grouped", "📚 按题目分组"),
            ("timeline", "⏰ 时间线"),
            ("stats", "📊 详细统计")
        ],
        format_func=lambda x: x[1],
        key="view_mode_radio"
    )
    st.session_state.history_view_mode = view_mode[0]
    
    # 筛选面板
    subjects = list(stats['subject_distribution'].keys())
    filter_params = render_filter_panel(subjects)
    
    # 应用筛选
    correctness_map = {"正确": True, "错误": False, "未知": None}
    correctness_values = [correctness_map.get(c) for c in filter_params['correctness']]
    filtered_submissions = data_service.search_submissions(
        user['id'], 
        user['role'],
        subjects=filter_params['subjects'],
        correctness=correctness_values,
        date_range=filter_params['date_range']
    )
    
    if not filtered_submissions:
        render_empty_state("没有找到符合筛选条件的记录", "🔍")
        return
    
    # 根据视图模式渲染内容
    if st.session_state.history_view_mode == 'grouped':
        render_grouped_view(filtered_submissions)
    elif st.session_state.history_view_mode == 'timeline':
        render_timeline_view(filtered_submissions)
    elif st.session_state.history_view_mode == 'stats':
        render_stats_view(filtered_submissions)

def render_grouped_view(submissions: List[Dict]):
    """渲染分组视图"""
    st.subheader("📚 按题目分组")
    
    # 按题目分组
    grouped_submissions = data_service.group_submissions_by_question(submissions)
    
    if not grouped_submissions:
        render_empty_state("暂无分组数据", "📚")
        return
    
    # 显示分组统计
    st.info(f"共找到 {len(grouped_submissions)} 道不同的题目")
    
    # 渲染每个题目组
    for question_id, question_submissions in grouped_submissions.items():
        # 获取题目详情
        question_details = data_service.get_question_details(question_id)
        
        # 渲染题目组卡片
        render_question_group_card(question_id, question_submissions, question_details)

def render_timeline_view(submissions: List[Dict]):
    """渲染时间线视图"""
    st.subheader("⏰ 时间线")
    
    # 按时间排序
    sorted_submissions = sorted(submissions, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # 按日期分组
    date_groups = {}
    for submission in sorted_submissions:
        timestamp = submission.get('timestamp', '')
        if timestamp:
            try:
                date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = date.strftime('%Y年%m月%d日')
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append(submission)
            except:
                continue
    
        # 渲染时间线
    for date_str, day_submissions in date_groups.items():
        st.write(f"### {date_str}")
        
        for submission in day_submissions:
            # 获取分析结果
            ai_analysis = submission.get('ai_analysis')
            if ai_analysis:
                subject = ai_analysis.get('subject', '未指定')
                is_correct = ai_analysis.get('is_correct')
                q_text = submission.get('ocr_text', submission.get('submitted_ocr_text', ''))
            else:
                question_id = submission.get('question_id')
                question = data_service.get_question_details(question_id)
                if question:
                    subject = question.get('subject', '未指定')
                    is_correct = question.get('master_analysis', {}).get('is_correct')
                    q_text = question.get('canonical_text', '')
                else:
                    subject = '未指定'
                    is_correct = None
                    q_text = submission.get('submitted_ocr_text', '')
            
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
                                 (data_service.get_question_details(s.get('question_id', {})) or {}).get('subject') == subject]
            
            correct_count = sum(1 for s in subject_submissions if 
                              (s.get('ai_analysis', {}).get('is_correct') is True) or
                              (data_service.get_question_details(s.get('question_id', {})) or {}).get('master_analysis', {}).get('is_correct') is True)
            
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
    st.title("ℹ️ 关于 StudyHelper")
    st.info(
        """
        **版本:** 7.1.0 (类型修复)
        **项目愿景:** 打造一款懂你的智能学习助手。
        """
    )

def user_management_page():
    st.title("👥 用户管理")
    user = st.session_state.current_user
    if not user: st.warning("请先登录以查看此页面。"); return

    st.markdown(f"#### 欢迎，{user['name']}!")

    with elements(f"user_dashboard_{user['id']}"):
        if user['role'] == 'school':
            st.subheader("🏫 学校仪表盘")
            all_teachers, all_students, all_classes = um.get_all_teachers(), um.get_all_students(), um.get_all_classes()
            with mui.Grid(container=True, spacing=2):
                with mui.Grid(item=True, xs=6):
                    with mui.Paper(elevation=3, sx={"padding": 2, "textAlign": 'center'}):
                        mui.Typography("👨‍🏫 教师总数", variant="h6")
                        mui.Typography(len(all_teachers), variant="h4")
                with mui.Grid(item=True, xs=6):
                    with mui.Paper(elevation=3, sx={"padding": 2, "textAlign": 'center'}):
                        mui.Typography("🎓 学生总数", variant="h6")
                        mui.Typography(len(all_students), variant="h4")
            
            for cls in all_classes:
                teacher_name = next((t['name'] for t in all_teachers if cls['id'] in t.get('manages_classes', [])), '暂无')
                with mui.Card(key=cls['id'], sx={"marginTop": 2}):
                    mui.CardHeader(title=cls['name'], subheader=f"班主任: {teacher_name}")
                    with mui.CardContent:
                        for student in um.get_students_by_class(cls['id']):
                            mui.Chip(label=student['name'], variant="outlined", sx={"marginRight": 0.5, "marginBottom": 0.5})

        elif user['role'] == 'teacher':
            st.subheader("👨‍🏫 我管理的班级")
            managed_classes = um.get_classes_by_teacher(user['id'])
            if not managed_classes: st.info("您目前没有管理任何班级。"); return
            for cls in managed_classes:
                with mui.Card(key=cls['id'], sx={"marginTop": 2}):
                    mui.CardHeader(title=cls['name'])
                    with mui.CardContent:
                        for student in um.get_students_by_class(cls['id']):
                            mui.Chip(label=student['name'], variant="outlined", sx={"marginRight": 0.5, "marginBottom": 0.5})

        elif user['role'] == 'student':
            st.subheader("🧑‍🎓 我的信息")
            class_id = user.get('class_id')
            all_classes = um.get_all_classes()
            class_name = next((c['name'] for c in all_classes if c['id'] == class_id), "未分配班级")
            teacher_name = "暂无"
            if class_id:
                all_teachers = um.get_all_teachers()
                teacher_name = next((t['name'] for t in all_teachers if class_id in t.get('manages_classes', [])), "暂无")
            with mui.Card(sx={"padding": 2}):
                mui.Typography(f"姓名: {user['name']}", variant="h6")
                mui.Typography(f"班级: {class_name}", variant="body1")
                mui.Typography(f"班主任: {teacher_name}", variant="body1")

# --- 主程序 ---
load_dotenv("/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/.env")
st.set_page_config(page_title="StudyHelper", page_icon="📘", layout="wide")

if 'current_user' not in st.session_state: st.session_state.current_user = None

with st.sidebar:
    if st.session_state.current_user:
        user = st.session_state.current_user
        role_icon = {"school": "🏫", "teacher": "👨‍🏫", "student": "🧑‍🎓"}
        with elements("sidebar_user_card"):
            with mui.Paper(elevation=3, sx={"padding": 1, "marginBottom": 1}):
                mui.Typography(f"{role_icon.get(user['role'], '👤')} {user['name']}", variant="h6")
                mui.Typography(f"角色: {user['role']}", variant="body2")
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
            else: st.warning("请先选择一个用户")
    st.markdown("---")

    options = ["首页", "关于"]
    icons = ["house-door-fill", "info-circle-fill"]
    if st.session_state.current_user:
        options.insert(1, "用户管理")
        icons.insert(1, "people-fill")
        if st.session_state.current_user['role'] in ['student', 'teacher', 'school']:
            options.insert(2, "答题历史")
            icons.insert(2, "card-checklist")
        if st.session_state.current_user['role'] in ['student', 'teacher']:
            options.insert(2, "智能搜题")
            icons.insert(2, "search-heart-fill")

    selected = option_menu(
        menu_title="StudyHelper", options=options, icons=icons, menu_icon="book-half", default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "25px"}, 
            "nav-link": {"color": "#333333", "font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )

# 页面路由
if selected == "首页": home()
elif selected == "用户管理": user_management_page()
elif selected == "智能搜题":
    if st.session_state.current_user: intelligent_search_page()
    else: st.warning("请从侧边栏登录以使用此功能。")
elif selected == "答题历史":
    if st.session_state.current_user: submission_history_page()
    else: st.warning("请从侧边栏登录以使用此功能。")
elif selected == "关于": about()