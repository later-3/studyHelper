"""
校长仪表盘组件
为校长提供学校整体管理和决策支持，包括学校概览、年级对比、学科表现、教师团队评估、战略建议等
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

class PrincipalDashboard:
    """校长仪表盘类"""
    
    def __init__(self):
        self.data_service = DataService()
        self.user_management = user_management_v2
    
    def render_school_overview(self, principal_id: str) -> None:
        """渲染学校概览"""
        st.subheader("🏫 学校概览")
        school_info = self.user_management.get_school_info()
        if not school_info:
            st.warning("无法获取学校信息")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("年级数", school_info.get('total_grades', 0))
        with col2:
            st.metric("班级数", school_info.get('total_classes', 0))
        with col3:
            st.metric("学生数", school_info.get('total_students', 0))
        with col4:
            st.metric("教师数", school_info.get('total_teachers', 0))
        st.divider()
        st.write(f"**学校名称**：{school_info.get('name', '未知')}")
        st.write(f"**地址**：{school_info.get('address', '未知')}")
        st.write(f"**校长**：{self.user_management.get_user_by_id(principal_id).get('name', '未知')}")
        st.write(f"**创建时间**：{school_info.get('created_at', '未知')}")
        st.write(f"**更新时间**：{school_info.get('updated_at', '未知')}")
    
    def render_grade_comparison(self, principal_id: str) -> None:
        """渲染年级对比"""
        st.subheader("📊 年级对比")
        grades = self.user_management.get_all_grades()
        if not grades:
            st.warning("暂无年级数据")
            return
        
        # 年级对比表格
        df = pd.DataFrame([
            {
                '年级': g['name'],
                '班级数': g.get('total_classes', 0),
                '学生数': g.get('total_students', 0),
                '教师数': g.get('total_teachers', 0),
                '平均正确率': g.get('average_accuracy', 0)
            } for g in grades
        ])
        st.dataframe(df, use_container_width=True)
        
        # 年级平均正确率对比图
        fig = px.bar(
            df,
            x='年级',
            y='平均正确率',
            title="各年级平均正确率对比",
            color='平均正确率',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()
    
    def render_subject_performance(self, principal_id: str) -> None:
        """渲染学科表现"""
        st.subheader("📚 学科表现")
        classes = self.user_management.get_all_classes()
        if not classes:
            st.warning("暂无班级数据")
            return
        
        # 汇总全校学科数据
        subject_stats = {}
        for cls in classes:
            subject_perf = cls.get('subject_performance', {})
            for subject, data in subject_perf.items():
                if subject not in subject_stats:
                    subject_stats[subject] = []
                subject_stats[subject].append(data.get('average', 0))
        
        if not subject_stats:
            st.info("暂无学科数据")
            return
        
        # 生成学科表现表格
        subject_df = pd.DataFrame([
            {
                '学科': subject,
                '全校平均分': sum(scores)/len(scores) if scores else 0
            } for subject, scores in subject_stats.items()
        ])
        st.dataframe(subject_df, use_container_width=True)
        
        # 学科分布图
        fig = px.bar(
            subject_df,
            x='学科',
            y='全校平均分',
            title="全校学科平均分对比",
            color='全校平均分',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()
    
    def render_teacher_team_evaluation(self, principal_id: str) -> None:
        """渲染教师团队评估"""
        st.subheader("👩‍🏫 教师团队评估")
        teachers = self.user_management.get_teachers()
        if not teachers:
            st.warning("暂无教师数据")
            return
        
        teacher_stats = []
        for teacher in teachers:
            managed_classes = self.user_management.get_managed_classes(teacher['id'])
            total_students = 0
            total_accuracy = 0
            for cls in managed_classes:
                total_students += cls.get('student_count', 0)
                total_accuracy += cls.get('average_accuracy', 0)
            avg_accuracy = total_accuracy / len(managed_classes) if managed_classes else 0
            teacher_stats.append({
                '姓名': teacher['name'],
                '教授学科': ', '.join(teacher.get('subject_teach', [])),
                '管理班级': len(managed_classes),
                '学生数': total_students,
                '平均正确率': avg_accuracy
            })
        if not teacher_stats:
            st.info("暂无教师团队数据")
            return
        df = pd.DataFrame(teacher_stats)
        st.dataframe(df, use_container_width=True)
        # 教师平均正确率分布
        fig = px.histogram(
            df,
            x='平均正确率',
            nbins=10,
            title="教师平均正确率分布"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()
    
    def render_strategic_suggestions(self, principal_id: str) -> None:
        """渲染战略建议"""
        st.subheader("💡 战略建议")
        school_info = self.user_management.get_school_info()
        grades = self.user_management.get_all_grades()
        teachers = self.user_management.get_teachers()
        suggestions = []
        # 学校整体表现
        avg_acc = school_info.get('total_students', 0)
        if grades:
            avg_acc = sum(g.get('average_accuracy', 0) for g in grades) / len(grades)
        if avg_acc < 70:
            suggestions.append({
                'type': '整体提升',
                'suggestion': f'学校整体正确率偏低({avg_acc:.1f}%)，建议加强教研、优化课程体系。',
                'priority': 'high'
            })
        elif avg_acc < 80:
            suggestions.append({
                'type': '稳步提升',
                'suggestion': f'学校表现良好({avg_acc:.1f}%)，可推动校际交流、教师培训。',
                'priority': 'medium'
            })
        else:
            suggestions.append({
                'type': '优秀表现',
                'suggestion': f'学校表现优秀({avg_acc:.1f}%)，可探索特色课程和创新项目。',
                'priority': 'low'
            })
        # 年级差异
        if grades:
            accs = [g.get('average_accuracy', 0) for g in grades]
            if max(accs) - min(accs) > 15:
                suggestions.append({
                    'type': '年级差异',
                    'suggestion': f'年级间差异较大({max(accs)-min(accs):.1f}%)，建议加强年级间经验交流。',
                    'priority': 'high'
                })
        # 教师团队
        if teachers:
            active_teachers = sum(1 for t in teachers if t.get('last_login'))
            activity_rate = active_teachers / len(teachers) * 100
            if activity_rate < 80:
                suggestions.append({
                    'type': '教师活跃度',
                    'suggestion': f'教师活跃度偏低({activity_rate:.1f}%)，建议加强激励和培训。',
                    'priority': 'medium'
                })
        for suggestion in suggestions:
            priority_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.write(f"{priority_color[suggestion['priority']]} **{suggestion['type']}**")
                with col2:
                    st.write(suggestion['suggestion'])
                st.divider()
    
    def render_quick_actions(self, principal_id: str) -> None:
        """渲染快速操作"""
        st.subheader("⚡ 快速操作")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 生成学校报告", use_container_width=True):
                st.success("正在生成学校学习报告...")
        with col2:
            if st.button("👥 校务会议", use_container_width=True):
                st.info("跳转到校务会议安排页面")
        with col3:
            if st.button("📧 通知发布", use_container_width=True):
                st.info("跳转到全校通知发布页面")
        st.divider()
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("📈 查看趋势", use_container_width=True):
                st.info("显示学校学习趋势分析")
        with col5:
            if st.button("🎯 设置目标", use_container_width=True):
                st.info("设置学校发展目标")
        with col6:
            if st.button("📋 导出数据", use_container_width=True):
                st.success("正在导出学校数据...")
    
    def render_principal_dashboard(self, principal_id: str) -> None:
        """渲染校长仪表盘主界面"""
        st.title("🏫 校长仪表盘")
        principal = self.user_management.get_user_by_id(principal_id)
        if not principal:
            st.error("无法获取校长信息")
            return
        st.write(f"**欢迎回来，{principal['name']}校长！**")
        school_info = self.user_management.get_school_info()
        if school_info:
            st.write(f"**管理学校**：{school_info.get('name', '未知')}")
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏫 学校概览",
            "📊 年级对比",
            "📚 学科表现",
            "👩‍🏫 教师团队",
            "💡 战略建议"
        ])
        with tab1:
            self.render_school_overview(principal_id)
        with tab2:
            self.render_grade_comparison(principal_id)
        with tab3:
            self.render_subject_performance(principal_id)
        with tab4:
            self.render_teacher_team_evaluation(principal_id)
        with tab5:
            self.render_strategic_suggestions(principal_id)
        st.divider()
        self.render_quick_actions(principal_id) 