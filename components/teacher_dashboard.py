"""
教师仪表盘组件
为教师提供强大的班级管理和学情分析工具，包括班级概览、学情分析、学生排名、重点关注学生等
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any, Optional
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_management_v2 import user_management_v2
from services.data_service import DataService

class TeacherDashboard:
    """教师仪表盘类"""
    
    def __init__(self):
        self.data_service = DataService()
        self.user_management = user_management_v2
    
    def render_class_overview(self, teacher_id: str) -> None:
        """渲染班级概览"""
        st.subheader("📊 班级概览")
        
        # 获取教师信息
        teacher = self.user_management.get_user_by_id(teacher_id)
        if not teacher:
            st.warning("无法获取教师信息")
            return
        
        # 获取教师管理的班级
        managed_classes = self.user_management.get_managed_classes(teacher_id)
        if not managed_classes:
            st.warning("您还没有管理的班级")
            return
        
        # 显示班级概览卡片
        for class_info in managed_classes:
            with st.container():
                st.write(f"**{class_info['name']}**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        label="学生人数",
                        value=class_info.get('student_count', 0)
                    )
                
                with col2:
                    accuracy = class_info.get('average_accuracy', 0)
                    st.metric(
                        label="平均正确率",
                        value=f"{accuracy:.1f}%"
                    )
                
                with col3:
                    # 计算需要关注的学生数量
                    attention_students = len(class_info.get('needs_attention_students', []))
                    st.metric(
                        label="需关注学生",
                        value=attention_students,
                        delta_color="inverse" if attention_students > 0 else "normal"
                    )
                
                with col4:
                    # 计算今日活跃学生数（模拟数据）
                    active_today = int(class_info.get('student_count', 0) * 0.8)
                    st.metric(
                        label="今日活跃",
                        value=active_today
                    )
                
                st.divider()
    
    def render_subject_analysis(self, teacher_id: str) -> None:
        """渲染学科分析"""
        st.subheader("📚 学科分析")
        
        # 获取教师信息
        teacher = self.user_management.get_user_by_id(teacher_id)
        if not teacher:
            st.warning("无法获取教师信息")
            return
        
        # 获取教师教授的学科
        subjects = teacher.get('subject_teach', [])
        if not subjects:
            st.warning("未设置教授学科")
            return
        
        # 获取班级信息
        managed_classes = self.user_management.get_managed_classes(teacher_id)
        if not managed_classes:
            st.warning("您还没有管理的班级")
            return
        
        # 按学科显示分析
        for subject in subjects:
            st.write(f"**{subject}学科分析**")
            
            # 收集该学科在所有班级的表现数据
            subject_data = []
            for class_info in managed_classes:
                subject_perf = class_info.get('subject_performance', {}).get(subject, {})
                if subject_perf:
                    subject_data.append({
                        'class_name': class_info['name'],
                        'average': subject_perf.get('average', 0),
                        'weak_points': subject_perf.get('weak_points', [])
                    })
            
            if subject_data:
                # 创建学科表现图表
                df = pd.DataFrame(subject_data)
                
                # 平均分柱状图
                fig = px.bar(
                    df, 
                    x='class_name', 
                    y='average',
                    title=f"{subject}各班级平均分",
                    labels={'class_name': '班级', 'average': '平均分'},
                    color='average',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # 显示薄弱知识点
                st.write("**薄弱知识点分析**：")
                for data in subject_data:
                    if data['weak_points']:
                        st.write(f"- {data['class_name']}：{', '.join(data['weak_points'])}")
                    else:
                        st.write(f"- {data['class_name']}：表现良好")
            else:
                st.info(f"暂无{subject}学科数据")
            
            st.divider()
    
    def render_student_ranking(self, teacher_id: str) -> None:
        """渲染学生排名"""
        st.subheader("🏆 学生排名")
        
        # 获取教师管理的学生
        managed_students = self.user_management.get_managed_students(teacher_id)
        if not managed_students:
            st.warning("您还没有管理的学生")
            return
        
        # 获取学生的学习统计
        student_stats = []
        for student in managed_students:
            stats = self.user_management.get_learning_stats(student['id'])
            if stats:
                student_stats.append({
                    'name': student['name'],
                    'student_number': student.get('student_number', ''),
                    'accuracy': stats.get('accuracy_rate', 0),
                    'total_submissions': stats.get('total_submissions', 0),
                    'correct_count': stats.get('correct_count', 0),
                    'study_hours': stats.get('study_hours', 0)
                })
        
        if not student_stats:
            st.info("暂无学生学习数据")
            return
        
        # 按正确率排序
        student_stats.sort(key=lambda x: x['accuracy'], reverse=True)
        
        # 创建排名表格
        df = pd.DataFrame(student_stats)
        df['rank'] = range(1, len(df) + 1)
        
        # 重新排列列顺序
        df = df[['rank', 'name', 'student_number', 'accuracy', 'total_submissions', 'correct_count', 'study_hours']]
        df.columns = ['排名', '姓名', '学号', '正确率(%)', '总题数', '正确题数', '学习时长(小时)']
        
        # 显示排名表格
        st.dataframe(df, use_container_width=True)
        
        # 显示前三名
        if len(student_stats) >= 3:
            st.write("**🏅 前三名**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if len(student_stats) >= 1:
                    st.metric("🥇 第一名", student_stats[0]['name'], f"{student_stats[0]['accuracy']:.1f}%")
            
            with col2:
                if len(student_stats) >= 2:
                    st.metric("🥈 第二名", student_stats[1]['name'], f"{student_stats[1]['accuracy']:.1f}%")
            
            with col3:
                if len(student_stats) >= 3:
                    st.metric("🥉 第三名", student_stats[2]['name'], f"{student_stats[2]['accuracy']:.1f}%")
    
    def render_attention_students(self, teacher_id: str) -> None:
        """渲染重点关注学生"""
        st.subheader("⚠️ 重点关注学生")
        
        # 获取教师管理的班级
        managed_classes = self.user_management.get_managed_classes(teacher_id)
        if not managed_classes:
            st.warning("您还没有管理的班级")
            return
        
        # 收集需要关注的学生
        attention_students = []
        for class_info in managed_classes:
            student_ids = class_info.get('needs_attention_students', [])
            for student_id in student_ids:
                student = self.user_management.get_user_by_id(student_id)
                if student:
                    stats = self.user_management.get_learning_stats(student_id)
                    attention_students.append({
                        'name': student['name'],
                        'class_name': class_info['name'],
                        'student_number': student.get('student_number', ''),
                        'accuracy': stats.get('accuracy_rate', 0) if stats else 0,
                        'total_submissions': stats.get('total_submissions', 0) if stats else 0,
                        'last_submission': stats.get('last_submission_date', '未知') if stats else '未知'
                    })
        
        if not attention_students:
            st.success("目前没有需要特别关注的学生，班级表现良好！")
            return
        
        # 按正确率排序（从低到高）
        attention_students.sort(key=lambda x: x['accuracy'])
        
        # 显示重点关注学生列表
        for i, student in enumerate(attention_students):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{student['name']}** ({student['class_name']})")
                    st.write(f"学号：{student['student_number']}")
                
                with col2:
                    st.metric(
                        "正确率",
                        f"{student['accuracy']:.1f}%",
                        delta_color="inverse"
                    )
                
                with col3:
                    st.metric(
                        "总题数",
                        student['total_submissions']
                    )
                
                with col4:
                    st.write(f"最近提交：{student['last_submission']}")
                
                # 添加关注按钮
                if st.button(f"查看详情", key=f"detail_{i}"):
                    st.info(f"查看 {student['name']} 的详细学习报告")
                
                st.divider()
    
    def render_teaching_suggestions(self, teacher_id: str) -> None:
        """渲染教学建议"""
        st.subheader("💡 教学建议")
        
        # 获取教师信息
        teacher = self.user_management.get_user_by_id(teacher_id)
        if not teacher:
            st.warning("无法获取教师信息")
            return
        
        # 获取班级信息
        managed_classes = self.user_management.get_managed_classes(teacher_id)
        if not managed_classes:
            st.warning("您还没有管理的班级")
            return
        
        # 分析班级整体情况并生成建议
        suggestions = []
        
        for class_info in managed_classes:
            class_name = class_info['name']
            accuracy = class_info.get('average_accuracy', 0)
            attention_students = len(class_info.get('needs_attention_students', []))
            
            # 基于正确率生成建议
            if accuracy < 70:
                suggestions.append({
                    'class': class_name,
                    'type': '整体提升',
                    'suggestion': f'{class_name}整体正确率偏低({accuracy:.1f}%)，建议加强基础知识点讲解，增加练习量。',
                    'priority': 'high'
                })
            elif accuracy < 80:
                suggestions.append({
                    'class': class_name,
                    'type': '稳步提升',
                    'suggestion': f'{class_name}表现良好({accuracy:.1f}%)，可以适当增加难度，拓展学生思维。',
                    'priority': 'medium'
                })
            else:
                suggestions.append({
                    'class': class_name,
                    'type': '优秀表现',
                    'suggestion': f'{class_name}表现优秀({accuracy:.1f}%)，可以安排一些挑战性题目。',
                    'priority': 'low'
                })
            
            # 基于需要关注的学生数量生成建议
            if attention_students > 0:
                suggestions.append({
                    'class': class_name,
                    'type': '个别辅导',
                    'suggestion': f'{class_name}有{attention_students}名学生需要特别关注，建议安排个别辅导。',
                    'priority': 'high'
                })
        
        # 显示教学建议
        for suggestion in suggestions:
            priority_color = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢'
            }
            
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.write(f"{priority_color[suggestion['priority']]} **{suggestion['type']}**")
                
                with col2:
                    st.write(f"**{suggestion['class']}**：{suggestion['suggestion']}")
                
                st.divider()
    
    def render_quick_actions(self, teacher_id: str) -> None:
        """渲染快速操作"""
        st.subheader("⚡ 快速操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 生成班级报告", use_container_width=True):
                st.success("正在生成班级学习报告...")
        
        with col2:
            if st.button("📝 布置作业", use_container_width=True):
                st.info("跳转到作业布置页面")
        
        with col3:
            if st.button("📧 联系家长", use_container_width=True):
                st.info("跳转到家长沟通页面")
        
        st.divider()
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            if st.button("📈 查看趋势", use_container_width=True):
                st.info("显示班级学习趋势分析")
        
        with col5:
            if st.button("🎯 设置目标", use_container_width=True):
                st.info("设置班级学习目标")
        
        with col6:
            if st.button("📋 导出数据", use_container_width=True):
                st.success("正在导出班级数据...")
    
    def render_teacher_dashboard(self, teacher_id: str) -> None:
        """渲染教师仪表盘主界面"""
        st.title("👨‍🏫 教师仪表盘")
        
        # 获取教师信息
        teacher = self.user_management.get_user_by_id(teacher_id)
        if not teacher:
            st.error("无法获取教师信息")
            return
        
        # 显示教师信息
        st.write(f"**欢迎回来，{teacher['name']}老师！**")
        st.write(f"**教授学科**：{', '.join(teacher.get('subject_teach', []))}")
        
        # 创建标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 班级概览", 
            "📚 学科分析", 
            "🏆 学生排名", 
            "⚠️ 重点关注", 
            "💡 教学建议"
        ])
        
        with tab1:
            self.render_class_overview(teacher_id)
        
        with tab2:
            self.render_subject_analysis(teacher_id)
        
        with tab3:
            self.render_student_ranking(teacher_id)
        
        with tab4:
            self.render_attention_students(teacher_id)
        
        with tab5:
            self.render_teaching_suggestions(teacher_id)
        
        # 快速操作区域
        st.divider()
        self.render_quick_actions(teacher_id) 