"""
测试升级版用户管理模块 (user_management_v2.py)
验证四类用户角色的管理功能和权限控制
"""

import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_management_v2 import UserManagementV2

class TestUserManagementV2(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建临时测试数据文件
        cls.test_data = {
            "school_info": {
                "id": "school_01",
                "name": "测试学校",
                "address": "测试地址",
                "phone": "010-12345678",
                "email": "test@school.edu.cn",
                "principal_id": "principal_01",
                "total_students": 4,
                "total_teachers": 2,
                "total_classes": 2,
                "total_grades": 1,
                "created_at": "2025-01-01",
                "updated_at": "2025-07-12"
            },
            "grades": [
                {
                    "id": "grade_05",
                    "name": "五年级",
                    "grade_level": 5,
                    "manager_id": "grade_manager_01",
                    "school_id": "school_01",
                    "total_classes": 2,
                    "total_students": 4,
                    "total_teachers": 2,
                    "average_accuracy": 78.5,
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                }
            ],
            "classes": [
                {
                    "id": "class_01",
                    "name": "五年级一班",
                    "grade_id": "grade_05",
                    "teacher_id": "teacher_01",
                    "school_id": "school_01",
                    "student_count": 2,
                    "average_accuracy": 82.0,
                    "subject_performance": {
                        "数学": {"average": 85.0, "weak_points": ["分数计算"]},
                        "语文": {"average": 88.0, "weak_points": []}
                    },
                    "needs_attention_students": [],
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "class_02",
                    "name": "五年级二班",
                    "grade_id": "grade_05",
                    "teacher_id": "teacher_02",
                    "school_id": "school_01",
                    "student_count": 2,
                    "average_accuracy": 75.0,
                    "subject_performance": {
                        "数学": {"average": 78.0, "weak_points": ["几何"]},
                        "语文": {"average": 82.0, "weak_points": ["阅读理解"]}
                    },
                    "needs_attention_students": [],
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                }
            ],
            "users": [
                {
                    "id": "principal_01",
                    "name": "王校长",
                    "role": "principal",
                    "school_id": "school_01",
                    "email": "principal@school.edu.cn",
                    "phone": "13800138001",
                    "permissions": ["school_management", "grade_management", "teacher_management", "student_management", "data_analysis"],
                    "last_login": "2025-07-12T10:00:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "grade_manager_01",
                    "name": "李主任",
                    "role": "grade_manager",
                    "grade_id": "grade_05",
                    "school_id": "school_01",
                    "email": "manager@school.edu.cn",
                    "phone": "13800138002",
                    "permissions": ["grade_management", "class_management", "teacher_management", "student_management", "data_analysis"],
                    "last_login": "2025-07-12T09:30:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "teacher_01",
                    "name": "张老师",
                    "role": "teacher",
                    "class_id": "class_01",
                    "grade_id": "grade_05",
                    "school_id": "school_01",
                    "email": "zhang@school.edu.cn",
                    "phone": "13800138003",
                    "subject_teach": ["数学", "语文"],
                    "manages_classes": ["class_01"],
                    "permissions": ["class_management", "student_management", "data_analysis"],
                    "last_login": "2025-07-12T08:45:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "teacher_02",
                    "name": "李老师",
                    "role": "teacher",
                    "class_id": "class_02",
                    "grade_id": "grade_05",
                    "school_id": "school_01",
                    "email": "li@school.edu.cn",
                    "phone": "13800138004",
                    "subject_teach": ["数学", "英语"],
                    "manages_classes": ["class_02"],
                    "permissions": ["class_management", "student_management", "data_analysis"],
                    "last_login": "2025-07-12T08:30:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "student_01",
                    "name": "小明",
                    "role": "student",
                    "class_id": "class_01",
                    "grade_id": "grade_05",
                    "school_id": "school_01",
                    "email": "xiaoming@student.school.edu.cn",
                    "phone": "13900139001",
                    "student_number": "2025001",
                    "gender": "男",
                    "birth_date": "2014-03-15",
                    "parent_phone": "13900139001",
                    "permissions": ["personal_learning", "data_view"],
                    "learning_stats": {
                        "total_submissions": 45,
                        "correct_count": 38,
                        "accuracy_rate": 84.4,
                        "last_activity": "2025-07-12T10:30:00"
                    },
                    "last_login": "2025-07-12T10:30:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "student_02",
                    "name": "小红",
                    "role": "student",
                    "class_id": "class_01",
                    "grade_id": "grade_05",
                    "school_id": "school_01",
                    "email": "xiaohong@student.school.edu.cn",
                    "phone": "13900139002",
                    "student_number": "2025002",
                    "gender": "女",
                    "birth_date": "2014-05-20",
                    "parent_phone": "13900139002",
                    "permissions": ["personal_learning", "data_view"],
                    "learning_stats": {
                        "total_submissions": 52,
                        "correct_count": 47,
                        "accuracy_rate": 90.4,
                        "last_activity": "2025-07-12T11:15:00"
                    },
                    "last_login": "2025-07-12T11:15:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "student_03",
                    "name": "小刚",
                    "role": "student",
                    "class_id": "class_02",
                    "grade_id": "grade_05",
                    "school_id": "school_01",
                    "email": "xiaogang@student.school.edu.cn",
                    "phone": "13900139003",
                    "student_number": "2025003",
                    "gender": "男",
                    "birth_date": "2014-02-10",
                    "parent_phone": "13900139003",
                    "permissions": ["personal_learning", "data_view"],
                    "learning_stats": {
                        "total_submissions": 38,
                        "correct_count": 28,
                        "accuracy_rate": 73.7,
                        "last_activity": "2025-07-12T09:45:00"
                    },
                    "last_login": "2025-07-12T09:45:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                },
                {
                    "id": "student_04",
                    "name": "小丽",
                    "role": "student",
                    "class_id": "class_02",
                    "grade_id": "grade_05",
                    "school_id": "school_01",
                    "email": "xiaoli@student.school.edu.cn",
                    "phone": "13900139004",
                    "student_number": "2025004",
                    "gender": "女",
                    "birth_date": "2014-07-08",
                    "parent_phone": "13900139004",
                    "permissions": ["personal_learning", "data_view"],
                    "learning_stats": {
                        "total_submissions": 41,
                        "correct_count": 35,
                        "accuracy_rate": 85.4,
                        "last_activity": "2025-07-12T10:00:00"
                    },
                    "last_login": "2025-07-12T10:00:00",
                    "created_at": "2025-01-01",
                    "updated_at": "2025-07-12"
                }
            ],
            "metadata": {
                "version": "2.0",
                "created_at": "2025-07-12",
                "description": "测试数据",
                "schema_version": "2.0"
            }
        }
        
        # 创建临时文件
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_data_file = os.path.join(cls.temp_dir, 'test_school_data_v2.json')
        
        with open(cls.test_data_file, 'w', encoding='utf-8') as f:
            json.dump(cls.test_data, f, ensure_ascii=False, indent=2)
        
        # 创建用户管理实例
        cls.um = UserManagementV2(cls.test_data_file)
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        shutil.rmtree(cls.temp_dir)
    
    def test_get_all_users(self):
        """测试获取所有用户"""
        users = self.um.get_all_users()
        self.assertEqual(len(users), 8)  # 1校长 + 1年级主任 + 2教师 + 4学生
        
        # 验证角色分布
        roles = [user['role'] for user in users]
        self.assertEqual(roles.count('principal'), 1)
        self.assertEqual(roles.count('grade_manager'), 1)
        self.assertEqual(roles.count('teacher'), 2)
        self.assertEqual(roles.count('student'), 4)
    
    def test_get_user_by_id(self):
        """测试根据ID查找用户"""
        # 测试存在的用户
        user = self.um.get_user_by_id('student_01')
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], '小明')
        self.assertEqual(user['role'], 'student')
        
        # 测试不存在的用户
        user = self.um.get_user_by_id('nonexistent')
        self.assertIsNone(user)
    
    def test_get_users_by_role(self):
        """测试根据角色获取用户"""
        # 测试校长
        principals = self.um.get_users_by_role('principal')
        self.assertEqual(len(principals), 1)
        self.assertEqual(principals[0]['name'], '王校长')
        
        # 测试年级主任
        managers = self.um.get_users_by_role('grade_manager')
        self.assertEqual(len(managers), 1)
        self.assertEqual(managers[0]['name'], '李主任')
        
        # 测试教师
        teachers = self.um.get_users_by_role('teacher')
        self.assertEqual(len(teachers), 2)
        teacher_names = [t['name'] for t in teachers]
        self.assertIn('张老师', teacher_names)
        self.assertIn('李老师', teacher_names)
        
        # 测试学生
        students = self.um.get_users_by_role('student')
        self.assertEqual(len(students), 4)
    
    def test_get_managed_students(self):
        """测试获取管理的学生"""
        # 校长管理所有学生
        students = self.um.get_managed_students('principal_01')
        self.assertEqual(len(students), 4)
        
        # 年级主任管理年级内所有学生
        students = self.um.get_managed_students('grade_manager_01')
        self.assertEqual(len(students), 4)
        
        # 教师管理班级内学生
        students = self.um.get_managed_students('teacher_01')
        self.assertEqual(len(students), 2)  # 一班有2个学生
        
        students = self.um.get_managed_students('teacher_02')
        self.assertEqual(len(students), 2)  # 二班有2个学生
        
        # 学生只能管理自己
        students = self.um.get_managed_students('student_01')
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]['id'], 'student_01')
    
    def test_get_managed_classes(self):
        """测试获取管理的班级"""
        # 校长管理所有班级
        classes = self.um.get_managed_classes('principal_01')
        self.assertEqual(len(classes), 2)
        
        # 年级主任管理年级内所有班级
        classes = self.um.get_managed_classes('grade_manager_01')
        self.assertEqual(len(classes), 2)
        
        # 教师管理自己的班级
        classes = self.um.get_managed_classes('teacher_01')
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]['id'], 'class_01')
        
        classes = self.um.get_managed_classes('teacher_02')
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]['id'], 'class_02')
        
        # 学生不管理班级
        classes = self.um.get_managed_classes('student_01')
        self.assertEqual(len(classes), 0)
    
    def test_get_managed_grades(self):
        """测试获取管理的年级"""
        # 校长管理所有年级
        grades = self.um.get_managed_grades('principal_01')
        self.assertEqual(len(grades), 1)
        
        # 年级主任管理自己的年级
        grades = self.um.get_managed_grades('grade_manager_01')
        self.assertEqual(len(grades), 1)
        self.assertEqual(grades[0]['id'], 'grade_05')
        
        # 教师不管理年级
        grades = self.um.get_managed_grades('teacher_01')
        self.assertEqual(len(grades), 0)
        
        # 学生不管理年级
        grades = self.um.get_managed_grades('student_01')
        self.assertEqual(len(grades), 0)
    
    def test_get_user_permissions(self):
        """测试获取用户权限"""
        # 校长权限
        permissions = self.um.get_user_permissions('principal_01')
        expected_permissions = ["school_management", "grade_management", "teacher_management", "student_management", "data_analysis"]
        self.assertEqual(set(permissions), set(expected_permissions))
        
        # 年级主任权限
        permissions = self.um.get_user_permissions('grade_manager_01')
        expected_permissions = ["grade_management", "class_management", "teacher_management", "student_management", "data_analysis"]
        self.assertEqual(set(permissions), set(expected_permissions))
        
        # 教师权限
        permissions = self.um.get_user_permissions('teacher_01')
        expected_permissions = ["class_management", "student_management", "data_analysis"]
        self.assertEqual(set(permissions), set(expected_permissions))
        
        # 学生权限
        permissions = self.um.get_user_permissions('student_01')
        expected_permissions = ["personal_learning", "data_view"]
        self.assertEqual(set(permissions), set(expected_permissions))
    
    def test_has_permission(self):
        """测试权限检查"""
        # 校长有所有权限
        self.assertTrue(self.um.has_permission('principal_01', 'school_management'))
        self.assertTrue(self.um.has_permission('principal_01', 'grade_management'))
        self.assertTrue(self.um.has_permission('principal_01', 'teacher_management'))
        
        # 年级主任没有学校管理权限
        self.assertFalse(self.um.has_permission('grade_manager_01', 'school_management'))
        self.assertTrue(self.um.has_permission('grade_manager_01', 'grade_management'))
        
        # 教师没有年级管理权限
        self.assertFalse(self.um.has_permission('teacher_01', 'grade_management'))
        self.assertTrue(self.um.has_permission('teacher_01', 'class_management'))
        
        # 学生只有个人学习权限
        self.assertFalse(self.um.has_permission('student_01', 'class_management'))
        self.assertTrue(self.um.has_permission('student_01', 'personal_learning'))
    
    def test_get_user_hierarchy(self):
        """测试获取用户层级关系"""
        hierarchy = self.um.get_user_hierarchy('teacher_01')
        
        # 验证基本信息
        self.assertEqual(hierarchy['user']['name'], '张老师')
        self.assertEqual(hierarchy['user']['role'], 'teacher')
        
        # 验证学校信息
        self.assertEqual(hierarchy['school']['name'], '测试学校')
        
        # 验证年级信息
        self.assertEqual(hierarchy['grade']['name'], '五年级')
        
        # 验证班级信息
        self.assertEqual(hierarchy['class']['name'], '五年级一班')
        
        # 验证管理的学生
        self.assertEqual(len(hierarchy['managed_students']), 2)
        
        # 验证管理的班级
        self.assertEqual(len(hierarchy['managed_classes']), 1)
        self.assertEqual(hierarchy['managed_classes'][0]['id'], 'class_01')
        
        # 验证管理的年级（教师不管理年级）
        self.assertEqual(len(hierarchy['managed_grades']), 0)
    
    def test_get_learning_stats(self):
        """测试获取学习统计"""
        # 学生有学习统计
        stats = self.um.get_learning_stats('student_01')
        self.assertIn('total_submissions', stats)
        self.assertIn('correct_count', stats)
        self.assertIn('accuracy_rate', stats)
        self.assertEqual(stats['total_submissions'], 45)
        self.assertEqual(stats['accuracy_rate'], 84.4)
        
        # 非学生没有学习统计
        stats = self.um.get_learning_stats('teacher_01')
        self.assertEqual(stats, {})
        
        stats = self.um.get_learning_stats('principal_01')
        self.assertEqual(stats, {})
    
    def test_get_user_summary(self):
        """测试获取用户摘要"""
        # 学生摘要
        summary = self.um.get_user_summary('student_01')
        self.assertEqual(summary['name'], '小明')
        self.assertEqual(summary['role'], 'student')
        self.assertIn('student_number', summary)
        self.assertIn('learning_stats', summary)
        
        # 教师摘要
        summary = self.um.get_user_summary('teacher_01')
        self.assertEqual(summary['name'], '张老师')
        self.assertEqual(summary['role'], 'teacher')
        self.assertIn('subject_teach', summary)
        self.assertIn('manages_classes', summary)
        
        # 年级主任摘要
        summary = self.um.get_user_summary('grade_manager_01')
        self.assertEqual(summary['name'], '李主任')
        self.assertEqual(summary['role'], 'grade_manager')
        self.assertIn('grade_id', summary)
        
        # 校长摘要
        summary = self.um.get_user_summary('principal_01')
        self.assertEqual(summary['name'], '王校长')
        self.assertEqual(summary['role'], 'principal')
    
    def test_get_school_info(self):
        """测试获取学校信息"""
        school_info = self.um.get_school_info()
        self.assertEqual(school_info['name'], '测试学校')
        self.assertEqual(school_info['total_students'], 4)
        self.assertEqual(school_info['total_teachers'], 2)
        self.assertEqual(school_info['total_classes'], 2)
        self.assertEqual(school_info['total_grades'], 1)
    
    def test_get_all_grades(self):
        """测试获取所有年级"""
        grades = self.um.get_all_grades()
        self.assertEqual(len(grades), 1)
        self.assertEqual(grades[0]['name'], '五年级')
    
    def test_get_all_classes(self):
        """测试获取所有班级"""
        classes = self.um.get_all_classes()
        self.assertEqual(len(classes), 2)
        class_names = [cls['name'] for cls in classes]
        self.assertIn('五年级一班', class_names)
        self.assertIn('五年级二班', class_names)
    
    def test_get_grade_by_id(self):
        """测试根据ID获取年级"""
        grade = self.um.get_grade_by_id('grade_05')
        self.assertIsNotNone(grade)
        self.assertEqual(grade['name'], '五年级')
        
        grade = self.um.get_grade_by_id('nonexistent')
        self.assertIsNone(grade)
    
    def test_get_class_by_id(self):
        """测试根据ID获取班级"""
        cls = self.um.get_class_by_id('class_01')
        self.assertIsNotNone(cls)
        self.assertEqual(cls['name'], '五年级一班')
        
        cls = self.um.get_class_by_id('nonexistent')
        self.assertIsNone(cls)
    
    def test_get_teacher_by_class(self):
        """测试根据班级ID获取班主任"""
        teacher = self.um.get_teacher_by_class('class_01')
        self.assertIsNotNone(teacher)
        self.assertEqual(teacher['name'], '张老师')
        
        teacher = self.um.get_teacher_by_class('class_02')
        self.assertIsNotNone(teacher)
        self.assertEqual(teacher['name'], '李老师')
        
        teacher = self.um.get_teacher_by_class('nonexistent')
        self.assertIsNone(teacher)
    
    def test_get_grade_manager_by_grade(self):
        """测试根据年级ID获取年级主任"""
        manager = self.um.get_grade_manager_by_grade('grade_05')
        self.assertIsNotNone(manager)
        self.assertEqual(manager['name'], '李主任')
        
        manager = self.um.get_grade_manager_by_grade('nonexistent')
        self.assertIsNone(manager)

if __name__ == '__main__':
    unittest.main(verbosity=2) 