"""
重构的数据服务 - 使用PostgreSQL + SQLAlchemy
支持高效查询、分组和统计功能
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import pandas as pd
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text, func, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger_config import setup_logger

logger = setup_logger('data_service_v3', level=logging.INFO)

class DataServiceV3:
    """重构的数据服务类 - 使用PostgreSQL数据库"""
    
    def __init__(self, database_url: str = None):
        """
        初始化数据服务
        
        Args:
            database_url: PostgreSQL连接URL，格式：postgresql://user:password@host:port/database
        """
        if database_url is None:
            # 从环境变量或配置文件获取数据库连接信息
            database_url = self._get_database_url()
        
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
        
        # 缓存
        self._cache = {}
        self._cache_timestamp = None
        
    def _get_database_url(self) -> str:
        """获取数据库连接URL"""
        # 优先从环境变量获取
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'studyhelper')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def _initialize_database(self):
        """初始化数据库连接"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False  # 设置为True可以看到SQL语句
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("数据库连接初始化成功")
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def get_user_submissions(self, user_id: str, role: str = None, limit: int = None) -> List[Dict]:
        """
        获取用户可见的提交记录
        
        Args:
            user_id: 用户ID
            role: 用户角色
            limit: 限制返回数量
            
        Returns:
            提交记录列表
        """
        try:
            with self.get_session() as session:
                if role == 'student':
                    # 学生只能看到自己的提交
                    query = session.execute(text("""
                        SELECT s.*, sa.*, u.name as user_name, u.role as user_role
                        FROM submissions s
                        LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                        LEFT JOIN users u ON s.user_id = u.id
                        WHERE s.user_id = :user_id
                        ORDER BY s.timestamp DESC
                    """), {'user_id': user_id})
                    
                elif role == 'teacher':
                    # 教师可以看到管理班级学生的提交
                    query = session.execute(text("""
                        SELECT s.*, sa.*, u.name as user_name, u.role as user_role
                        FROM submissions s
                        LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                        LEFT JOIN users u ON s.user_id = u.id
                        WHERE u.class_id IN (
                            SELECT c.id FROM classes c 
                            WHERE c.teacher_id = :teacher_id
                        )
                        ORDER BY s.timestamp DESC
                    """), {'teacher_id': user_id})
                    
                elif role == 'grade_manager':
                    # 年级主任可以看到年级内所有学生的提交
                    query = session.execute(text("""
                        SELECT s.*, sa.*, u.name as user_name, u.role as user_role
                        FROM submissions s
                        LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                        LEFT JOIN users u ON s.user_id = u.id
                        WHERE u.grade_id = (
                            SELECT g.id FROM grades g 
                            WHERE g.manager_id = :manager_id
                        )
                        ORDER BY s.timestamp DESC
                    """), {'manager_id': user_id})
                    
                elif role == 'principal':
                    # 校长可以看到学校内所有提交
                    query = session.execute(text("""
                        SELECT s.*, sa.*, u.name as user_name, u.role as user_role
                        FROM submissions s
                        LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                        LEFT JOIN users u ON s.user_id = u.id
                        WHERE u.school_id = (
                            SELECT sch.id FROM schools sch 
                            WHERE sch.principal_id = :principal_id
                        )
                        ORDER BY s.timestamp DESC
                    """), {'principal_id': user_id})
                    
                else:
                    return []
                
                # 获取结果
                results = []
                for row in query:
                    if limit and len(results) >= limit:
                        break
                    
                    # 转换为字典格式
                    submission_dict = dict(row._mapping)
                    results.append(submission_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"获取用户提交记录失败: {e}")
            return []
    
    def get_submissions_by_user(self, user_id: str) -> List[Dict]:
        """获取指定用户的所有提交记录（兼容性方法）"""
        return self.get_user_submissions(user_id, role='student')
    
    def get_submissions_by_question(self, user_id: str, question_id: str) -> List[Dict]:
        """获取指定题目的所有提交记录"""
        try:
            with self.get_session() as session:
                query = session.execute(text("""
                    SELECT s.*, sa.*, u.name as user_name
                    FROM submissions s
                    LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE s.user_id = :user_id AND s.question_id = :question_id
                    ORDER BY s.timestamp DESC
                """), {'user_id': user_id, 'question_id': question_id})
                
                return [dict(row._mapping) for row in query]
                
        except Exception as e:
            logger.error(f"获取题目提交记录失败: {e}")
            return []
    
    def group_submissions_by_question(self, submissions: List[Dict]) -> Dict[str, List[Dict]]:
        """按题目分组提交记录"""
        grouped = defaultdict(list)
        
        for submission in submissions:
            # 确定题目ID
            question_id = submission.get('question_id')
            if not question_id:
                # 如果没有question_id，尝试从OCR文本生成
                ocr_text = submission.get('ocr_text') or submission.get('submitted_ocr_text', '')
                if ocr_text:
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
        
        stats = {
            'total_count': len(submissions),
            'correct_count': 0,
            'incorrect_count': 0,
            'subject_distribution': defaultdict(int),
            'recent_activity': defaultdict(int)
        }
        
        for submission in submissions:
            # 获取分析结果
            is_correct = submission.get('is_correct')
            subject = submission.get('subject', '未指定')
            
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
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                    stats['recent_activity'][str(date)] += 1
                except:
                    pass
        
        # 计算准确率
        if stats['total_count'] > 0:
            stats['accuracy_rate'] = round(stats['correct_count'] / stats['total_count'] * 100, 2)
        else:
            stats['accuracy_rate'] = 0
        
        # 转换defaultdict为普通dict
        stats['subject_distribution'] = dict(stats['subject_distribution'])
        stats['recent_activity'] = dict(stats['recent_activity'])
        
        return stats
    
    def get_question_details(self, question_id: str) -> Optional[Dict]:
        """获取题目详细信息"""
        try:
            with self.get_session() as session:
                query = session.execute(text("""
                    SELECT q.*, qa.*
                    FROM questions q
                    LEFT JOIN question_analyses qa ON q.id = qa.question_id
                    WHERE q.id = :question_id
                """), {'question_id': question_id})
                
                row = query.fetchone()
                return dict(row._mapping) if row else None
                
        except Exception as e:
            logger.error(f"获取题目详情失败: {e}")
            return None
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        try:
            with self.get_session() as session:
                query = session.execute(text("""
                    SELECT u.*, s.name as school_name, g.name as grade_name, c.name as class_name
                    FROM users u
                    LEFT JOIN schools s ON u.school_id = s.id
                    LEFT JOIN grades g ON u.grade_id = g.id
                    LEFT JOIN classes c ON u.class_id = c.id
                    WHERE u.id = :user_id
                """), {'user_id': user_id})
                
                row = query.fetchone()
                return dict(row._mapping) if row else None
                
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    def get_class_info(self, class_id: str) -> Optional[Dict]:
        """获取班级信息"""
        try:
            with self.get_session() as session:
                query = session.execute(text("""
                    SELECT c.*, g.name as grade_name, s.name as school_name,
                           u.name as teacher_name
                    FROM classes c
                    LEFT JOIN grades g ON c.grade_id = g.id
                    LEFT JOIN schools s ON c.school_id = s.id
                    LEFT JOIN users u ON c.teacher_id = u.id
                    WHERE c.id = :class_id
                """), {'class_id': class_id})
                
                row = query.fetchone()
                return dict(row._mapping) if row else None
                
        except Exception as e:
            logger.error(f"获取班级信息失败: {e}")
            return None
    
    def get_student_performance(self, student_id: str) -> Dict[str, Any]:
        """获取学生表现数据"""
        try:
            with self.get_session() as session:
                # 获取基础统计
                stats_query = session.execute(text("""
                    SELECT 
                        COUNT(s.id) as total_submissions,
                        COUNT(sa.id) as analyzed_submissions,
                        COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct_submissions,
                        CASE 
                            WHEN COUNT(sa.id) > 0 THEN 
                                ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id) * 100, 2)
                            ELSE 0 
                        END as accuracy_rate
                    FROM users u
                    LEFT JOIN submissions s ON u.id = s.user_id
                    LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                    WHERE u.id = :student_id
                """), {'student_id': student_id})
                
                stats = dict(stats_query.fetchone()._mapping)
                
                # 获取学科分布
                subject_query = session.execute(text("""
                    SELECT sa.subject, COUNT(*) as count
                    FROM submissions s
                    JOIN submission_analyses sa ON s.id = sa.submission_id
                    WHERE s.user_id = :student_id
                    GROUP BY sa.subject
                    ORDER BY count DESC
                """), {'student_id': student_id})
                
                subject_distribution = {row.subject: row.count for row in subject_query}
                
                # 获取最近活动
                recent_query = session.execute(text("""
                    SELECT DATE(s.timestamp) as date, COUNT(*) as count
                    FROM submissions s
                    WHERE s.user_id = :student_id
                    AND s.timestamp >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(s.timestamp)
                    ORDER BY date DESC
                """), {'student_id': student_id})
                
                recent_activity = {str(row.date): row.count for row in recent_query}
                
                return {
                    **stats,
                    'subject_distribution': subject_distribution,
                    'recent_activity': recent_activity
                }
                
        except Exception as e:
            logger.error(f"获取学生表现数据失败: {e}")
            return {
                'total_submissions': 0,
                'analyzed_submissions': 0,
                'correct_submissions': 0,
                'accuracy_rate': 0,
                'subject_distribution': {},
                'recent_activity': {}
            }
    
    def get_class_performance(self, class_id: str) -> Dict[str, Any]:
        """获取班级表现数据"""
        try:
            with self.get_session() as session:
                # 获取班级基础统计
                stats_query = session.execute(text("""
                    SELECT 
                        COUNT(DISTINCT u.id) as student_count,
                        COUNT(s.id) as total_submissions,
                        COUNT(sa.id) as analyzed_submissions,
                        COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct_submissions,
                        CASE 
                            WHEN COUNT(sa.id) > 0 THEN 
                                ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id) * 100, 2)
                            ELSE 0 
                        END as accuracy_rate
                    FROM classes c
                    LEFT JOIN users u ON c.id = u.class_id AND u.role = 'student'
                    LEFT JOIN submissions s ON u.id = s.user_id
                    LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                    WHERE c.id = :class_id
                """), {'class_id': class_id})
                
                stats = dict(stats_query.fetchone()._mapping)
                
                # 获取学科表现
                subject_query = session.execute(text("""
                    SELECT 
                        sa.subject,
                        COUNT(*) as total,
                        COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct,
                        CASE 
                            WHEN COUNT(*) > 0 THEN 
                                ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(*) * 100, 2)
                            ELSE 0 
                        END as accuracy
                    FROM classes c
                    JOIN users u ON c.id = u.class_id AND u.role = 'student'
                    JOIN submissions s ON u.id = s.user_id
                    JOIN submission_analyses sa ON s.id = sa.submission_id
                    WHERE c.id = :class_id
                    GROUP BY sa.subject
                    ORDER BY total DESC
                """), {'class_id': class_id})
                
                subject_performance = {}
                for row in subject_query:
                    subject_performance[row.subject] = {
                        'total': row.total,
                        'correct': row.correct,
                        'accuracy': row.accuracy
                    }
                
                # 获取需要关注的学生
                attention_query = session.execute(text("""
                    SELECT u.id, u.name, 
                           COUNT(s.id) as submission_count,
                           COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct_count,
                           CASE 
                               WHEN COUNT(sa.id) > 0 THEN 
                                   ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id) * 100, 2)
                               ELSE 0 
                           END as accuracy_rate
                    FROM classes c
                    JOIN users u ON c.id = u.class_id AND u.role = 'student'
                    LEFT JOIN submissions s ON u.id = s.user_id
                    LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                    WHERE c.id = :class_id
                    GROUP BY u.id, u.name
                    HAVING COUNT(sa.id) > 0 AND 
                           (COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id)) < 0.7
                    ORDER BY accuracy_rate ASC
                    LIMIT 5
                """), {'class_id': class_id})
                
                needs_attention = [
                    {
                        'id': row.id,
                        'name': row.name,
                        'submission_count': row.submission_count,
                        'correct_count': row.correct_count,
                        'accuracy_rate': row.accuracy_rate
                    }
                    for row in attention_query
                ]
                
                return {
                    **stats,
                    'subject_performance': subject_performance,
                    'needs_attention_students': needs_attention
                }
                
        except Exception as e:
            logger.error(f"获取班级表现数据失败: {e}")
            return {
                'student_count': 0,
                'total_submissions': 0,
                'analyzed_submissions': 0,
                'correct_submissions': 0,
                'accuracy_rate': 0,
                'subject_performance': {},
                'needs_attention_students': []
            }
    
    def search_submissions(self, user_id: str, role: str, 
                          subjects: List[str] = None, 
                          correctness: List[Optional[bool]] = None,
                          date_range: Tuple[str, str] = None,
                          limit: int = 100) -> List[Dict]:
        """
        搜索提交记录
        
        Args:
            user_id: 用户ID
            role: 用户角色
            subjects: 学科过滤
            correctness: 正确性过滤
            date_range: 日期范围 (start_date, end_date)
            limit: 限制返回数量
            
        Returns:
            提交记录列表
        """
        try:
            with self.get_session() as session:
                # 构建基础查询
                base_query = """
                    SELECT s.*, sa.*, u.name as user_name, u.role as user_role
                    FROM submissions s
                    LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE 1=1
                """
                
                params = {}
                
                # 根据角色添加权限过滤
                if role == 'student':
                    base_query += " AND s.user_id = :user_id"
                    params['user_id'] = user_id
                elif role == 'teacher':
                    base_query += """ AND u.class_id IN (
                        SELECT c.id FROM classes c WHERE c.teacher_id = :teacher_id
                    )"""
                    params['teacher_id'] = user_id
                elif role == 'grade_manager':
                    base_query += """ AND u.grade_id = (
                        SELECT g.id FROM grades g WHERE g.manager_id = :manager_id
                    )"""
                    params['manager_id'] = user_id
                elif role == 'principal':
                    base_query += """ AND u.school_id = (
                        SELECT sch.id FROM schools sch WHERE sch.principal_id = :principal_id
                    )"""
                    params['principal_id'] = user_id
                
                # 添加过滤条件
                if subjects:
                    placeholders = ','.join([f"'{subject}'" for subject in subjects])
                    base_query += f" AND sa.subject IN ({placeholders})"
                
                if correctness is not None:
                    if len(correctness) == 1:
                        base_query += " AND sa.is_correct = :correctness"
                        params['correctness'] = correctness[0]
                    else:
                        placeholders = ','.join(['true' if c else 'false' for c in correctness])
                        base_query += f" AND sa.is_correct IN ({placeholders})"
                
                if date_range:
                    base_query += " AND s.timestamp BETWEEN :start_date AND :end_date"
                    params['start_date'] = date_range[0]
                    params['end_date'] = date_range[1]
                
                # 添加排序和限制
                base_query += " ORDER BY s.timestamp DESC"
                if limit:
                    base_query += f" LIMIT {limit}"
                
                query = session.execute(text(base_query), params)
                return [dict(row._mapping) for row in query]
                
        except Exception as e:
            logger.error(f"搜索提交记录失败: {e}")
            return []
    
    def get_mistake_book_entries(self, user_id: str) -> List[Dict]:
        """获取用户的错题本条目"""
        try:
            with self.get_session() as session:
                query = session.execute(text("""
                    SELECT mbe.*, s.submitted_ocr_text, sa.subject, sa.knowledge_point,
                           q.canonical_text as question_text
                    FROM mistake_book_entries mbe
                    LEFT JOIN submissions s ON mbe.submission_id = s.id
                    LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                    LEFT JOIN questions q ON mbe.question_id = q.id
                    WHERE mbe.user_id = :user_id
                    ORDER BY mbe.created_at DESC
                """), {'user_id': user_id})
                
                return [dict(row._mapping) for row in query]
                
        except Exception as e:
            logger.error(f"获取错题本条目失败: {e}")
            return []
    
    def create_mistake_book_entry(self, user_id: str, submission_id: str, 
                                 question_id: str = None, subject: str = None,
                                 knowledge_point: str = None) -> bool:
        """创建错题本条目"""
        try:
            with self.get_session() as session:
                session.execute(text("""
                    INSERT INTO mistake_book_entries 
                    (user_id, submission_id, question_id, subject, knowledge_point, 
                     difficulty_level, mastery_level)
                    VALUES (:user_id, :submission_id, :question_id, :subject, :knowledge_point, 1, 1)
                    ON CONFLICT (user_id, submission_id) DO NOTHING
                """), {
                    'user_id': user_id,
                    'submission_id': submission_id,
                    'question_id': question_id,
                    'subject': subject,
                    'knowledge_point': knowledge_point
                })
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"创建错题本条目失败: {e}")
            return False
    
    def update_mistake_book_entry(self, entry_id: str, mastery_level: int = None,
                                 notes: str = None, tags: List[str] = None) -> bool:
        """更新错题本条目"""
        try:
            with self.get_session() as session:
                update_fields = []
                params = {'entry_id': entry_id}
                
                if mastery_level is not None:
                    update_fields.append("mastery_level = :mastery_level")
                    params['mastery_level'] = mastery_level
                
                if notes is not None:
                    update_fields.append("notes = :notes")
                    params['notes'] = notes
                
                if tags is not None:
                    update_fields.append("tags = :tags")
                    params['tags'] = json.dumps(tags, ensure_ascii=False)
                
                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    query = f"""
                        UPDATE mistake_book_entries 
                        SET {', '.join(update_fields)}
                        WHERE id = :entry_id
                    """
                    session.execute(text(query), params)
                    session.commit()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"更新错题本条目失败: {e}")
            return False
    
    def get_analytics_data(self, user_id: str, role: str, 
                          start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """获取分析数据"""
        try:
            with self.get_session() as session:
                # 构建日期过滤条件
                date_filter = ""
                params = {}
                if start_date and end_date:
                    date_filter = "AND s.timestamp BETWEEN :start_date AND :end_date"
                    params['start_date'] = start_date
                    params['end_date'] = end_date
                
                # 根据角色构建权限过滤
                if role == 'student':
                    user_filter = "AND s.user_id = :user_id"
                    params['user_id'] = user_id
                elif role == 'teacher':
                    user_filter = """AND u.class_id IN (
                        SELECT c.id FROM classes c WHERE c.teacher_id = :teacher_id
                    )"""
                    params['teacher_id'] = user_id
                elif role == 'grade_manager':
                    user_filter = """AND u.grade_id = (
                        SELECT g.id FROM grades g WHERE g.manager_id = :manager_id
                    )"""
                    params['manager_id'] = user_id
                elif role == 'principal':
                    user_filter = """AND u.school_id = (
                        SELECT sch.id FROM schools sch WHERE sch.principal_id = :principal_id
                    )"""
                    params['principal_id'] = user_id
                else:
                    return {}
                
                # 获取总体统计
                stats_query = session.execute(text(f"""
                    SELECT 
                        COUNT(s.id) as total_submissions,
                        COUNT(sa.id) as analyzed_submissions,
                        COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct_submissions,
                        CASE 
                            WHEN COUNT(sa.id) > 0 THEN 
                                ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id) * 100, 2)
                            ELSE 0 
                        END as accuracy_rate
                    FROM submissions s
                    LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE 1=1 {user_filter} {date_filter}
                """), params)
                
                stats = dict(stats_query.fetchone()._mapping)
                
                # 获取学科分布
                subject_query = session.execute(text(f"""
                    SELECT sa.subject, COUNT(*) as count
                    FROM submissions s
                    JOIN submission_analyses sa ON s.id = sa.submission_id
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE 1=1 {user_filter} {date_filter}
                    GROUP BY sa.subject
                    ORDER BY count DESC
                """), params)
                
                subject_distribution = {row.subject: row.count for row in subject_query}
                
                # 获取每日活动
                daily_query = session.execute(text(f"""
                    SELECT DATE(s.timestamp) as date, COUNT(*) as count
                    FROM submissions s
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE 1=1 {user_filter} {date_filter}
                    GROUP BY DATE(s.timestamp)
                    ORDER BY date DESC
                    LIMIT 30
                """), params)
                
                daily_activity = {str(row.date): row.count for row in daily_query}
                
                return {
                    **stats,
                    'subject_distribution': subject_distribution,
                    'daily_activity': daily_activity
                }
                
        except Exception as e:
            logger.error(f"获取分析数据失败: {e}")
            return {}
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")


# 为了保持向后兼容性，创建一个别名
DataService = DataServiceV3 