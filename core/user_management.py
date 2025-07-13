import json

DATA_FILE = '/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/data/school_data.json'

def load_all_data():
    """加载并解析整个数据文件。"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_users():
    """获取所有用户列表。"""
    data = load_all_data()
    return data.get('users', [])

def get_user_by_id(user_id):
    """根据ID查找用户。"""
    users = get_all_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def get_students_by_class(class_id):
    """获取指定班级的所有学生。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'student' and user.get('class_id') == class_id]

def get_students_by_grade(grade_id):
    """获取指定年级的所有学生。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'student' and user.get('grade_id') == grade_id]

def get_students_by_school(school_id):
    """获取指定学校的所有学生。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'student' and user.get('school_id') == school_id]

def get_classes_by_teacher(teacher_id):
    """获取老师管理的所有班级信息。"""
    teacher = get_user_by_id(teacher_id)
    if not teacher or 'manages_classes' not in teacher:
        return []
    
    all_classes = load_all_data().get('classes', [])
    managed_class_ids = teacher['manages_classes']
    return [cls for cls in all_classes if cls['id'] in managed_class_ids]

def get_classes_by_grade(grade_id):
    """获取指定年级的所有班级。"""
    all_classes = load_all_data().get('classes', [])
    return [cls for cls in all_classes if cls.get('grade_id') == grade_id]

def get_classes_by_school(school_id):
    """获取指定学校的所有班级。"""
    all_classes = load_all_data().get('classes', [])
    return [cls for cls in all_classes if cls.get('school_id') == school_id]

def get_grades_by_school(school_id):
    """获取指定学校的所有年级。"""
    all_grades = load_all_data().get('grades', [])
    return [grade for grade in all_grades if grade.get('school_id') == school_id]

def get_all_teachers():
    """获取所有老师的列表。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'teacher']

def get_teachers_by_grade(grade_id):
    """获取指定年级的所有老师。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'teacher' and user.get('grade_id') == grade_id]

def get_teachers_by_school(school_id):
    """获取指定学校的所有老师。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'teacher' and user.get('school_id') == school_id]

def get_all_students():
    """获取所有学生的列表。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'student']

def get_all_classes():
    """获取所有班级的列表。"""
    data = load_all_data()
    return data.get('classes', [])

def get_all_grades():
    """获取所有年级的列表。"""
    data = load_all_data()
    return data.get('grades', [])

def get_grade_managers():
    """获取所有年级主任的列表。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'grade_manager']

def get_principals():
    """获取所有校长的列表。"""
    all_users = get_all_users()
    return [user for user in all_users if user.get('role') == 'principal']

def get_school_info():
    """获取学校信息。"""
    data = load_all_data()
    return data.get('school_info', {})

def get_user_hierarchy(user_id):
    """获取用户的层级信息（班级、年级、学校）。"""
    user = get_user_by_id(user_id)
    if not user:
        return None
    
    hierarchy = {
        'user': user,
        'class': None,
        'grade': None,
        'school': None
    }
    
    # 获取班级信息
    if user.get('class_id'):
        all_classes = get_all_classes()
        hierarchy['class'] = next((cls for cls in all_classes if cls['id'] == user['class_id']), None)
    
    # 获取年级信息
    if user.get('grade_id'):
        all_grades = get_all_grades()
        hierarchy['grade'] = next((grade for grade in all_grades if grade['id'] == user['grade_id']), None)
    
    # 获取学校信息
    if user.get('school_id'):
        hierarchy['school'] = get_school_info()
    
    return hierarchy

def get_managed_users(user_id):
    """获取用户管理的所有下级用户。"""
    user = get_user_by_id(user_id)
    if not user:
        return []
    
    role = user.get('role')
    managed_users = []
    
    if role == 'principal':
        # 校长管理全校用户
        managed_users = get_all_users()
    elif role == 'grade_manager':
        # 年级主任管理本年级用户
        grade_id = user.get('grade_id')
        if grade_id:
            managed_users = get_students_by_grade(grade_id)
            # 添加本年级的老师
            managed_users.extend(get_teachers_by_grade(grade_id))
    elif role == 'teacher':
        # 老师管理本班学生
        class_id = user.get('class_id')
        if class_id:
            managed_users = get_students_by_class(class_id)
    
    return managed_users

def get_user_permissions(user_id):
    """获取用户的权限列表。"""
    user = get_user_by_id(user_id)
    if not user:
        return []
    
    role = user.get('role')
    permissions = []
    
    if role == 'principal':
        permissions = [
            'view_school_overview',
            'view_all_grades',
            'view_all_classes', 
            'view_all_teachers',
            'view_all_students',
            'manage_school_settings',
            'view_school_analytics'
        ]
    elif role == 'grade_manager':
        permissions = [
            'view_grade_overview',
            'view_grade_classes',
            'view_grade_teachers',
            'view_grade_students',
            'manage_grade_settings',
            'view_grade_analytics'
        ]
    elif role == 'teacher':
        permissions = [
            'view_class_overview',
            'view_class_students',
            'manage_class_settings',
            'view_class_analytics',
            'view_student_details'
        ]
    elif role == 'student':
        permissions = [
            'view_own_profile',
            'view_own_submissions',
            'view_own_analytics',
            'upload_questions'
        ]
    
    return permissions

def can_access_user_data(requester_id, target_user_id):
    """检查用户是否有权限访问目标用户的数据。"""
    requester = get_user_by_id(requester_id)
    target = get_user_by_id(target_user_id)
    
    if not requester or not target:
        return False
    
    # 自己可以访问自己的数据
    if requester_id == target_user_id:
        return True
    
    requester_role = requester.get('role')
    target_role = target.get('role')
    
    # 校长可以访问所有用户数据
    if requester_role == 'principal':
        return True
    
    # 年级主任可以访问本年级用户数据
    if requester_role == 'grade_manager':
        return (requester.get('grade_id') == target.get('grade_id'))
    
    # 老师可以访问本班学生数据
    if requester_role == 'teacher':
        return (target_role == 'student' and 
                requester.get('class_id') == target.get('class_id'))
    
    return False
