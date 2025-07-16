#!/usr/bin/env python3
"""
StudyHelper Data Migration Script
将现有的JSON文件数据迁移到PostgreSQL数据库

使用方法:
    python scripts/migrate_data.py --config database.ini
    python scripts/migrate_data.py --dry-run  # 仅验证数据，不执行迁移
"""

import sys
import os
import json
import argparse
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import configparser
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger_config import setup_logger

class DataMigrator:
    """数据迁移器，负责将JSON数据迁移到PostgreSQL"""
    
    def __init__(self, db_config: Dict[str, str], dry_run: bool = False):
        self.db_config = db_config
        self.dry_run = dry_run
        self.logger = setup_logger('data_migrator', level=logging.INFO)
        self.connection = None
        self.cursor = None
        
        # 迁移统计
        self.migration_stats = {
            'schools': {'processed': 0, 'errors': 0},
            'grades': {'processed': 0, 'errors': 0},
            'classes': {'processed': 0, 'errors': 0},
            'users': {'processed': 0, 'errors': 0},
            'questions': {'processed': 0, 'errors': 0},
            'submissions': {'processed': 0, 'errors': 0},
            'question_images': {'processed': 0, 'errors': 0}
        }
    
    def connect_database(self):
        """连接到PostgreSQL数据库"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            self.logger.info("成功连接到PostgreSQL数据库")
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect_database(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.logger.info("数据库连接已关闭")
    
    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """加载JSON文件数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"成功加载JSON文件: {file_path}")
            return data
        except Exception as e:
            self.logger.error(f"加载JSON文件失败 {file_path}: {e}")
            raise
    
    def validate_school_data(self, data: Dict[str, Any]) -> bool:
        """验证学校数据格式"""
        required_fields = ['school_info', 'grades', 'classes', 'users']
        for field in required_fields:
            if field not in data:
                self.logger.error(f"缺少必需字段: {field}")
                return False
        return True
    
    def migrate_schools(self, school_data: Dict[str, Any]):
        """迁移学校数据"""
        try:
            school_info = school_data['school_info']
            
            # 准备学校数据
            school_record = {
                'id': school_info['id'],
                'name': school_info['name'],
                'address': school_info.get('address'),
                'phone': school_info.get('phone'),
                'email': school_info.get('email'),
                'principal_id': school_info.get('principal_id'),
                'total_students': school_info.get('total_students', 0),
                'total_teachers': school_info.get('total_teachers', 0),
                'total_classes': school_info.get('total_classes', 0),
                'total_grades': school_info.get('total_grades', 0),
                'created_at': school_info.get('created_at'),
                'updated_at': school_info.get('updated_at')
            }
            
            if not self.dry_run:
                # 插入学校数据
                self.cursor.execute("""
                    INSERT INTO schools (id, name, address, phone, email, principal_id, 
                                       total_students, total_teachers, total_classes, total_grades, 
                                       created_at, updated_at)
                    VALUES (%(id)s, %(name)s, %(address)s, %(phone)s, %(email)s, %(principal_id)s,
                           %(total_students)s, %(total_teachers)s, %(total_classes)s, %(total_grades)s,
                           %(created_at)s, %(updated_at)s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        address = EXCLUDED.address,
                        phone = EXCLUDED.phone,
                        email = EXCLUDED.email,
                        principal_id = EXCLUDED.principal_id,
                        total_students = EXCLUDED.total_students,
                        total_teachers = EXCLUDED.total_teachers,
                        total_classes = EXCLUDED.total_classes,
                        total_grades = EXCLUDED.total_grades,
                        updated_at = CURRENT_TIMESTAMP
                """, school_record)
            
            self.migration_stats['schools']['processed'] += 1
            self.logger.info(f"成功迁移学校: {school_info['name']}")
            
        except Exception as e:
            self.migration_stats['schools']['errors'] += 1
            self.logger.error(f"迁移学校数据失败: {e}")
    
    def migrate_grades(self, grades_data: List[Dict[str, Any]]):
        """迁移年级数据"""
        for grade in grades_data:
            try:
                grade_record = {
                    'id': grade['id'],
                    'name': grade['name'],
                    'grade_level': grade['grade_level'],
                    'manager_id': grade.get('manager_id'),
                    'school_id': grade['school_id'],
                    'total_classes': grade.get('total_classes', 0),
                    'total_students': grade.get('total_students', 0),
                    'total_teachers': grade.get('total_teachers', 0),
                    'average_accuracy': grade.get('average_accuracy', 0.00),
                    'created_at': grade.get('created_at'),
                    'updated_at': grade.get('updated_at')
                }
                
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO grades (id, name, grade_level, manager_id, school_id,
                                          total_classes, total_students, total_teachers, 
                                          average_accuracy, created_at, updated_at)
                        VALUES (%(id)s, %(name)s, %(grade_level)s, %(manager_id)s, %(school_id)s,
                               %(total_classes)s, %(total_students)s, %(total_teachers)s,
                               %(average_accuracy)s, %(created_at)s, %(updated_at)s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            grade_level = EXCLUDED.grade_level,
                            manager_id = EXCLUDED.manager_id,
                            total_classes = EXCLUDED.total_classes,
                            total_students = EXCLUDED.total_students,
                            total_teachers = EXCLUDED.total_teachers,
                            average_accuracy = EXCLUDED.average_accuracy,
                            updated_at = CURRENT_TIMESTAMP
                    """, grade_record)
                
                self.migration_stats['grades']['processed'] += 1
                self.logger.info(f"成功迁移年级: {grade['name']}")
                
            except Exception as e:
                self.migration_stats['grades']['errors'] += 1
                self.logger.error(f"迁移年级数据失败 {grade.get('id', 'unknown')}: {e}")
    
    def migrate_classes(self, classes_data: List[Dict[str, Any]]):
        """迁移班级数据"""
        for class_data in classes_data:
            try:
                class_record = {
                    'id': class_data['id'],
                    'name': class_data['name'],
                    'grade_id': class_data['grade_id'],
                    'teacher_id': class_data.get('teacher_id'),
                    'school_id': class_data['school_id'],
                    'student_count': class_data.get('student_count', 0),
                    'average_accuracy': class_data.get('average_accuracy', 0.00),
                    'subject_performance': json.dumps(class_data.get('subject_performance', {}), ensure_ascii=False),
                    'needs_attention_students': json.dumps(class_data.get('needs_attention_students', []), ensure_ascii=False),
                    'created_at': class_data.get('created_at'),
                    'updated_at': class_data.get('updated_at')
                }
                
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO classes (id, name, grade_id, teacher_id, school_id,
                                           student_count, average_accuracy, subject_performance,
                                           needs_attention_students, created_at, updated_at)
                        VALUES (%(id)s, %(name)s, %(grade_id)s, %(teacher_id)s, %(school_id)s,
                               %(student_count)s, %(average_accuracy)s, %(subject_performance)s,
                               %(needs_attention_students)s, %(created_at)s, %(updated_at)s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            grade_id = EXCLUDED.grade_id,
                            teacher_id = EXCLUDED.teacher_id,
                            student_count = EXCLUDED.student_count,
                            average_accuracy = EXCLUDED.average_accuracy,
                            subject_performance = EXCLUDED.subject_performance,
                            needs_attention_students = EXCLUDED.needs_attention_students,
                            updated_at = CURRENT_TIMESTAMP
                    """, class_record)
                
                self.migration_stats['classes']['processed'] += 1
                self.logger.info(f"成功迁移班级: {class_data['name']}")
                
            except Exception as e:
                self.migration_stats['classes']['errors'] += 1
                self.logger.error(f"迁移班级数据失败 {class_data.get('id', 'unknown')}: {e}")
    
    def migrate_users(self, users_data: List[Dict[str, Any]]):
        """迁移用户数据"""
        for user in users_data:
            try:
                # 生成密码哈希和盐（临时密码为123456）
                password_hash = hashlib.sha256("123456".encode()).hexdigest()
                salt = hashlib.md5(user['id'].encode()).hexdigest()
                
                user_record = {
                    'id': user['id'],
                    'name': user['name'],
                    'role': user['role'],
                    'email': user['email'],
                    'phone': user.get('phone'),
                    'password_hash': password_hash,
                    'salt': salt,
                    'school_id': user.get('school_id'),
                    'grade_id': user.get('grade_id'),
                    'class_id': user.get('class_id'),
                    'student_number': user.get('student_number'),
                    'gender': user.get('gender'),
                    'birth_date': user.get('birth_date'),
                    'parent_phone': user.get('parent_phone'),
                    'subject_teach': json.dumps(user.get('subject_teach', []), ensure_ascii=False),
                    'manages_classes': json.dumps(user.get('manages_classes', []), ensure_ascii=False),
                    'permissions': json.dumps(user.get('permissions', []), ensure_ascii=False),
                    'learning_stats': json.dumps(user.get('learning_stats', {}), ensure_ascii=False),
                    'last_login': user.get('last_login'),
                    'created_at': user.get('created_at'),
                    'updated_at': user.get('updated_at')
                }
                
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO users (id, name, role, email, phone, password_hash, salt,
                                         school_id, grade_id, class_id, student_number, gender,
                                         birth_date, parent_phone, subject_teach, manages_classes,
                                         permissions, learning_stats, last_login, created_at, updated_at)
                        VALUES (%(id)s, %(name)s, %(role)s, %(email)s, %(phone)s, %(password_hash)s, %(salt)s,
                               %(school_id)s, %(grade_id)s, %(class_id)s, %(student_number)s, %(gender)s,
                               %(birth_date)s, %(parent_phone)s, %(subject_teach)s, %(manages_classes)s,
                               %(permissions)s, %(learning_stats)s, %(last_login)s, %(created_at)s, %(updated_at)s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            role = EXCLUDED.role,
                            email = EXCLUDED.email,
                            phone = EXCLUDED.phone,
                            school_id = EXCLUDED.school_id,
                            grade_id = EXCLUDED.grade_id,
                            class_id = EXCLUDED.class_id,
                            student_number = EXCLUDED.student_number,
                            gender = EXCLUDED.gender,
                            birth_date = EXCLUDED.birth_date,
                            parent_phone = EXCLUDED.parent_phone,
                            subject_teach = EXCLUDED.subject_teach,
                            manages_classes = EXCLUDED.manages_classes,
                            permissions = EXCLUDED.permissions,
                            learning_stats = EXCLUDED.learning_stats,
                            last_login = EXCLUDED.last_login,
                            updated_at = CURRENT_TIMESTAMP
                    """, user_record)
                
                self.migration_stats['users']['processed'] += 1
                self.logger.info(f"成功迁移用户: {user['name']} ({user['role']})")
                
            except Exception as e:
                self.migration_stats['users']['errors'] += 1
                self.logger.error(f"迁移用户数据失败 {user.get('id', 'unknown')}: {e}")
    
    def migrate_questions(self, question_bank_data: Dict[str, Any]):
        """迁移题库数据"""
        for question_id, question_data in question_bank_data.items():
            try:
                question_record = {
                    'id': question_id,
                    'canonical_text': question_data['canonical_text'],
                    'subject': question_data['subject'],
                    'first_submission_image': question_data.get('first_submission_image'),
                    'first_seen_timestamp': question_data.get('first_seen_timestamp'),
                    'created_at': question_data.get('first_seen_timestamp'),
                    'updated_at': question_data.get('first_seen_timestamp')
                }
                
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO questions (id, canonical_text, subject, first_submission_image,
                                             first_seen_timestamp, created_at, updated_at)
                        VALUES (%(id)s, %(canonical_text)s, %(subject)s, %(first_submission_image)s,
                               %(first_seen_timestamp)s, %(created_at)s, %(updated_at)s)
                        ON CONFLICT (id) DO UPDATE SET
                            canonical_text = EXCLUDED.canonical_text,
                            subject = EXCLUDED.subject,
                            first_submission_image = EXCLUDED.first_submission_image,
                            updated_at = CURRENT_TIMESTAMP
                    """, question_record)
                    
                    # 迁移题目分析数据
                    if 'master_analysis' in question_data:
                        analysis = question_data['master_analysis']
                        analysis_record = {
                            'question_id': question_id,
                            'subject': analysis['subject'],
                            'is_correct': analysis.get('is_correct'),
                            'error_analysis': analysis.get('error_analysis'),
                            'correct_answer': analysis.get('correct_answer'),
                            'solution_steps': analysis.get('solution_steps'),
                            'knowledge_point': analysis.get('knowledge_point'),
                            'common_mistakes': analysis.get('common_mistakes')
                        }
                        
                        self.cursor.execute("""
                            INSERT INTO question_analyses (question_id, subject, is_correct, error_analysis,
                                                         correct_answer, solution_steps, knowledge_point, common_mistakes)
                            VALUES (%(question_id)s, %(subject)s, %(is_correct)s, %(error_analysis)s,
                                   %(correct_answer)s, %(solution_steps)s, %(knowledge_point)s, %(common_mistakes)s)
                            ON CONFLICT (question_id) DO UPDATE SET
                                subject = EXCLUDED.subject,
                                is_correct = EXCLUDED.is_correct,
                                error_analysis = EXCLUDED.error_analysis,
                                correct_answer = EXCLUDED.correct_answer,
                                solution_steps = EXCLUDED.solution_steps,
                                knowledge_point = EXCLUDED.knowledge_point,
                                common_mistakes = EXCLUDED.common_mistakes,
                                updated_at = CURRENT_TIMESTAMP
                        """, analysis_record)
                
                self.migration_stats['questions']['processed'] += 1
                self.logger.info(f"成功迁移题目: {question_id[:8]}...")
                
            except Exception as e:
                self.migration_stats['questions']['errors'] += 1
                self.logger.error(f"迁移题目数据失败 {question_id}: {e}")
    
    def migrate_submissions(self, submissions_data: List[Dict[str, Any]]):
        """迁移提交历史数据"""
        for submission in submissions_data:
            try:
                submission_record = {
                    'id': submission['submission_id'],
                    'user_id': submission['user_id'],
                    'question_id': submission.get('question_id'),
                    'submitted_ocr_text': submission.get('submitted_ocr_text') or submission.get('ocr_text'),
                    'image_path': submission.get('image_path'),
                    'subject': submission.get('subject'),
                    'timestamp': submission['timestamp'],
                    'processing_status': 'completed'
                }
                
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO submissions (id, user_id, question_id, submitted_ocr_text,
                                               image_path, subject, timestamp, processing_status)
                        VALUES (%(id)s, %(user_id)s, %(question_id)s, %(submitted_ocr_text)s,
                               %(image_path)s, %(subject)s, %(timestamp)s, %(processing_status)s)
                        ON CONFLICT (id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            question_id = EXCLUDED.question_id,
                            submitted_ocr_text = EXCLUDED.submitted_ocr_text,
                            image_path = EXCLUDED.image_path,
                            subject = EXCLUDED.subject,
                            timestamp = EXCLUDED.timestamp,
                            processing_status = EXCLUDED.processing_status
                    """, submission_record)
                    
                    # 迁移提交分析数据
                    if 'ai_analysis' in submission:
                        analysis = submission['ai_analysis']
                        analysis_record = {
                            'submission_id': submission['submission_id'],
                            'subject': analysis['subject'],
                            'is_correct': analysis['is_correct'],
                            'error_analysis': analysis.get('error_analysis'),
                            'correct_answer': analysis.get('correct_answer'),
                            'solution_steps': analysis.get('solution_steps'),
                            'knowledge_point': analysis.get('knowledge_point'),
                            'common_mistakes': analysis.get('common_mistakes')
                        }
                        
                        self.cursor.execute("""
                            INSERT INTO submission_analyses (submission_id, subject, is_correct, error_analysis,
                                                           correct_answer, solution_steps, knowledge_point, common_mistakes)
                            VALUES (%(submission_id)s, %(subject)s, %(is_correct)s, %(error_analysis)s,
                                   %(correct_answer)s, %(solution_steps)s, %(knowledge_point)s, %(common_mistakes)s)
                            ON CONFLICT (submission_id) DO UPDATE SET
                                subject = EXCLUDED.subject,
                                is_correct = EXCLUDED.is_correct,
                                error_analysis = EXCLUDED.error_analysis,
                                correct_answer = EXCLUDED.correct_answer,
                                solution_steps = EXCLUDED.solution_steps,
                                knowledge_point = EXCLUDED.knowledge_point,
                                common_mistakes = EXCLUDED.common_mistakes
                        """, analysis_record)
                
                self.migration_stats['submissions']['processed'] += 1
                self.logger.info(f"成功迁移提交: {submission['submission_id'][:8]}...")
                
            except Exception as e:
                self.migration_stats['submissions']['errors'] += 1
                self.logger.error(f"迁移提交数据失败 {submission.get('submission_id', 'unknown')}: {e}")
    
    def migrate_question_images(self, phash_data: Dict[str, Any]):
        """迁移题目图片数据"""
        for phash, question_id in phash_data.items():
            try:
                image_record = {
                    'question_id': question_id,
                    'image_path': f"data/submissions/{question_id[:8]}.png",  # 假设路径
                    'perceptual_hash': phash,
                    'created_at': datetime.now()
                }
                
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO question_images (question_id, image_path, perceptual_hash, created_at)
                        VALUES (%(question_id)s, %(image_path)s, %(perceptual_hash)s, %(created_at)s)
                        ON CONFLICT (perceptual_hash) DO UPDATE SET
                            question_id = EXCLUDED.question_id,
                            image_path = EXCLUDED.image_path
                    """, image_record)
                
                self.migration_stats['question_images']['processed'] += 1
                self.logger.info(f"成功迁移题目图片: {phash}")
                
            except Exception as e:
                self.migration_stats['question_images']['errors'] += 1
                self.logger.error(f"迁移题目图片失败 {phash}: {e}")
    
    def run_migration(self, data_dir: str):
        """执行完整的数据迁移"""
        try:
            self.logger.info("开始数据迁移...")
            
            # 1. 迁移学校数据
            school_data_path = os.path.join(data_dir, 'school_data_v2.json')
            if os.path.exists(school_data_path):
                self.logger.info("迁移学校数据...")
                school_data = self.load_json_data(school_data_path)
                if self.validate_school_data(school_data):
                    self.migrate_schools(school_data)
                    self.migrate_grades(school_data['grades'])
                    self.migrate_classes(school_data['classes'])
                    self.migrate_users(school_data['users'])
            
            # 2. 迁移题库数据
            question_bank_path = os.path.join(data_dir, 'question_bank.json')
            if os.path.exists(question_bank_path):
                self.logger.info("迁移题库数据...")
                question_bank_data = self.load_json_data(question_bank_path)
                self.migrate_questions(question_bank_data)
            
            # 3. 迁移提交历史数据
            submission_history_path = os.path.join(data_dir, 'submission_history.json')
            if os.path.exists(submission_history_path):
                self.logger.info("迁移提交历史数据...")
                submission_history_data = self.load_json_data(submission_history_path)
                self.migrate_submissions(submission_history_data)
            
            # 4. 迁移题目图片数据
            phash_path = os.path.join(data_dir, 'phash_to_question_id.json')
            if os.path.exists(phash_path):
                self.logger.info("迁移题目图片数据...")
                phash_data = self.load_json_data(phash_path)
                self.migrate_question_images(phash_data)
            
            # 提交事务
            if not self.dry_run:
                self.connection.commit()
                self.logger.info("数据迁移完成，事务已提交")
            else:
                self.logger.info("数据验证完成（dry-run模式）")
            
            # 输出迁移统计
            self.print_migration_stats()
            
        except Exception as e:
            if not self.dry_run and self.connection:
                self.connection.rollback()
                self.logger.error("数据迁移失败，事务已回滚")
            self.logger.error(f"数据迁移过程中发生错误: {e}")
            raise
    
    def print_migration_stats(self):
        """打印迁移统计信息"""
        self.logger.info("=" * 50)
        self.logger.info("数据迁移统计")
        self.logger.info("=" * 50)
        
        for table, stats in self.migration_stats.items():
            self.logger.info(f"{table:20} | 成功: {stats['processed']:4d} | 错误: {stats['errors']:4d}")
        
        total_processed = sum(stats['processed'] for stats in self.migration_stats.values())
        total_errors = sum(stats['errors'] for stats in self.migration_stats.values())
        
        self.logger.info("-" * 50)
        self.logger.info(f"总计: 成功 {total_processed} 条记录, 错误 {total_errors} 条记录")
        
        if total_errors > 0:
            self.logger.warning(f"有 {total_errors} 条记录迁移失败，请检查日志")
        else:
            self.logger.info("所有数据迁移成功！")


