"""
简化的UI组件库
使用streamlit原生组件，避免elements的兼容性问题
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# 设计系统常量
COLORS = {
    'primary': '#1976D2',      # 教育蓝
    'success': '#4CAF50',      # 成功绿
    'warning': '#FF9800',      # 警告橙
    'error': '#F44336',        # 错误红
    'info': '#2196F3',         # 信息蓝
    'grey': '#9E9E9E',         # 灰色
    'light_grey': '#F5F5F5',   # 浅灰
    'white': '#FFFFFF',        # 白色
    'black': '#212121'         # 深黑
}

def render_stats_overview(stats: Dict[str, Any]):
    """渲染统计概览"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总题数", stats['total_count'])
    
    with col2:
        st.metric("正确", stats['correct_count'])
    
    with col3:
        st.metric("错误", stats['incorrect_count'])
    
    with col4:
        st.metric("正确率", f"{stats['accuracy_rate']:.1f}%")

def render_subject_distribution_chart(stats: Dict[str, Any]):
    """渲染学科分布图表"""
    if not stats['subject_distribution']:
        st.info("暂无学科分布数据")
        return
    
    # 准备数据
    subjects = list(stats['subject_distribution'].keys())
    counts = list(stats['subject_distribution'].values())
    
    # 创建饼图
    fig = px.pie(
        values=counts, 
        names=subjects,
        title="学科分布",
        color_discrete_sequence=[COLORS['primary'], COLORS['success'], COLORS['warning'], COLORS['error'], COLORS['info']]
    )
    fig.update_layout(
        height=300,
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_activity_trend_chart(stats: Dict[str, Any]):
    """渲染活动趋势图表"""
    if not stats['recent_activity']:
        st.info("暂无活动数据")
        return
    
    # 准备数据
    dates = list(stats['recent_activity'].keys())
    counts = list(stats['recent_activity'].values())
    
    # 按日期排序
    date_count_pairs = sorted(zip(dates, counts), key=lambda x: x[0])
    dates, counts = zip(*date_count_pairs)
    
    # 创建折线图
    fig = px.line(
        x=dates, 
        y=counts,
        title="最近活动趋势",
        labels={'x': '日期', 'y': '提交次数'}
    )
    fig.update_traces(line_color=COLORS['primary'], line_width=3)
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_filter_panel(subjects: List[str]):
    """渲染筛选面板"""
    st.write("### 筛选条件")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_subjects = st.multiselect(
            "学科",
            options=subjects,
            default=subjects,
            key="subject_filter"
        )
        
        correctness_options = ["正确", "错误", "未知"]
        selected_correctness = st.multiselect(
            "正确性",
            options=correctness_options,
            default=correctness_options,
            key="correctness_filter"
        )
    
    with col2:
        start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=30))
        end_date = st.date_input("结束日期", value=datetime.now())
    
    return {
        'subjects': selected_subjects,
        'correctness': selected_correctness,
        'date_range': (start_date, end_date)
    }

