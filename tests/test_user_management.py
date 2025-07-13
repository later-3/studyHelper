import unittest
import json
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_management import (
    load_all_data,
    get_all_users,
    get_user_by_id,
    get_students_by_class,
    get_classes_by_teacher,
    get_all_teachers,
    get_all_students,
    get_all_classes
)

class TestUserManagement(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """在所有测试开始前，创建临时的测试数据文件。"""
        cls.test_data = {
            "school_name": "测试学校",
            "users": [
                {"id": "admin1", "name": "校长", "role": "school"},
                {"id": "teacher1", "name": "王老师", "role": "teacher", "manages_classes": ["class1"]},
                {"id": "teacher2", "name": "刘老师", "role": "teacher", "manages_classes": ["class2"]},
                {"id": "student1", "name": "学生A", "role": "student", "class_id": "class1"},
                {"id": "student2", "name": "学生B", "role": "student", "class_id": "class1"},
                {"id": "student3", "name": "学生C", "role": "student", "class_id": "class2"}
            ],
            "classes": [
                {"id": "class1", "name": "一班"},
                {"id": "class2", "name": "二班"}
            ]
        }
        # 注意：测试时需要让 user_management 模块使用这个测试文件
        # 我们通过修改模块内的全局变量 DATA_FILE 来实现
        import user_management
        user_management.DATA_FILE = 'test_school_data.json'
        with open(user_management.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(cls.test_data, f)

    @classmethod
    def tearDownClass(cls):
        """在所有测试结束后，删除临时的测试数据文件。"""
        import user_management
        os.remove(user_management.DATA_FILE)

    def test_load_all_data(self):
        """测试是否能成功加载整个数据文件。"""
        data = load_all_data()
        self.assertEqual(data['school_name'], "测试学校")
        self.assertEqual(len(data['users']), 6)

    def test_get_user_by_id(self):
        """测试根据ID查找用户。"""
        self.assertEqual(get_user_by_id('teacher1')['name'], '王老师')
        self.assertIsNone(get_user_by_id('nonexistent'))

    def test_get_students_by_class(self):
        """测试获取班级学生列表。"""
        students_class1 = get_students_by_class('class1')
        self.assertEqual(len(students_class1), 2)
        self.assertEqual(students_class1[0]['name'], '学生A')
        students_class3 = get_students_by_class('class3')
        self.assertEqual(len(students_class3), 0)

    def test_get_classes_by_teacher(self):
        """测试获取老师管理的班级。"""
        classes_teacher1 = get_classes_by_teacher('teacher1')
        self.assertEqual(len(classes_teacher1), 1)
        self.assertEqual(classes_teacher1[0]['name'], '一班')
        classes_teacher_none = get_classes_by_teacher('admin1')
        self.assertEqual(len(classes_teacher_none), 0)

    def test_get_all_teachers(self):
        """测试获取所有老师列表。"""
        teachers = get_all_teachers()
        self.assertEqual(len(teachers), 2)

    def test_get_all_students(self):
        """测试获取所有学生列表。"""
        students = get_all_students()
        self.assertEqual(len(students), 3)

    def test_get_all_classes(self):
        """测试获取所有班级列表。"""
        classes = get_all_classes()
        self.assertEqual(len(classes), 2)

if __name__ == '__main__':
    unittest.main()