def load_database_config(config_file: str) -> Dict[str, str]:
    """从配置文件加载数据库配置"""
    config = configparser.ConfigParser()
    config.read(config_file)
    
    if 'postgresql' not in config:
        raise ValueError("配置文件中缺少 [postgresql] 部分")
    
    return {
        'host': config['postgresql']['host'],
        'port': config['postgresql']['port'],
        'database': config['postgresql']['database'],
        'user': config['postgresql']['user'],
        'password': config['postgresql']['password']
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='StudyHelper数据迁移工具')
    parser.add_argument('--config', default='database.ini', help='数据库配置文件路径')
    parser.add_argument('--data-dir', default='data', help='JSON数据文件目录')
    parser.add_argument('--dry-run', action='store_true', help='仅验证数据，不执行迁移')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细日志输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    try:
        # 加载数据库配置
        db_config = load_database_config(args.config)
        
        # 创建迁移器
        migrator = DataMigrator(db_config, args.dry_run)
        
        # 连接数据库
        migrator.connect_database()
        
        # 执行迁移
        migrator.run_migration(args.data_dir)
        
    except Exception as e:
        print(f"迁移失败: {e}")
        sys.exit(1)
    finally:
        if 'migrator' in locals():
            migrator.disconnect_database()


if __name__ == '__main__':
    main() 