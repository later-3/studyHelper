"""
答题历史页面组件
显示用户的答题记录和统计分析
"""

import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

def render_history_page():
    """渲染答题历史页面"""
    logger.info("渲染答题历史页面")
    
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("请先登录以查看答题历史")
        return
    
    st.title("📖 答题历史")
    st.markdown(f"查看 **{current_user['name']}** 的学习记录")
    
    try:
        # 获取用户提交记录
        from services.data_service import data_service
        
        with st.spinner("📊 加载数据中..."):
            submissions = data_service.get_user_submissions(current_user['id'], current_user['role'])
            
        if not submissions:
            _render_empty_state()
            return
        
        # 获取统计信息
        stats = data_service.get_submission_stats(submissions)
        
        # 渲染统计概览
        _render_stats_overview(stats)
        
        # 渲染视图选择和内容
        _render_history_content(submissions, stats)
        
    except Exception as e:
        logger.error(f"加载答题历史时发生错误: {e}")
        st.error(f"数据加载失败: {str(e)}")
        
        if st.checkbox("显示错误详情"):
            st.exception(e)

def _render_empty_state():
    """渲染空状态"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>📝 暂无答题记录</h3>
            <p>开始使用智能搜题功能，记录您的学习历程吧！</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🧠 开始搜题", use_container_width=True, type="primary"):
            st.session_state.selected_page = "search"
            st.rerun()

def _render_stats_overview(stats):
    """渲染统计概览"""
    st.markdown("---")
    st.subheader("📊 学习概览")
    
    # 主要统计指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="总题数",
            value=stats.get('total_count', 0),
            help="您总共分析过的题目数量"
        )
    
    with col2:
        st.metric(
            label="正确题数", 
            value=stats.get('correct_count', 0),
            help="答对的题目数量"
        )
    
    with col3:
        st.metric(
            label="错误题数",
            value=stats.get('incorrect_count', 0),
            help="答错的题目数量"
        )
    
    with col4:
        accuracy = stats.get('accuracy_rate', 0)
        st.metric(
            label="正确率",
            value=f"{accuracy:.1f}%",
            help="正确题数占总题数的百分比"
        )
    
    # 图表展示
    col1, col2 = st.columns(2)
    
    with col1:
        _render_subject_chart(stats)
    
    with col2:
        _render_activity_chart(stats)

def _render_subject_chart(stats):
    """渲染学科分布图表"""
    subject_dist = stats.get('subject_distribution', {})
    
    if not subject_dist:
        st.info("📚 暂无学科分布数据")
        return
    
    try:
        import plotly.express as px
        
        # 准备数据
        subjects = list(subject_dist.keys())
        counts = list(subject_dist.values())
        
        # 创建饼图
        fig = px.pie(
            values=counts,
            names=subjects,
            title="📚 学科分布",
            color_discrete_sequence=['#1976D2', '#4CAF50', '#FF9800', '#F44336', '#9C27B0']
        )
        
        fig.update_layout(
            height=300,
            showlegend=True,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        # 如果plotly不可用，使用简单的文本显示
        st.markdown("**📚 学科分布：**")
        for subject, count in subject_dist.items():
            st.markdown(f"- {subject}: {count} 题")

def _render_activity_chart(stats):
    """渲染活动趋势图表"""
    activity_data = stats.get('recent_activity', {})
    
    if not activity_data:
        st.info("📅 暂无活动数据")
        return
    
    try:
        import plotly.express as px
        import pandas as pd
        
        # 准备数据
        dates = list(activity_data.keys())
        counts = list(activity_data.values())
        
        # 按日期排序
        date_count_pairs = sorted(zip(dates, counts), key=lambda x: x[0])
        dates, counts = zip(*date_count_pairs) if date_count_pairs else ([], [])
        
        if dates:
            df = pd.DataFrame({
                '日期': dates,
                '题目数': counts
            })
            
            fig = px.line(
                df,
                x='日期',
                y='题目数',
                title="📅 最近活动趋势",
                markers=True
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        # 如果plotly不可用，使用简单的文本显示
        st.markdown("**📅 最近活动：**")
        for date, count in sorted(activity_data.items()):
            st.markdown(f"- {date}: {count} 题")

def _render_history_content(submissions, stats):
    """渲染历史内容"""
    st.markdown("---")
    
    # 视图选择
    view_mode = st.radio(
        "查看方式",
        options=["📚 按题目分组", "⏰ 时间线", "📊 详细统计"],
        horizontal=True,
        key="history_view_mode"
    )
    
    # 筛选选项
    with st.expander("🔍 筛选选项"):
        _render_filter_options(stats)
    
    # 根据选择的视图模式渲染内容
    if view_mode == "📚 按题目分组":
        _render_grouped_view(submissions)
    elif view_mode == "⏰ 时间线":
        _render_timeline_view(submissions)
    elif view_mode == "📊 详细统计":
        _render_detailed_stats(submissions, stats)

def _render_filter_options(stats):
    """渲染筛选选项"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        subjects = list(stats.get('subject_distribution', {}).keys())
        if subjects:
            selected_subjects = st.multiselect(
                "学科筛选",
                options=subjects,
                default=subjects,
                key="subject_filter"
            )
    
    with col2:
        correctness_options = ["全部", "正确", "错误"]
        selected_correctness = st.selectbox(
            "正确性筛选",
            options=correctness_options,
            key="correctness_filter"
        )
    
    with col3:
        date_range = st.date_input(
            "日期范围",
            value=[],
            key="date_filter"
        )

