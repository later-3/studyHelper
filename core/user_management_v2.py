"""
升级版用户管理模块
支持四类用户角色：校长、年级主任、教师、学生
基于新的数据结构 (school_data_v2.json)
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserManagementV2:
    """升级版用户管理类"""
    
    def __init__(self, data_file: str = 'data/school_data_v2.json'):
        self.data_file = data_file
        self._data = None
        self._cache_timestamp = None
    
    def _load_data(self) -> Dict[str, Any]:
        """加载数据文件"""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"数据文件不存在: {self.data_file}")
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查数据版本
            if 'metadata' in data and data['metadata'].get('version') != '2.0':
                logger.warning("数据文件版本不是2.0，可能存在兼容性问题")
            
            return data
        except Exception as e:
            logger.error(f"加载数据文件失败: {e}")
            raise
    
    def _get_data(self) -> Dict[str, Any]:
        """获取数据（带缓存）"""
        if self._data is None:
            self._data = self._load_data()
        return self._data
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户列表"""
        data = self._get_data()
        return data.get('users', [])
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找用户"""
        users = self.get_all_users()
        for user in users:
            if user['id'] == user_id:
                return user
        return None
    
    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """根据角色获取用户列表"""
        users = self.get_all_users()
        return [user for user in users if user['role'] == role]
    
    def get_principal(self) -> Optional[Dict[str, Any]]:
        """获取校长信息"""
        principals = self.get_users_by_role('principal')
        return principals[0] if principals else None
    
    def get_grade_managers(self) -> List[Dict[str, Any]]:
        """获取所有年级主任"""
        return self.get_users_by_role('grade_manager')
    
    def get_grade_manager_by_grade(self, grade_id: str) -> Optional[Dict[str, Any]]:
        """根据年级ID获取年级主任"""
        managers = self.get_grade_managers()
        for manager in managers:
            if manager.get('grade_id') == grade_id:
                return manager
        return None
    
    def get_teachers(self) -> List[Dict[str, Any]]:
        """获取所有教师"""
        return self.get_users_by_role('teacher')
    
    def get_teachers_by_grade(self, grade_id: str) -> List[Dict[str, Any]]:
        """根据年级ID获取教师列表"""
        teachers = self.get_teachers()
        return [teacher for teacher in teachers if teacher.get('grade_id') == grade_id]
    
    def get_teacher_by_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        """根据班级ID获取班主任"""
        teachers = self.get_teachers()
        for teacher in teachers:
            if teacher.get('class_id') == class_id:
                return teacher
        return None
    
    def get_students(self) -> List[Dict[str, Any]]:
        """获取所有学生"""
        return self.get_users_by_role('student')
    
    def get_students_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        """根据班级ID获取学生列表"""
        students = self.get_students()
        return [student for student in students if student.get('class_id') == class_id]
    
    def get_students_by_grade(self, grade_id: str) -> List[Dict[str, Any]]:
        """根据年级ID获取学生列表"""
        students = self.get_students()
        return [student for student in students if student.get('grade_id') == grade_id]
    
    def get_managed_students(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户管理的学生列表"""
        user = self.get_user_by_id(user_id)
        if not user:
            return []
        
        role = user['role']
        if role == 'student':
            return [user]  # 学生只能管理自己
        elif role == 'teacher':
            class_id = user.get('class_id')
            return self.get_students_by_class(class_id) if class_id else []
        elif role == 'grade_manager':
            grade_id = user.get('grade_id')
            return self.get_students_by_grade(grade_id) if grade_id else []
        elif role == 'principal':
            return self.get_students()  # 校长管理所有学生
        else:
            return []
    
    def get_managed_classes(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户管理的班级列表"""
        user = self.get_user_by_id(user_id)
        if not user:
            return []
        
        data = self._get_data()
        classes = data.get('classes', [])
        
        role = user['role']
        if role == 'teacher':
            class_id = user.get('class_id')
            return [cls for cls in classes if cls['id'] == class_id] if class_id else []
        elif role == 'grade_manager':
            grade_id = user.get('grade_id')
            return [cls for cls in classes if cls.get('grade_id') == grade_id] if grade_id else []
        elif role == 'principal':
            return classes  # 校长管理所有班级
        else:
            return []
    
    def get_managed_grades(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户管理的年级列表"""
        user = self.get_user_by_id(user_id)
        if not user:
            return []
        
        data = self._get_data()
        grades = data.get('grades', [])
        
        role = user['role']
        if role == 'grade_manager':
            grade_id = user.get('grade_id')
            return [grade for grade in grades if grade['id'] == grade_id] if grade_id else []
        elif role == 'principal':
            return grades  # 校长管理所有年级
        else:
            return []
    
    def get_school_info(self) -> Dict[str, Any]:
        """获取学校信息"""
        data = self._get_data()
        return data.get('school_info', {})
    
    def get_all_grades(self) -> List[Dict[str, Any]]:
        """获取所有年级"""
        data = self._get_data()
        return data.get('grades', [])
    
    def get_grade_by_id(self, grade_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取年级信息"""
        grades = self.get_all_grades()
        for grade in grades:
            if grade['id'] == grade_id:
                return grade
        return None
    
    def get_all_classes(self) -> List[Dict[str, Any]]:
        """获取所有班级"""
        data = self._get_data()
        return data.get('classes', [])
    
    def get_class_by_id(self, class_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取班级信息"""
        classes = self.get_all_classes()
        for cls in classes:
            if cls['id'] == class_id:
                return cls
        return None
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限列表"""
        user = self.get_user_by_id(user_id)
        return user.get('permissions', []) if user else []
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有指定权限"""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions
    
    def get_user_hierarchy(self, user_id: str) -> Dict[str, Any]:
        """获取用户的层级关系"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        hierarchy = {
            'user': user,
            'school': self.get_school_info(),
            'grade': None,
            'class': None,
            'managed_students': [],
            'managed_classes': [],
            'managed_grades': []
        }
        
        # 获取年级信息
        if user.get('grade_id'):
            hierarchy['grade'] = self.get_grade_by_id(user['grade_id'])
        
        # 获取班级信息
        if user.get('class_id'):
            hierarchy['class'] = self.get_class_by_id(user['class_id'])
        
        # 获取管理的学生
        hierarchy['managed_students'] = self.get_managed_students(user_id)
        
        # 获取管理的班级
        hierarchy['managed_classes'] = self.get_managed_classes(user_id)
        
        # 获取管理的年级
        hierarchy['managed_grades'] = self.get_managed_grades(user_id)
        
        return hierarchy
    
    def get_learning_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户学习统计"""
        user = self.get_user_by_id(user_id)
        if not user or user['role'] != 'student':
            return {}
        
        return user.get('learning_stats', {})
    
    def update_user_last_login(self, user_id: str) -> bool:
        """更新用户最后登录时间"""
        try:
            data = self._get_data()
            users = data.get('users', [])
            
            for user in users:
                if user['id'] == user_id:
                    user['last_login'] = datetime.now().isoformat()
                    user['updated_at'] = datetime.now().isoformat()
                    break
            
            # 保存数据
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 清除缓存
            self._data = None
            
            return True
        except Exception as e:
            logger.error(f"更新用户登录时间失败: {e}")
            return False
    
    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户摘要信息"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        summary = {
            'id': user['id'],
            'name': user['name'],
            'role': user['role'],
            'email': user.get('email', ''),
            'last_login': user.get('last_login', ''),
            'permissions': user.get('permissions', [])
        }
        
        # 根据角色添加特定信息
        if user['role'] == 'student':
            summary.update({
                'student_number': user.get('student_number', ''),
                'class_id': user.get('class_id', ''),
                'grade_id': user.get('grade_id', ''),
                'learning_stats': user.get('learning_stats', {})
            })
        elif user['role'] == 'teacher':
            summary.update({
                'class_id': user.get('class_id', ''),
                'grade_id': user.get('grade_id', ''),
                'subject_teach': user.get('subject_teach', []),
                'manages_classes': user.get('manages_classes', [])
            })
        elif user['role'] == 'grade_manager':
            summary.update({
                'grade_id': user.get('grade_id', '')
            })
        
        return summary

# 创建全局实例
user_management_v2 = UserManagementV2()

# 兼容性函数（保持向后兼容）
def get_all_users():
    """获取所有用户列表（兼容性函数）"""
    return user_management_v2.get_all_users()

def get_user_by_id(user_id: str):
    """根据ID查找用户（兼容性函数）"""
    return user_management_v2.get_user_by_id(user_id)

def get_students_by_class(class_id: str):
    """根据班级ID获取学生列表（兼容性函数）"""
    return user_management_v2.get_students_by_class(class_id)

def get_classes_by_teacher(teacher_id: str):
    """根据教师ID获取管理的班级（兼容性函数）"""
    return user_management_v2.get_managed_classes(teacher_id)

def get_all_teachers():
    """获取所有教师（兼容性函数）"""
    return user_management_v2.get_teachers()

def get_all_students():
    """获取所有学生（兼容性函数）"""
    return user_management_v2.get_students()

def get_all_classes():
    """获取所有班级（兼容性函数）"""
    return user_management_v2.get_all_classes() 