def render_question_group_card(question_id: str, submissions: List[Dict], question_details: Optional[Dict] = None):
    """渲染题目组卡片"""
    if not submissions:
        return
    
    # 获取最新提交
    latest_submission = submissions[0]
    
    # 获取分析结果
    ai_analysis = latest_submission.get('ai_analysis')
    if ai_analysis:
        analysis = ai_analysis
        q_text = latest_submission.get('ocr_text', latest_submission.get('submitted_ocr_text', ''))
        subject = analysis.get('subject', '未指定')
        is_correct = analysis.get('is_correct')
    else:
        if question_details:
            analysis = question_details.get('master_analysis', {})
            q_text = question_details.get('canonical_text', '')
            subject = question_details.get('subject', '未指定')
            is_correct = analysis.get('is_correct')
        else:
            analysis = {}
            q_text = latest_submission.get('submitted_ocr_text', '')
            subject = '未指定'
            is_correct = None
    
    # 格式化时间
    timestamp = latest_submission.get('timestamp', '')
    if timestamp:
        try:
            date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = date.strftime('%Y-%m-%d %H:%M')
        except:
            formatted_time = timestamp
    else:
        formatted_time = '未知时间'
    
    # 渲染卡片
    with st.container():
        st.write(f"### 题目组 ({len(submissions)}次提交) - {subject}")
        
        # 题目内容
        st.text_area("题目内容", value=q_text, height=100, disabled=True, key=f"q_text_{question_id}")
        
        # 状态和统计
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if is_correct is True:
                st.success("✅ 正确")
            elif is_correct is False:
                st.error("❌ 错误")
            else:
                st.info("❓ 未知")
        
        with col2:
            correct_count = sum(1 for s in submissions if s.get('ai_analysis', {}).get('is_correct') is True)
            total_count = len(submissions)
            st.write(f"正确率: {correct_count}/{total_count}")
        
        with col3:
            st.write(f"最新提交: {formatted_time}")
        
        # 操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("查看详情", key=f"detail_{question_id}"):
                st.session_state.selected_question = question_id
                st.session_state.show_detail = True
        
        with col2:
            if st.button("重新练习", key=f"practice_{question_id}"):
                st.session_state.practice_question = question_id
        
        # 详细信息（可展开）
        if st.session_state.get('selected_question') == question_id and st.session_state.get('show_detail'):
            with st.expander("详细分析", expanded=True):
                # 解题步骤
                if analysis.get('solution_steps'):
                    st.write("**解题步骤:**")
                    st.write(analysis['solution_steps'])
                
                # 知识点
                if analysis.get('knowledge_point'):
                    st.write("**知识点:**")
                    st.write(analysis['knowledge_point'])
                
                # 常见易错点
                if analysis.get('common_mistakes'):
                    st.write("**常见易错点:**")
                    st.write(analysis['common_mistakes'])
                
                # 错误分析
                if analysis.get('error_analysis'):
                    st.write("**错误分析:**")
                    st.write(analysis['error_analysis'])
                
                # 正确答案
                if analysis.get('correct_answer'):
                    st.write("**正确答案:**")
                    st.write(analysis['correct_answer'])
        
        st.divider()

def render_student_performance_card(student_id: str, student_name: str, performance: Dict[str, Any]):
    """渲染学生学习表现卡片"""
    stats = performance['overall_stats']
    subject_stats = performance['subject_stats']
    
    with st.container():
        st.write(f"### {student_name}")
        
        # 总体统计
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总题数", stats['total_count'])
        
        with col2:
            st.metric("正确率", f"{stats['accuracy_rate']:.1f}%")
        
        with col3:
            recent_count = len(performance['recent_submissions'])
            st.metric("活跃度", f"{recent_count}题")
        
        # 学科表现
        if subject_stats:
            st.write("**学科表现:**")
            for subject, stats in subject_stats.items():
                if stats['total'] > 0:
                    accuracy = stats['accuracy']
                    st.write(f"- {subject}: {accuracy:.1f}%")
        
        st.divider()

def render_class_overview(class_info: Dict[str, Any], class_performance: Dict[str, Any]):
    """渲染班级概览"""
    st.write(f"### 班级: {class_info.get('name', '未知班级')}")
    
    # 班级统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总人数", class_performance['total_students'])
    
    with col2:
        st.metric("活跃人数", class_performance['active_students'])
    
    with col3:
        st.metric("平均正确率", f"{class_performance['average_accuracy']:.1f}%")
    
    with col4:
        if class_performance['total_students'] > 0:
            active_rate = class_performance['active_students'] / class_performance['total_students'] * 100
            st.metric("活跃率", f"{active_rate:.1f}%")
        else:
            st.metric("活跃率", "0%")

def render_loading_spinner(message: str = "加载中..."):
    """渲染加载动画"""
    st.spinner(message)

def render_empty_state(message: str = "暂无数据", icon: str = "📝"):
    """渲染空状态"""
    st.write(f"## {icon}")
    st.write(f"### {message}") 