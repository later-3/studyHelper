"""
学生仪表盘组件
为学生提供个性化的学习助手界面，包括学习概览、今日目标、最近错题、推荐练习等
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import Dict, List, Any, Optional
import json

from core.user_management_v2 import user_management_v2
from services.data_service import DataService

class StudentDashboard:
    """学生仪表盘类"""
    
    def __init__(self):
        self.data_service = DataService()
        self.user_management = user_management_v2
    
    def render_learning_overview(self, user_id: str) -> None:
        """渲染学习概览"""
        st.subheader("📊 今日学习概览")
        
        # 获取学生学习统计
        learning_stats = self.user_management.get_learning_stats(user_id)
        user = self.user_management.get_user_by_id(user_id)
        
        if not learning_stats or not user:
            st.warning("无法获取学习数据")
            return
        
        # 创建概览卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="今日做题数",
                value=learning_stats.get('today_submissions', 0),
                delta=learning_stats.get('today_submissions_delta', 0)
            )
        
        with col2:
            st.metric(
                label="正确率",
                value=f"{learning_stats.get('accuracy_rate', 0):.1f}%",
                delta=f"{learning_stats.get('accuracy_delta', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                label="新增错题",
                value=learning_stats.get('new_mistakes', 0),
                delta=learning_stats.get('mistakes_delta', 0),
                delta_color="inverse"
            )
        
        with col4:
            # 计算学习时长（模拟数据）
            study_hours = learning_stats.get('study_hours', 2.5)
            st.metric(
                label="学习时长",
                value=f"{study_hours:.1f}小时",
                delta=f"{learning_stats.get('study_hours_delta', 0.5):.1f}小时"
            )
    
    def render_learning_goals(self, user_id: str) -> None:
        """渲染学习目标"""
        st.subheader("🎯 学习目标")
        
        # 获取用户信息
        user = self.user_management.get_user_by_id(user_id)
        if not user:
            st.warning("无法获取用户信息")
            return
        
        # 模拟学习目标数据
        goals = {
            'weekly_target': 20,
            'weekly_progress': 15,
            'weak_subject': '数学',
            'focus_topics': ['分数计算', '几何图形']
        }
        
        # 计算进度
        progress = (goals['weekly_progress'] / goals['weekly_target']) * 100
        
        # 显示目标进度
        st.write(f"**本周目标**：完成 {goals['weekly_target']} 道题目")
        st.progress(progress / 100)
        st.write(f"**当前进度**：{goals['weekly_progress']}/{goals['weekly_target']} ({progress:.1f}%)")
        
        # 显示薄弱学科
        st.write(f"**重点关注**：{goals['weak_subject']}")
        st.write(f"**重点知识点**：{', '.join(goals['focus_topics'])}")
    
    def render_recent_mistakes(self, user_id: str) -> None:
        """渲染最近错题"""
        st.subheader("📚 最近错题")
        
        # 获取学生的错题数据
        submissions = self.data_service.get_submissions_by_user(user_id)
        if not submissions:
            st.info("暂无错题记录")
            return
        
        # 筛选最近的错题（错误答案）
        recent_mistakes = []
        for submission in submissions[-10:]:  # 最近10条记录
            if submission.get('is_correct') == False:
                recent_mistakes.append(submission)
        
        if not recent_mistakes:
            st.success("最近没有错题，继续保持！")
            return
        
        # 按学科分组显示错题
        subjects = {}
        for mistake in recent_mistakes:
            subject = mistake.get('subject', '未知学科')
            if subject not in subjects:
                subjects[subject] = []
            subjects[subject].append(mistake)
        
        # 显示错题列表
        for subject, mistakes in subjects.items():
            with st.expander(f"{subject} ({len(mistakes)}题)"):
                for i, mistake in enumerate(mistakes[:3]):  # 每个学科最多显示3题
                    st.write(f"**题目 {i+1}**：{mistake.get('question_text', '题目内容')[:50]}...")
                    st.write(f"**错误答案**：{mistake.get('user_answer', '无')}")
                    st.write(f"**正确答案**：{mistake.get('correct_answer', '无')}")
                    st.write(f"**时间**：{mistake.get('timestamp', '未知')}")
                    st.divider()
    
    def render_recommended_exercises(self, user_id: str) -> None:
        """渲染推荐练习"""
        st.subheader("🚀 推荐练习")
        
        # 获取用户信息
        user = self.user_management.get_user_by_id(user_id)
        if not user:
            st.warning("无法获取用户信息")
            return
        
        # 模拟推荐练习数据
        recommendations = [
            {
                'type': '基于错题推荐',
                'count': 3,
                'subjects': ['数学', '语文'],
                'difficulty': '中等',
                'description': '针对你最近的错题类型'
            },
            {
                'type': '知识点巩固',
                'count': 2,
                'subjects': ['数学'],
                'difficulty': '基础',
                'description': '巩固分数计算基础'
            },
            {
                'type': '难度提升',
                'count': 1,
                'subjects': ['数学'],
                'difficulty': '困难',
                'description': '挑战几何应用题'
            }
        ]
        
        # 显示推荐练习
        for rec in recommendations:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{rec['type']}**")
                    st.write(f"📝 {rec['description']}")
                    st.write(f"📚 学科：{', '.join(rec['subjects'])}")
                    st.write(f"🎯 难度：{rec['difficulty']}")
                
                with col2:
                    st.write(f"**{rec['count']}题**")
                    if st.button(f"开始练习", key=f"practice_{rec['type']}"):
                        st.success(f"开始{rec['type']}练习！")
                
                st.divider()
    
    def render_learning_trends(self, user_id: str) -> None:
        """渲染学习趋势"""
        st.subheader("📈 学习趋势")
        
        # 获取学习统计数据
        learning_stats = self.user_management.get_learning_stats(user_id)
        if not learning_stats:
            st.warning("无法获取学习趋势数据")
            return
        
        # 模拟一周的学习数据
        dates = [(datetime.now() - timedelta(days=i)).strftime('%m-%d') for i in range(6, -1, -1)]
        accuracy_rates = [75, 78, 82, 79, 85, 88, 84]  # 模拟数据
        submission_counts = [5, 8, 6, 10, 7, 9, 6]  # 模拟数据
        
        # 创建正确率趋势图
        fig_accuracy = go.Figure()
        fig_accuracy.add_trace(go.Scatter(
            x=dates,
            y=accuracy_rates,
            mode='lines+markers',
            name='正确率',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        fig_accuracy.update_layout(
            title="本周正确率变化",
            xaxis_title="日期",
            yaxis_title="正确率 (%)",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_accuracy, use_container_width=True)
        
        # 创建做题数量趋势图
        fig_count = go.Figure()
        fig_count.add_trace(go.Bar(
            x=dates,
            y=submission_counts,
            name='做题数量',
            marker_color='#ff7f0e'
        ))
        fig_count.update_layout(
            title="本周做题数量",
            xaxis_title="日期",
            yaxis_title="题目数量",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_count, use_container_width=True)
    
    def render_subject_performance(self, user_id: str) -> None:
        """渲染学科表现"""
        st.subheader("📊 学科掌握情况")
        
        # 模拟学科表现数据
        subjects_data = {
            '数学': {'average': 85.0, 'total': 25, 'weak_points': ['分数计算', '几何']},
            '语文': {'average': 88.0, 'total': 20, 'weak_points': []},
            '英语': {'average': 75.0, 'total': 15, 'weak_points': ['语法', '词汇']}
        }
        
        # 创建学科表现饼图
        subjects = list(subjects_data.keys())
        averages = [subjects_data[subj]['average'] for subj in subjects]
        
        fig = go.Figure(data=[go.Pie(
            labels=subjects,
            values=averages,
            hole=0.3,
            marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c']
        )])
        fig.update_layout(
            title="各学科平均正确率",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示详细统计
        col1, col2, col3 = st.columns(3)
        
        for i, (subject, data) in enumerate(subjects_data.items()):
            with [col1, col2, col3][i]:
                st.metric(
                    label=subject,
                    value=f"{data['average']:.1f}%",
                    delta=f"{data['total']}题"
                )
                
                if data['weak_points']:
                    st.write(f"**薄弱点**：{', '.join(data['weak_points'])}")
                else:
                    st.write("**状态**：掌握良好")
    
    def render_quick_actions(self, user_id: str) -> None:
        """渲染快速操作"""
        st.subheader("⚡ 快速操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📷 拍照搜题", use_container_width=True):
                st.session_state.page = "upload"
                st.rerun()
        
        with col2:
            if st.button("📚 查看错题本", use_container_width=True):
                st.session_state.page = "answer_history"
                st.rerun()
        
        with col3:
            if st.button("🎯 开始练习", use_container_width=True):
                st.success("正在准备练习题...")
    
    def render_student_dashboard(self, user_id: str) -> None:
        """渲染完整的学生仪表盘"""
        st.title("🎓 我的学习助手")
        
        # 获取用户信息
        user = self.user_management.get_user_by_id(user_id)
        if not user:
            st.error("用户信息获取失败")
            return
        
        # 显示用户欢迎信息
        st.write(f"欢迎回来，**{user['name']}**！今天是 {datetime.now().strftime('%Y年%m月%d日')}")
        
        # 渲染各个组件
        self.render_learning_overview(user_id)
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_learning_goals(user_id)
            st.divider()
            self.render_recent_mistakes(user_id)
        
        with col2:
            self.render_quick_actions(user_id)
            st.divider()
            self.render_recommended_exercises(user_id)
        
        st.divider()
        self.render_learning_trends(user_id)
        st.divider()
        self.render_subject_performance(user_id)

# 创建全局实例
student_dashboard = StudentDashboard() 