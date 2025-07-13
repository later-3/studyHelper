"""
年级主任仪表盘组件
为年级主任提供年级管理和教学指导工具，包括年级概览、班级排名、学科分析、教师表现评估、管理建议等
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

class GradeManagerDashboard:
    """年级主任仪表盘类"""
    
    def __init__(self):
        self.data_service = DataService()
        self.user_management = user_management_v2
    
    def render_grade_overview(self, grade_manager_id: str) -> None:
        """渲染年级概览"""
        st.subheader("📊 年级概览")
        
        # 获取年级主任信息
        grade_manager = self.user_management.get_user_by_id(grade_manager_id)
        if not grade_manager:
            st.warning("无法获取年级主任信息")
            return
        
        # 获取年级信息
        grade_id = grade_manager.get('grade_id')
        if not grade_id:
            st.warning("您还没有管理的年级")
            return
        
        grade_info = self.user_management.get_grade_by_id(grade_id)
        if not grade_info:
            st.warning("无法获取年级信息")
            return
        
        # 获取年级下的班级
        managed_classes = self.user_management.get_managed_classes(grade_manager_id)
        
        # 显示年级概览卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="班级数量",
                value=grade_info.get('total_classes', 0)
            )
        
        with col2:
            st.metric(
                label="学生总数",
                value=grade_info.get('total_students', 0)
            )
        
        with col3:
            accuracy = grade_info.get('average_accuracy', 0)
            st.metric(
                label="年级平均正确率",
                value=f"{accuracy:.1f}%"
            )
        
        with col4:
            st.metric(
                label="教师数量",
                value=grade_info.get('total_teachers', 0)
            )
        
        st.divider()
        
        # 显示年级基本信息
        st.write(f"**年级名称**：{grade_info['name']}")
        st.write(f"**年级主任**：{grade_manager['name']}")
        st.write(f"**创建时间**：{grade_info.get('created_at', '未知')}")
        
        # 显示班级列表
        if managed_classes:
            st.write("**班级列表**：")
            for class_info in managed_classes:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{class_info['name']}**")
                    teacher = self.user_management.get_teacher_by_class(class_info['id'])
                    if teacher:
                        st.write(f"班主任：{teacher['name']}")
                
                with col2:
                    st.metric(
                        "学生数",
                        class_info.get('student_count', 0)
                    )
                
                with col3:
                    class_accuracy = class_info.get('average_accuracy', 0)
                    st.metric(
                        "正确率",
                        f"{class_accuracy:.1f}%"
                    )
                
                with col4:
                    attention_count = len(class_info.get('needs_attention_students', []))
                    st.metric(
                        "需关注",
                        attention_count,
                        delta_color="inverse" if attention_count > 0 else "normal"
                    )
                
                st.divider()
    
    def render_class_ranking(self, grade_manager_id: str) -> None:
        """渲染班级排名"""
        st.subheader("🏆 班级排名")
        
        # 获取年级主任管理的班级
        managed_classes = self.user_management.get_managed_classes(grade_manager_id)
        if not managed_classes:
            st.warning("您还没有管理的班级")
            return
        
        # 收集班级统计数据
        class_stats = []
        for class_info in managed_classes:
            # 获取班级学生
            students = self.user_management.get_students_by_class(class_info['id'])
            
            # 计算班级统计
            total_submissions = 0
            total_correct = 0
            active_students = 0
            
            for student in students:
                stats = self.user_management.get_learning_stats(student['id'])
                if stats:
                    total_submissions += stats.get('total_submissions', 0)
                    total_correct += stats.get('correct_count', 0)
                    if stats.get('total_submissions', 0) > 0:
                        active_students += 1
            
            accuracy = (total_correct / total_submissions * 100) if total_submissions > 0 else 0
            activity_rate = (active_students / len(students) * 100) if students else 0
            
            class_stats.append({
                'class_name': class_info['name'],
                'student_count': len(students),
                'accuracy': accuracy,
                'activity_rate': activity_rate,
                'total_submissions': total_submissions,
                'attention_students': len(class_info.get('needs_attention_students', []))
            })
        
        if not class_stats:
            st.info("暂无班级数据")
            return
        
        # 按正确率排序
        class_stats.sort(key=lambda x: x['accuracy'], reverse=True)
        
        # 创建排名表格
        df = pd.DataFrame(class_stats)
        df['rank'] = range(1, len(df) + 1)
        
        # 重新排列列顺序
        df = df[['rank', 'class_name', 'student_count', 'accuracy', 'activity_rate', 'total_submissions', 'attention_students']]
        df.columns = ['排名', '班级', '学生数', '正确率(%)', '活跃率(%)', '总题数', '需关注学生']
        
        # 显示排名表格
        st.dataframe(df, use_container_width=True)
        
        # 显示前三名
        if len(class_stats) >= 3:
            st.write("**🏅 前三名班级**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if len(class_stats) >= 1:
                    st.metric("🥇 第一名", class_stats[0]['class_name'], f"{class_stats[0]['accuracy']:.1f}%")
            
            with col2:
                if len(class_stats) >= 2:
                    st.metric("🥈 第二名", class_stats[1]['class_name'], f"{class_stats[1]['accuracy']:.1f}%")
            
            with col3:
                if len(class_stats) >= 3:
                    st.metric("🥉 第三名", class_stats[2]['class_name'], f"{class_stats[2]['accuracy']:.1f}%")
    
    def render_subject_analysis(self, grade_manager_id: str) -> None:
        """渲染学科分析"""
        st.subheader("📚 学科分析")
        
        # 获取年级主任管理的班级
        managed_classes = self.user_management.get_managed_classes(grade_manager_id)
        if not managed_classes:
            st.warning("您还没有管理的班级")
            return
        
        # 收集所有学科数据
        all_subjects = set()
        subject_data = {}
        
        for class_info in managed_classes:
            subject_performance = class_info.get('subject_performance', {})
            for subject, data in subject_performance.items():
                all_subjects.add(subject)
                if subject not in subject_data:
                    subject_data[subject] = []
                subject_data[subject].append({
                    'class_name': class_info['name'],
                    'average': data.get('average', 0),
                    'weak_points': data.get('weak_points', [])
                })
        
        if not all_subjects:
            st.info("暂无学科数据")
            return
        
        # 按学科显示分析
        for subject in sorted(all_subjects):
            st.write(f"**{subject}学科分析**")
            
            subject_class_data = subject_data[subject]
            if subject_class_data:
                # 创建学科表现图表
                df = pd.DataFrame(subject_class_data)
                
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
                
                # 计算年级平均分
                grade_average = df['average'].mean()
                st.metric(f"{subject}年级平均分", f"{grade_average:.1f}分")
                
                # 显示薄弱知识点
                st.write("**薄弱知识点分析**：")
                for data in subject_class_data:
                    if data['weak_points']:
                        st.write(f"- {data['class_name']}：{', '.join(data['weak_points'])}")
                    else:
                        st.write(f"- {data['class_name']}：表现良好")
            else:
                st.info(f"暂无{subject}学科数据")
            
            st.divider()
    
    def render_teacher_evaluation(self, grade_manager_id: str) -> None:
        """渲染教师表现评估"""
        st.subheader("👨‍🏫 教师表现评估")
        
        # 获取年级主任管理的教师
        grade_id = self.user_management.get_user_by_id(grade_manager_id).get('grade_id')
        if not grade_id:
            st.warning("您还没有管理的年级")
            return
        
        teachers = self.user_management.get_teachers_by_grade(grade_id)
        if not teachers:
            st.warning("您还没有管理的教师")
            return
        
        # 收集教师表现数据
        teacher_stats = []
        for teacher in teachers:
            # 获取教师管理的班级
            managed_classes = self.user_management.get_managed_classes(teacher['id'])
            
            total_students = 0
            total_accuracy = 0
            total_attention_students = 0
            
            for class_info in managed_classes:
                students = self.user_management.get_students_by_class(class_info['id'])
                total_students += len(students)
                total_attention_students += len(class_info.get('needs_attention_students', []))
                
                # 计算班级平均正确率
                class_accuracy = class_info.get('average_accuracy', 0)
                total_accuracy += class_accuracy
            
            avg_accuracy = total_accuracy / len(managed_classes) if managed_classes else 0
            attention_rate = (total_attention_students / total_students * 100) if total_students > 0 else 0
            
            teacher_stats.append({
                'name': teacher['name'],
                'subjects': ', '.join(teacher.get('subject_teach', [])),
                'managed_classes': len(managed_classes),
                'total_students': total_students,
                'avg_accuracy': avg_accuracy,
                'attention_rate': attention_rate,
                'last_login': teacher.get('last_login', '未知')
            })
        
        if not teacher_stats:
            st.info("暂无教师数据")
            return
        
        # 按平均正确率排序
        teacher_stats.sort(key=lambda x: x['avg_accuracy'], reverse=True)
        
        # 创建教师评估表格
        df = pd.DataFrame(teacher_stats)
        df['rank'] = range(1, len(df) + 1)
        
        # 重新排列列顺序
        df = df[['rank', 'name', 'subjects', 'managed_classes', 'total_students', 'avg_accuracy', 'attention_rate']]
        df.columns = ['排名', '姓名', '教授学科', '管理班级', '学生总数', '平均正确率(%)', '需关注率(%)']
        
        # 显示评估表格
        st.dataframe(df, use_container_width=True)
        
        # 显示优秀教师
        if len(teacher_stats) >= 3:
            st.write("**🌟 优秀教师**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if len(teacher_stats) >= 1:
                    st.metric("🥇 第一名", teacher_stats[0]['name'], f"{teacher_stats[0]['avg_accuracy']:.1f}%")
            
            with col2:
                if len(teacher_stats) >= 2:
                    st.metric("🥈 第二名", teacher_stats[1]['name'], f"{teacher_stats[1]['avg_accuracy']:.1f}%")
            
            with col3:
                if len(teacher_stats) >= 3:
                    st.metric("🥉 第三名", teacher_stats[2]['name'], f"{teacher_stats[2]['avg_accuracy']:.1f}%")
    
    def render_management_suggestions(self, grade_manager_id: str) -> None:
        """渲染管理建议"""
        st.subheader("💡 管理建议")
        
        # 获取年级主任信息
        grade_manager = self.user_management.get_user_by_id(grade_manager_id)
        if not grade_manager:
            st.warning("无法获取年级主任信息")
            return
        
        # 获取年级信息
        grade_id = grade_manager.get('grade_id')
        if not grade_id:
            st.warning("您还没有管理的年级")
            return
        
        grade_info = self.user_management.get_grade_by_id(grade_id)
        if not grade_info:
            st.warning("无法获取年级信息")
            return
        
        # 获取班级信息
        managed_classes = self.user_management.get_managed_classes(grade_manager_id)
        if not managed_classes:
            st.warning("您还没有管理的班级")
            return
        
        # 分析年级整体情况并生成建议
        suggestions = []
        
        # 年级整体表现分析
        grade_accuracy = grade_info.get('average_accuracy', 0)
        if grade_accuracy < 70:
            suggestions.append({
                'type': '年级整体提升',
                'suggestion': f'年级整体正确率偏低({grade_accuracy:.1f}%)，建议加强年级教研活动，统一教学标准。',
                'priority': 'high'
            })
        elif grade_accuracy < 80:
            suggestions.append({
                'type': '年级稳步提升',
                'suggestion': f'年级表现良好({grade_accuracy:.1f}%)，可以组织优秀教师分享教学经验。',
                'priority': 'medium'
            })
        else:
            suggestions.append({
                'type': '年级优秀表现',
                'suggestion': f'年级表现优秀({grade_accuracy:.1f}%)，可以安排一些挑战性活动。',
                'priority': 'low'
            })
        
        # 班级差异分析
        accuracies = [cls.get('average_accuracy', 0) for cls in managed_classes]
        if accuracies:
            max_acc = max(accuracies)
            min_acc = min(accuracies)
            diff = max_acc - min_acc
            
            if diff > 15:
                suggestions.append({
                    'type': '班级差异较大',
                    'suggestion': f'班级间差异较大({diff:.1f}%)，建议组织班级间交流活动，促进均衡发展。',
                    'priority': 'high'
                })
        
        # 教师团队分析
        teachers = self.user_management.get_teachers_by_grade(grade_id)
        if teachers:
            active_teachers = sum(1 for t in teachers if t.get('last_login'))
            activity_rate = active_teachers / len(teachers) * 100
            
            if activity_rate < 80:
                suggestions.append({
                    'type': '教师活跃度',
                    'suggestion': f'教师活跃度偏低({activity_rate:.1f}%)，建议加强教师培训和激励机制。',
                    'priority': 'medium'
                })
        
        # 显示管理建议
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
                    st.write(suggestion['suggestion'])
                
                st.divider()
    
    def render_quick_actions(self, grade_manager_id: str) -> None:
        """渲染快速操作"""
        st.subheader("⚡ 快速操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 生成年级报告", use_container_width=True):
                st.success("正在生成年级学习报告...")
        
        with col2:
            if st.button("👥 教师会议", use_container_width=True):
                st.info("跳转到教师会议安排页面")
        
        with col3:
            if st.button("📧 通知发布", use_container_width=True):
                st.info("跳转到通知发布页面")
        
        st.divider()
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            if st.button("📈 查看趋势", use_container_width=True):
                st.info("显示年级学习趋势分析")
        
        with col5:
            if st.button("🎯 设置目标", use_container_width=True):
                st.info("设置年级学习目标")
        
        with col6:
            if st.button("📋 导出数据", use_container_width=True):
                st.success("正在导出年级数据...")
    
    def render_grade_manager_dashboard(self, grade_manager_id: str) -> None:
        """渲染年级主任仪表盘主界面"""
        st.title("👨‍💼 年级主任仪表盘")
        
        # 获取年级主任信息
        grade_manager = self.user_management.get_user_by_id(grade_manager_id)
        if not grade_manager:
            st.error("无法获取年级主任信息")
            return
        
        # 获取年级信息
        grade_id = grade_manager.get('grade_id')
        grade_info = self.user_management.get_grade_by_id(grade_id) if grade_id else None
        
        # 显示年级主任信息
        st.write(f"**欢迎回来，{grade_manager['name']}主任！**")
        if grade_info:
            st.write(f"**管理年级**：{grade_info['name']}")
        
        # 创建标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 年级概览", 
            "🏆 班级排名", 
            "📚 学科分析", 
            "👨‍🏫 教师评估", 
            "💡 管理建议"
        ])
        
        with tab1:
            self.render_grade_overview(grade_manager_id)
        
        with tab2:
            self.render_class_ranking(grade_manager_id)
        
        with tab3:
            self.render_subject_analysis(grade_manager_id)
        
        with tab4:
            self.render_teacher_evaluation(grade_manager_id)
        
        with tab5:
            self.render_management_suggestions(grade_manager_id)
        
        # 快速操作区域
        st.divider()
        self.render_quick_actions(grade_manager_id) 