def _render_grouped_view(submissions):
    """渲染分组视图"""
    st.subheader("📚 按题目分组")
    
    try:
        from services.data_service import data_service
        grouped = data_service.group_submissions_by_question(submissions)
        
        if not grouped:
            st.info("暂无分组数据")
            return
        
        st.info(f"共找到 {len(grouped)} 道不同的题目")
        
        for question_id, question_submissions in grouped.items():
            _render_question_group(question_id, question_submissions)
            
    except Exception as e:
        logger.error(f"渲染分组视图时发生错误: {e}")
        st.error("分组视图加载失败")

def _render_question_group(question_id, submissions):
    """渲染题目组"""
    if not submissions:
        return
    
    # 获取题目详情
    try:
        from services.data_service import data_service
        question_details = data_service.get_question_details(question_id)
        
        # 使用expander显示每个题目组
        latest_submission = submissions[0]  # 最新的提交
        
        # 获取题目信息
        if question_details:
            analysis = question_details.get('master_analysis', {})
            subject = analysis.get('subject', '未知')
            is_correct = analysis.get('is_correct')
            question_text = question_details.get('canonical_text', '')[:50] + "..."
        else:
            # 从提交记录中获取信息
            analysis = latest_submission.get('ai_analysis', {})
            subject = analysis.get('subject', '未知')
            is_correct = analysis.get('is_correct')
            question_text = latest_submission.get('ocr_text', '')[:50] + "..."
        
        # 状态图标
        status_icon = "✅" if is_correct else "❌" if is_correct is not None else "❓"
        
        with st.expander(f"{status_icon} {subject} - {question_text} (共{len(submissions)}次)"):
            # 显示分析结果
            if analysis:
                if is_correct:
                    st.success("答案正确")
                else:
                    st.error("答案错误")
                    if analysis.get('error_analysis'):
                        st.markdown(f"**错误分析：** {analysis['error_analysis']}")
                    if analysis.get('correct_answer'):
                        st.markdown(f"**正确答案：** {analysis['correct_answer']}")
            
            # 显示提交历史
            st.markdown("**提交历史：**")
            for i, submission in enumerate(submissions, 1):
                timestamp = submission.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        time_str = timestamp
                else:
                    time_str = "未知时间"
                
                st.markdown(f"第{i}次: {time_str}")
                
    except Exception as e:
        logger.error(f"渲染题目组时发生错误: {e}")
        st.error(f"题目组渲染失败: {str(e)}")

def _render_timeline_view(submissions):
    """渲染时间线视图"""
    st.subheader("⏰ 时间线")
    
    # 按时间排序
    sorted_submissions = sorted(
        submissions, 
        key=lambda x: x.get('timestamp', ''), 
        reverse=True
    )
    
    for submission in sorted_submissions:
        _render_timeline_item(submission)

