"""
测试升级版数据模型 (school_data_v2.json)
验证数据结构的正确性、完整性和关系一致性
"""

import unittest
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class TestDataModelV2(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """加载测试数据"""
        cls.data_file = 'data/school_data_v2.json'
        with open(cls.data_file, 'r', encoding='utf-8') as f:
            cls.data = json.load(f)
    
    def test_data_structure_completeness(self):
        """测试数据结构完整性"""
        required_sections = ['school_info', 'grades', 'classes', 'users', 'metadata']
        for section in required_sections:
            self.assertIn(section, self.data, f"缺少必要的数据段: {section}")
    
    def test_school_info_structure(self):
        """测试学校信息结构"""
        school_info = self.data['school_info']
        required_fields = [
            'id', 'name', 'address', 'phone', 'email', 'principal_id',
            'total_students', 'total_teachers', 'total_classes', 'total_grades',
            'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, school_info, f"学校信息缺少字段: {field}")
        
        # 验证数据类型
        self.assertIsInstance(school_info['total_students'], int)
        self.assertIsInstance(school_info['total_teachers'], int)
        self.assertIsInstance(school_info['total_classes'], int)
        self.assertIsInstance(school_info['total_grades'], int)
    
    def test_grades_structure(self):
        """测试年级数据结构"""
        grades = self.data['grades']
        self.assertIsInstance(grades, list)
        self.assertGreater(len(grades), 0, "年级数据不能为空")
        
        for grade in grades:
            required_fields = [
                'id', 'name', 'grade_level', 'manager_id', 'school_id',
                'total_classes', 'total_students', 'total_teachers',
                'average_accuracy', 'created_at', 'updated_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, grade, f"年级数据缺少字段: {field}")
            
            # 验证数据类型
            self.assertIsInstance(grade['grade_level'], int)
            self.assertIsInstance(grade['total_classes'], int)
            self.assertIsInstance(grade['total_students'], int)
            self.assertIsInstance(grade['total_teachers'], int)
            self.assertIsInstance(grade['average_accuracy'], (int, float))
    
    def test_classes_structure(self):
        """测试班级数据结构"""
        classes = self.data['classes']
        self.assertIsInstance(classes, list)
        self.assertGreater(len(classes), 0, "班级数据不能为空")
        
        for class_info in classes:
            required_fields = [
                'id', 'name', 'grade_id', 'teacher_id', 'school_id',
                'student_count', 'average_accuracy', 'subject_performance',
                'needs_attention_students', 'created_at', 'updated_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, class_info, f"班级数据缺少字段: {field}")
            
            # 验证数据类型
            self.assertIsInstance(class_info['student_count'], int)
            self.assertIsInstance(class_info['average_accuracy'], (int, float))
            self.assertIsInstance(class_info['subject_performance'], dict)
            self.assertIsInstance(class_info['needs_attention_students'], list)
    
    def test_users_structure(self):
        """测试用户数据结构"""
        users = self.data['users']
        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0, "用户数据不能为空")
        
        # 验证角色类型
        valid_roles = ['principal', 'grade_manager', 'teacher', 'student']
        role_counts = {'principal': 0, 'grade_manager': 0, 'teacher': 0, 'student': 0}
        
        for user in users:
            required_fields = [
                'id', 'name', 'role', 'school_id', 'email', 'phone',
                'permissions', 'last_login', 'created_at', 'updated_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, user, f"用户数据缺少字段: {field}")
            
            # 验证角色
            self.assertIn(user['role'], valid_roles, f"无效的用户角色: {user['role']}")
            role_counts[user['role']] += 1
            
            # 验证权限
            self.assertIsInstance(user['permissions'], list)
            self.assertGreater(len(user['permissions']), 0, "用户权限不能为空")
        
        # 验证每种角色至少有一个用户
        for role, count in role_counts.items():
            self.assertGreater(count, 0, f"缺少{role}角色的用户")
    
    def test_student_specific_fields(self):
        """测试学生特有字段"""
        students = [user for user in self.data['users'] if user['role'] == 'student']
        
        for student in students:
            student_fields = [
                'class_id', 'grade_id', 'student_number', 'gender',
                'birth_date', 'parent_phone', 'learning_stats'
            ]
            
            for field in student_fields:
                self.assertIn(field, student, f"学生数据缺少字段: {field}")
            
            # 验证学习统计
            learning_stats = student['learning_stats']
            required_stats = ['total_submissions', 'correct_count', 'accuracy_rate', 'last_activity']
            
            for stat in required_stats:
                self.assertIn(stat, learning_stats, f"学习统计缺少字段: {stat}")
            
            # 验证数据类型
            self.assertIsInstance(learning_stats['total_submissions'], int)
            self.assertIsInstance(learning_stats['correct_count'], int)
            self.assertIsInstance(learning_stats['accuracy_rate'], (int, float))
    
    def test_teacher_specific_fields(self):
        """测试教师特有字段"""
        teachers = [user for user in self.data['users'] if user['role'] == 'teacher']
        
        for teacher in teachers:
            teacher_fields = ['class_id', 'grade_id', 'subject_teach', 'manages_classes']
            
            for field in teacher_fields:
                self.assertIn(field, teacher, f"教师数据缺少字段: {field}")
            
            # 验证数据类型
            self.assertIsInstance(teacher['subject_teach'], list)
            self.assertIsInstance(teacher['manages_classes'], list)
            self.assertGreater(len(teacher['subject_teach']), 0, "教师教授学科不能为空")
            self.assertGreater(len(teacher['manages_classes']), 0, "教师管理班级不能为空")
    
    def test_grade_manager_specific_fields(self):
        """测试年级主任特有字段"""
        grade_managers = [user for user in self.data['users'] if user['role'] == 'grade_manager']
        
        for manager in grade_managers:
            self.assertIn('grade_id', manager, "年级主任缺少grade_id字段")
    
    def test_data_relationships(self):
        """测试数据关系一致性"""
        # 验证学校ID一致性
        school_id = self.data['school_info']['id']
        
        for grade in self.data['grades']:
            self.assertEqual(grade['school_id'], school_id, "年级school_id不一致")
        
        for class_info in self.data['classes']:
            self.assertEqual(class_info['school_id'], school_id, "班级school_id不一致")
        
        for user in self.data['users']:
            self.assertEqual(user['school_id'], school_id, "用户school_id不一致")
        
        # 验证年级和班级关系
        grade_ids = {grade['id'] for grade in self.data['grades']}
        for class_info in self.data['classes']:
            self.assertIn(class_info['grade_id'], grade_ids, "班级关联的年级不存在")
        
        # 验证班级和教师关系
        class_ids = {class_info['id'] for class_info in self.data['classes']}
        for user in self.data['users']:
            if user['role'] == 'teacher':
                self.assertIn(user['class_id'], class_ids, "教师关联的班级不存在")
            elif user['role'] == 'student':
                self.assertIn(user['class_id'], class_ids, "学生关联的班级不存在")
    
    def test_data_consistency(self):
        """测试数据一致性"""
        # 验证学校统计数据的准确性
        school_info = self.data['school_info']
        grades = self.data['grades']
        classes = self.data['classes']
        users = self.data['users']
        
        # 统计实际数据
        actual_total_grades = len(grades)
        actual_total_classes = len(classes)
        actual_total_teachers = len([u for u in users if u['role'] == 'teacher'])
        actual_total_students = len([u for u in users if u['role'] == 'student'])
        
        # 验证统计数据
        self.assertEqual(school_info['total_grades'], actual_total_grades, "年级总数不匹配")
        self.assertEqual(school_info['total_classes'], actual_total_classes, "班级总数不匹配")
        self.assertEqual(school_info['total_teachers'], actual_total_teachers, "教师总数不匹配")
        self.assertEqual(school_info['total_students'], actual_total_students, "学生总数不匹配")
    
    def test_permissions_structure(self):
        """测试权限结构"""
        valid_permissions = {
            'principal': ['school_management', 'grade_management', 'teacher_management', 'student_management', 'data_analysis'],
            'grade_manager': ['grade_management', 'class_management', 'teacher_management', 'student_management', 'data_analysis'],
            'teacher': ['class_management', 'student_management', 'data_analysis'],
            'student': ['personal_learning', 'data_view']
        }
        
        for user in self.data['users']:
            role = user['role']
            permissions = user['permissions']
            
            # 验证权限是否在有效权限列表中
            for permission in permissions:
                self.assertIn(permission, valid_permissions[role], 
                            f"用户{user['name']}的权限{permission}不在{role}角色的有效权限列表中")
    
    def test_date_format_consistency(self):
        """测试日期格式一致性"""
        date_fields = ['created_at', 'updated_at', 'last_login', 'birth_date', 'last_activity']
        
        for user in self.data['users']:
            for field in date_fields:
                if field in user:
                    # 验证日期格式
                    try:
                        datetime.fromisoformat(user[field].replace('Z', '+00:00'))
                    except ValueError:
                        self.fail(f"用户{user['name']}的{field}字段日期格式无效: {user[field]}")
        
        # 验证学校信息的日期
        for field in ['created_at', 'updated_at']:
            try:
                datetime.fromisoformat(self.data['school_info'][field])
            except ValueError:
                self.fail(f"学校信息的{field}字段日期格式无效: {self.data['school_info'][field]}")
    
    def test_metadata_structure(self):
        """测试元数据结构"""
        metadata = self.data['metadata']
        required_fields = ['version', 'created_at', 'description', 'schema_version']
        
        for field in required_fields:
            self.assertIn(field, metadata, f"元数据缺少字段: {field}")
        
        self.assertEqual(metadata['version'], '2.0', "版本号应该是2.0")
        self.assertEqual(metadata['schema_version'], '2.0', "模式版本应该是2.0")

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 