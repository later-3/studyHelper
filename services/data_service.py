"""
优化的数据服务
支持高效查询、分组和统计功能
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataService:
    """优化的数据服务类"""
    
    def __init__(self):
        self.submissions_file = 'data/submission_history.json'
        self.questions_file = 'data/question_bank.json'
        self.users_file = 'data/users.json'
        self.classes_file = 'data/classes.json'
        
        # 缓存
        self._submissions_cache = None
        self._questions_cache = None
        self._users_cache = None
        self._classes_cache = None
        self._cache_timestamp = None
        
    def _load_data(self, file_path: str, default_value: Any) -> Any:
        """加载数据文件"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")
        return default_value
    
    def _save_data(self, file_path: str, data: Any) -> bool:
        """保存数据文件"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存文件失败 {file_path}: {e}")
            return False
    
    def _get_cache_key(self) -> str:
        """获取缓存键"""
        files = [self.submissions_file, self.questions_file, self.users_file, self.classes_file]
        timestamps = []
        for file_path in files:
            if os.path.exists(file_path):
                timestamps.append(str(os.path.getmtime(file_path)))
            else:
                timestamps.append("0")
        return "_".join(timestamps)
    
    def _load_all_data(self):
        """加载所有数据到缓存"""
        cache_key = self._get_cache_key()
        if self._cache_timestamp == cache_key:
            return  # 缓存有效
        
        # 加载数据
        self._submissions_cache = self._load_data(self.submissions_file, [])
        self._questions_cache = self._load_data(self.questions_file, {})
        self._users_cache = self._load_data(self.users_file, {})
        self._classes_cache = self._load_data(self.classes_file, {})
        self._cache_timestamp = cache_key
        
        # 确保缓存不为None
        if self._submissions_cache is None:
            self._submissions_cache = []
        if self._questions_cache is None:
            self._questions_cache = {}
        if self._users_cache is None:
            self._users_cache = {}
        if self._classes_cache is None:
            self._classes_cache = {}
        
        logger.info("数据缓存已更新")
    
    def get_user_submissions(self, user_id: str, role: str = None) -> List[Dict]:
        """获取用户可见的提交记录"""
        self._load_all_data()
        
        if role == 'student':
            return [s for s in self._submissions_cache if s.get('user_id') == user_id]
        elif role == 'teacher':
            # 获取教师管理的班级学生
            managed_students = self._get_managed_students(user_id)
            return [s for s in self._submissions_cache if s.get('user_id') in managed_students]
        elif role == 'school':
            return self._submissions_cache
        else:
            return []
    
    def get_submissions_by_user(self, user_id: str) -> List[Dict]:
        """获取指定用户的所有提交记录（兼容性方法）"""
        return self.get_user_submissions(user_id, role='student')
    
    def _get_managed_students(self, teacher_id: str) -> List[str]:
        """获取教师管理的学生ID列表"""
        managed_students = []
        if self._classes_cache is None:
            self._classes_cache = {}
        for class_data in self._classes_cache.values():
            if class_data.get('teacher_id') == teacher_id:
                managed_students.extend(class_data.get('students', []))
        return managed_students
    
    def get_submissions_by_question(self, user_id: str, question_id: str) -> List[Dict]:
        """获取指定题目的所有提交记录"""
        self._load_all_data()
        return [s for s in self._submissions_cache 
                if s.get('user_id') == user_id and s.get('question_id') == question_id]
    
    def group_submissions_by_question(self, submissions: List[Dict]) -> Dict[str, List[Dict]]:
        """按题目分组提交记录"""
        grouped = defaultdict(list)
        
        for submission in submissions:
            # 确定题目ID
            question_id = submission.get('question_id')
            if not question_id:
                # 如果没有question_id，尝试从ai_analysis中获取
                ai_analysis = submission.get('ai_analysis', {})
                if ai_analysis:
                    # 使用OCR文本作为分组键
                    ocr_text = submission.get('ocr_text', submission.get('submitted_ocr_text', ''))
                    question_id = f"ocr_{hash(ocr_text)}"
                else:
                    continue
            
            grouped[question_id].append(submission)
        
        # 按最新提交时间排序
        for question_id in grouped:
            grouped[question_id].sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return dict(grouped)
    
    def get_submission_stats(self, submissions: List[Dict]) -> Dict[str, Any]:
        """获取提交统计信息"""
        if not submissions:
            return {
                'total_count': 0,
                'correct_count': 0,
                'incorrect_count': 0,
                'accuracy_rate': 0,
                'subject_distribution': {},
                'recent_activity': {}
            }
        
        # 确保数据已加载
        self._load_all_data()
        
        stats = {
            'total_count': len(submissions),
            'correct_count': 0,
            'incorrect_count': 0,
            'subject_distribution': defaultdict(int),
            'recent_activity': defaultdict(int)
        }
        
        for submission in submissions:
            # 获取分析结果
            ai_analysis = submission.get('ai_analysis')
            if ai_analysis:
                is_correct = ai_analysis.get('is_correct')
                subject = ai_analysis.get('subject', '未指定')
            else:
                # 从题库获取
                question_id = submission.get('question_id')
                # 确保_questions_cache不为None
                if self._questions_cache is None:
                    self._questions_cache = {}
                question = self._questions_cache.get(question_id, {})
                master_analysis = question.get('master_analysis', {})
                is_correct = master_analysis.get('is_correct')
                subject = question.get('subject', '未指定')
            
            # 统计正确性
            if is_correct is True:
                stats['correct_count'] += 1
            elif is_correct is False:
                stats['incorrect_count'] += 1
            
            # 统计学科分布
            stats['subject_distribution'][subject] += 1
            
            # 统计最近活动
            timestamp = submission.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = date.strftime('%Y-%m-%d')
                    stats['recent_activity'][date_str] += 1
                except:
                    pass
        
        # 计算正确率
        total_answered = stats['correct_count'] + stats['incorrect_count']
        stats['accuracy_rate'] = (stats['correct_count'] / total_answered * 100) if total_answered > 0 else 0
        
        return stats
    
    def get_question_details(self, question_id: str) -> Optional[Dict]:
        """获取题目详细信息"""
        self._load_all_data()
        if self._questions_cache is None:
            self._questions_cache = {}
        return self._questions_cache.get(question_id)
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        self._load_all_data()
        if self._users_cache is None:
            self._users_cache = {}
        return self._users_cache.get(user_id)
    
    def get_class_info(self, class_id: str) -> Optional[Dict]:
        """获取班级信息"""
        self._load_all_data()
        if self._classes_cache is None:
            self._classes_cache = {}
        return self._classes_cache.get(class_id)
    
    def get_student_performance(self, student_id: str) -> Dict[str, Any]:
        """获取学生学习表现"""
        submissions = self.get_user_submissions(student_id, 'student')
        stats = self.get_submission_stats(submissions)
        
        # 按学科分组统计
        subject_stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'accuracy': 0})
        
        for submission in submissions:
            ai_analysis = submission.get('ai_analysis')
            if ai_analysis:
                subject = ai_analysis.get('subject', '未指定')
                is_correct = ai_analysis.get('is_correct')
            else:
                question_id = submission.get('question_id')
                if self._questions_cache is None:
                    self._questions_cache = {}
                question = self._questions_cache.get(question_id, {})
                subject = question.get('subject', '未指定')
                is_correct = question.get('master_analysis', {}).get('is_correct')
            
            subject_stats[subject]['total'] += 1
            if is_correct is True:
                subject_stats[subject]['correct'] += 1
        
        # 计算各学科正确率
        for subject in subject_stats:
            total = subject_stats[subject]['total']
            correct = subject_stats[subject]['correct']
            subject_stats[subject]['accuracy'] = (correct / total * 100) if total > 0 else 0
        
        return {
            'overall_stats': stats,
            'subject_stats': dict(subject_stats),
            'recent_submissions': submissions[:10]  # 最近10次提交
        }
    
    def get_class_performance(self, class_id: str) -> Dict[str, Any]:
        """获取班级整体表现"""
        class_info = self.get_class_info(class_id)
        if not class_info:
            return {}
        
        students = class_info.get('students', [])
        class_stats = {
            'total_students': len(students),
            'active_students': 0,
            'average_accuracy': 0,
            'subject_performance': defaultdict(list),
            'student_performances': {}
        }
        
        total_accuracy = 0
        active_count = 0
        
        for student_id in students:
            performance = self.get_student_performance(student_id)
            if performance['overall_stats']['total_count'] > 0:
                class_stats['active_students'] += 1
                accuracy = performance['overall_stats']['accuracy_rate']
                total_accuracy += accuracy
                active_count += 1
                
                # 记录各学科表现
                for subject, stats in performance['subject_stats'].items():
                    class_stats['subject_performance'][subject].append(stats['accuracy'])
                
                class_stats['student_performances'][student_id] = performance
        
        if active_count > 0:
            class_stats['average_accuracy'] = total_accuracy / active_count
        
        return class_stats
    
    def search_submissions(self, user_id: str, role: str, 
                          subjects: List[str] = None, 
                          correctness: List[Optional[bool]] = None,
                          date_range: Tuple[str, str] = None) -> List[Dict]:
        """搜索提交记录"""
        submissions = self.get_user_submissions(user_id, role)
        
        # 应用筛选条件
        filtered = []
        for submission in submissions:
            # 获取分析结果
            ai_analysis = submission.get('ai_analysis')
            if ai_analysis:
                subject = ai_analysis.get('subject', '未指定')
                is_correct = ai_analysis.get('is_correct')
            else:
                question_id = submission.get('question_id')
                if self._questions_cache is None:
                    self._questions_cache = {}
                question = self._questions_cache.get(question_id, {})
                subject = question.get('subject', '未指定')
                is_correct = question.get('master_analysis', {}).get('is_correct')
            
            # 学科筛选
            if subjects and subject not in subjects:
                continue
            
            # 正确性筛选
            if correctness is not None and is_correct not in correctness:
                continue
            
            # 日期筛选
            if date_range:
                timestamp = submission.get('timestamp', '')
                if timestamp:
                    try:
                        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        start_date = datetime.fromisoformat(date_range[0])
                        end_date = datetime.fromisoformat(date_range[1])
                        if not (start_date <= date <= end_date):
                            continue
                    except:
                        pass
            
            filtered.append(submission)
        
        return filtered

# 全局实例
data_service = DataService() 