def _render_timeline_item(submission):
    """渲染时间线项目"""
    try:
        # 获取基本信息
        timestamp = submission.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                time_str = timestamp
        else:
            time_str = "未知时间"
        
        # 获取分析信息
        analysis = submission.get('ai_analysis', {})
        if not analysis:
            # 尝试从题目详情获取
            question_id = submission.get('question_id')
            if question_id:
                from services.data_service import data_service
                question_details = data_service.get_question_details(question_id)
                if question_details:
                    analysis = question_details.get('master_analysis', {})
        
        subject = analysis.get('subject', '未知')
        is_correct = analysis.get('is_correct')
        question_text = submission.get('ocr_text', submission.get('submitted_ocr_text', ''))
        
        # 状态图标和颜色
        if is_correct is True:
            status_icon = "✅"
            status_color = "success"
        elif is_correct is False:
            status_icon = "❌"
            status_color = "error"
        else:
            status_icon = "❓"
            status_color = "info"
        
        # 显示时间线项目
        col1, col2, col3, col4 = st.columns([2, 1, 2, 5])
        
        with col1:
            st.text(time_str)
        
        with col2:
            if status_color == "success":
                st.success(status_icon)
            elif status_color == "error":
                st.error(status_icon)
            else:
                st.info(status_icon)
        
        with col3:
            st.markdown(f"**{subject}**")
        
        with col4:
            display_text = question_text[:50] + "..." if len(question_text) > 50 else question_text
            st.text(display_text)
        
        st.divider()
        
    except Exception as e:
        logger.error(f"渲染时间线项目时发生错误: {e}")
        st.error("时间线项目渲染失败")

def _render_detailed_stats(submissions, stats):
    """渲染详细统计"""
    st.subheader("📊 详细统计")
    
    # 学科详细统计
    st.markdown("### 📚 学科表现")
    
    subject_dist = stats.get('subject_distribution', {})
    if subject_dist:
        # 计算每个学科的详细统计
        subject_stats = []
        
        for subject, total_count in subject_dist.items():
            # 筛选该学科的提交
            subject_submissions = [
                s for s in submissions 
                if _get_submission_subject(s) == subject
            ]
            
            # 计算正确数
            correct_count = sum(
                1 for s in subject_submissions 
                if _get_submission_correctness(s) is True
            )
            
            accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
            
            subject_stats.append({
                '学科': subject,
                '总题数': total_count,
                '正确数': correct_count,
                '错误数': total_count - correct_count,
                '正确率': f"{accuracy:.1f}%"
            })
        
        # 显示表格
        import pandas as pd
        df = pd.DataFrame(subject_stats)
        st.dataframe(df, use_container_width=True)
    
    # 最近活动统计
    st.markdown("### 📅 最近活动")
    
    activity_data = stats.get('recent_activity', {})
    if activity_data:
        activity_stats = [
            {'日期': date, '提交次数': count}
            for date, count in sorted(activity_data.items())
        ]
        
        import pandas as pd
        df = pd.DataFrame(activity_stats)
        st.dataframe(df, use_container_width=True)

def _get_submission_subject(submission):
    """获取提交记录的学科"""
    analysis = submission.get('ai_analysis', {})
    if analysis:
        return analysis.get('subject', '未知')
    
    # 尝试从题目详情获取
    question_id = submission.get('question_id')
    if question_id:
        try:
            from services.data_service import data_service
            question_details = data_service.get_question_details(question_id)
            if question_details:
                return question_details.get('master_analysis', {}).get('subject', '未知')
        except:
            pass
    
    return '未知'

def _get_submission_correctness(submission):
    """获取提交记录的正确性"""
    analysis = submission.get('ai_analysis', {})
    if analysis:
        return analysis.get('is_correct')
    
    # 尝试从题目详情获取
    question_id = submission.get('question_id')
    if question_id:
        try:
            from services.data_service import data_service
            question_details = data_service.get_question_details(question_id)
            if question_details:
                return question_details.get('master_analysis', {}).get('is_correct')
        except:
            pass
    
    return None