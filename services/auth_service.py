"""
用户认证服务
实现JWT token管理、用户注册、登录、密码重置等功能
"""

import os
import sys
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger_config import setup_logger
from services.data_service_v3 import DataServiceV3

logger = setup_logger('auth_service', level=logging.INFO)

class AuthService:
    """用户认证服务类"""
    
    def __init__(self, data_service: DataServiceV3 = None):
        """
        初始化认证服务
        
        Args:
            data_service: 数据服务实例
        """
        self.data_service = data_service or DataServiceV3()
        
        # JWT配置
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.access_token_expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        self.refresh_token_expire_days = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    
    def hash_password(self, password: str) -> Tuple[str, str]:
        """
        哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            (password_hash, salt) 元组
        """
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8'), salt.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            password_hash: 存储的密码哈希
            salt: 密码盐值
            
        Returns:
            验证是否成功
        """
        try:
            # 使用存储的盐值重新哈希密码
            check_hash = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8'))
            return check_hash.decode('utf-8') == password_hash
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False
    
    def create_access_token(self, user_id: str, role: str, permissions: list = None) -> str:
        """
        创建访问令牌
        
        Args:
            user_id: 用户ID
            role: 用户角色
            permissions: 用户权限列表
            
        Returns:
            JWT访问令牌
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            'sub': user_id,
            'role': role,
            'permissions': permissions or [],
            'type': 'access',
            'exp': expire
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        创建刷新令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            JWT刷新令牌
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            'sub': user_id,
            'type': 'refresh',
            'exp': expire
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            解码后的令牌数据，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            return None
    
    def register_user(self, user_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """
        注册新用户
        
        Args:
            user_data: 用户数据字典
            
        Returns:
            (success, message, user_info) 元组
        """
        try:
            # 验证必需字段
            required_fields = ['name', 'email', 'password', 'role']
            for field in required_fields:
                if field not in user_data:
                    return False, f"缺少必需字段: {field}", None
            
            # 验证邮箱格式
            if not self._is_valid_email(user_data['email']):
                return False, "邮箱格式无效", None
            
            # 验证密码强度
            if not self._is_valid_password(user_data['password']):
                return False, "密码强度不足，至少需要8个字符", None
            
            # 检查邮箱是否已存在
            if self._email_exists(user_data['email']):
                return False, "邮箱已被注册", None
            
            # 哈希密码
            password_hash, salt = self.hash_password(user_data['password'])
            
            # 生成用户ID
            user_id = self._generate_user_id(user_data['role'])
            
            # 准备用户数据
            user_record = {
                'id': user_id,
                'name': user_data['name'],
                'email': user_data['email'],
                'role': user_data['role'],
                'password_hash': password_hash,
                'salt': salt,
                'phone': user_data.get('phone'),
                'school_id': user_data.get('school_id'),
                'grade_id': user_data.get('grade_id'),
                'class_id': user_data.get('class_id'),
                'student_number': user_data.get('student_number'),
                'gender': user_data.get('gender'),
                'birth_date': user_data.get('birth_date'),
                'parent_phone': user_data.get('parent_phone'),
                'subject_teach': user_data.get('subject_teach'),
                'manages_classes': user_data.get('manages_classes'),
                'permissions': user_data.get('permissions', []),
                'status': 'active'
            }
            
            # 插入用户数据
            with self.data_service.get_session() as session:
                session.execute(text("""
                    INSERT INTO users (id, name, email, role, password_hash, salt, phone,
                                     school_id, grade_id, class_id, student_number, gender,
                                     birth_date, parent_phone, subject_teach, manages_classes,
                                     permissions, status, created_at, updated_at)
                    VALUES (:id, :name, :email, :role, :password_hash, :salt, :phone,
                           :school_id, :grade_id, :class_id, :student_number, :gender,
                           :birth_date, :parent_phone, :subject_teach, :manages_classes,
                           :permissions, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), user_record)
                session.commit()
            
            # 返回用户信息（不包含密码）
            user_info = {k: v for k, v in user_record.items() 
                        if k not in ['password_hash', 'salt']}
            
            logger.info(f"用户注册成功: {user_data['email']}")
            return True, "注册成功", user_info
            
        except SQLAlchemyError as e:
            logger.error(f"用户注册失败: {e}")
            return False, "注册失败，请稍后重试", None
        except Exception as e:
            logger.error(f"用户注册异常: {e}")
            return False, "注册过程中发生错误", None
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        用户登录
        
        Args:
            email: 邮箱
            password: 密码
            
        Returns:
            (success, message, auth_data) 元组
        """
        try:
            # 获取用户信息
            with self.data_service.get_session() as session:
                query = session.execute(text("""
                    SELECT id, name, email, role, password_hash, salt, permissions, status
                    FROM users WHERE email = :email
                """), {'email': email})
                
                user = query.fetchone()
                if not user:
                    return False, "邮箱或密码错误", None
                
                user_dict = dict(user._mapping)
            
            # 检查用户状态
            if user_dict['status'] != 'active':
                return False, "账户已被禁用", None
            
            # 验证密码
            if not self.verify_password(password, user_dict['password_hash'], user_dict['salt']):
                return False, "邮箱或密码错误", None
            
            # 创建令牌
            access_token = self.create_access_token(
                user_dict['id'], 
                user_dict['role'], 
                user_dict.get('permissions', [])
            )
            refresh_token = self.create_refresh_token(user_dict['id'])
            
            # 保存会话信息
            self._save_user_session(user_dict['id'], access_token, refresh_token)
            
            # 更新最后登录时间
            with self.data_service.get_session() as session:
                session.execute(text("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = :user_id
                """), {'user_id': user_dict['id']})
                session.commit()
            
            # 返回认证数据
            auth_data = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'expires_in': self.access_token_expire_minutes * 60,
                'user': {
                    'id': user_dict['id'],
                    'name': user_dict['name'],
                    'email': user_dict['email'],
                    'role': user_dict['role'],
                    'permissions': user_dict.get('permissions', [])
                }
            }
            
            logger.info(f"用户登录成功: {email}")
            return True, "登录成功", auth_data
            
        except SQLAlchemyError as e:
            logger.error(f"用户登录失败: {e}")
            return False, "登录失败，请稍后重试", None
        except Exception as e:
            logger.error(f"用户登录异常: {e}")
            return False, "登录过程中发生错误", None
    
    def refresh_token(self, refresh_token: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            (success, message, auth_data) 元组
        """
        try:
            # 验证刷新令牌
            payload = self.verify_token(refresh_token)
            if not payload or payload.get('type') != 'refresh':
                return False, "无效的刷新令牌", None
            
            user_id = payload.get('sub')
            if not user_id:
                return False, "无效的刷新令牌", None
            
            # 检查会话是否有效
            if not self._is_session_valid(user_id, refresh_token):
                return False, "会话已过期", None
            
            # 获取用户信息
            with self.data_service.get_session() as session:
                query = session.execute(text("""
                    SELECT id, name, email, role, permissions, status
                    FROM users WHERE id = :user_id
                """), {'user_id': user_id})
                
                user = query.fetchone()
                if not user or user.status != 'active':
                    return False, "用户不存在或已被禁用", None
                
                user_dict = dict(user._mapping)
            
            # 创建新的访问令牌
            new_access_token = self.create_access_token(
                user_dict['id'], 
                user_dict['role'], 
                user_dict.get('permissions', [])
            )
            
            # 更新会话
            self._update_user_session(user_id, new_access_token)
            
            auth_data = {
                'access_token': new_access_token,
                'token_type': 'bearer',
                'expires_in': self.access_token_expire_minutes * 60
            }
            
            return True, "令牌刷新成功", auth_data
            
        except Exception as e:
            logger.error(f"令牌刷新失败: {e}")
            return False, "令牌刷新失败", None
    
    def logout_user(self, user_id: str, access_token: str) -> bool:
        """
        用户登出
        
        Args:
            user_id: 用户ID
            access_token: 访问令牌
            
        Returns:
            是否成功登出
        """
        try:
            # 使会话失效
            with self.data_service.get_session() as session:
                session.execute(text("""
                    UPDATE user_sessions 
                    SET is_active = false, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id AND token_hash = :token_hash
                """), {
                    'user_id': user_id,
                    'token_hash': self._hash_token(access_token)
                })
                session.commit()
            
            logger.info(f"用户登出成功: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            (success, message) 元组
        """
        try:
            # 验证新密码强度
            if not self._is_valid_password(new_password):
                return False, "新密码强度不足，至少需要8个字符"
            
            # 获取用户当前密码
            with self.data_service.get_session() as session:
                query = session.execute(text("""
                    SELECT password_hash, salt FROM users WHERE id = :user_id
                """), {'user_id': user_id})
                
                user = query.fetchone()
                if not user:
                    return False, "用户不存在"
                
                user_dict = dict(user._mapping)
            
            # 验证旧密码
            if not self.verify_password(old_password, user_dict['password_hash'], user_dict['salt']):
                return False, "旧密码错误"
            
            # 生成新密码哈希
            new_password_hash, new_salt = self.hash_password(new_password)
            
            # 更新密码
            with self.data_service.get_session() as session:
                session.execute(text("""
                    UPDATE users 
                    SET password_hash = :password_hash, salt = :salt, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :user_id
                """), {
                    'user_id': user_id,
                    'password_hash': new_password_hash,
                    'salt': new_salt
                })
                session.commit()
            
            # 使所有现有会话失效
            self._invalidate_user_sessions(user_id)
            
            logger.info(f"用户密码修改成功: {user_id}")
            return True, "密码修改成功"
            
        except Exception as e:
            logger.error(f"密码修改失败: {e}")
            return False, "密码修改失败，请稍后重试"
    
    def reset_password_request(self, email: str) -> Tuple[bool, str]:
        """
        请求密码重置
        
        Args:
            email: 邮箱
            
        Returns:
            (success, message) 元组
        """
        try:
            # 检查邮箱是否存在
            with self.data_service.get_session() as session:
                query = session.execute(text("""
                    SELECT id, name FROM users WHERE email = :email AND status = 'active'
                """), {'email': email})
                
                user = query.fetchone()
                if not user:
                    return False, "如果邮箱存在，重置链接将发送到该邮箱"
                
                user_dict = dict(user._mapping)
            
            # 生成重置令牌
            reset_token = self._generate_reset_token(user_dict['id'])
            
            # 保存重置令牌（这里简化处理，实际应该发送邮件）
            logger.info(f"密码重置请求: {email}, 令牌: {reset_token}")
            
            return True, "如果邮箱存在，重置链接将发送到该邮箱"
            
        except Exception as e:
            logger.error(f"密码重置请求失败: {e}")
            return False, "请求失败，请稍后重试"
    
    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, str]:
        """
        重置密码
        
        Args:
            reset_token: 重置令牌
            new_password: 新密码
            
        Returns:
            (success, message) 元组
        """
        try:
            # 验证重置令牌
            user_id = self._verify_reset_token(reset_token)
            if not user_id:
                return False, "无效或已过期的重置令牌"
            
            # 验证新密码强度
            if not self._is_valid_password(new_password):
                return False, "新密码强度不足，至少需要8个字符"
            
            # 生成新密码哈希
            new_password_hash, new_salt = self.hash_password(new_password)
            
            # 更新密码
            with self.data_service.get_session() as session:
                session.execute(text("""
                    UPDATE users 
                    SET password_hash = :password_hash, salt = :salt, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :user_id
                """), {
                    'user_id': user_id,
                    'password_hash': new_password_hash,
                    'salt': new_salt
                })
                session.commit()
            
            # 使所有现有会话失效
            self._invalidate_user_sessions(user_id)
            
            logger.info(f"密码重置成功: {user_id}")
            return True, "密码重置成功"
            
        except Exception as e:
            logger.error(f"密码重置失败: {e}")
            return False, "密码重置失败，请稍后重试"
    
    def _is_valid_email(self, email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_password(self, password: str) -> bool:
        """验证密码强度"""
        return len(password) >= 8
    
    def _email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        try:
            with self.data_service.get_session() as session:
                query = session.execute(text("""
                    SELECT 1 FROM users WHERE email = :email
                """), {'email': email})
                return query.fetchone() is not None
        except:
            return False
    
    def _generate_user_id(self, role: str) -> str:
        """生成用户ID"""
        prefix = {
            'student': 'student',
            'teacher': 'teacher',
            'grade_manager': 'grade_manager',
            'principal': 'principal',
            'admin': 'admin'
        }.get(role, 'user')
        
        timestamp = str(int(datetime.now().timestamp() * 1000))
        random_suffix = secrets.token_hex(4)
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def _hash_token(self, token: str) -> str:
        """哈希令牌用于存储"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _save_user_session(self, user_id: str, access_token: str, refresh_token: str):
        """保存用户会话"""
        try:
            with self.data_service.get_session() as session:
                session.execute(text("""
                    INSERT INTO user_sessions 
                    (user_id, token_hash, refresh_token_hash, expires_at, is_active)
                    VALUES (:user_id, :token_hash, :refresh_token_hash, :expires_at, true)
                """), {
                    'user_id': user_id,
                    'token_hash': self._hash_token(access_token),
                    'refresh_token_hash': self._hash_token(refresh_token),
                    'expires_at': datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
                })
                session.commit()
        except Exception as e:
            logger.error(f"保存用户会话失败: {e}")
    
    def _update_user_session(self, user_id: str, new_access_token: str):
        """更新用户会话"""
        try:
            with self.data_service.get_session() as session:
                session.execute(text("""
                    UPDATE user_sessions 
                    SET token_hash = :token_hash, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id AND is_active = true
                """), {
                    'user_id': user_id,
                    'token_hash': self._hash_token(new_access_token)
                })
                session.commit()
        except Exception as e:
            logger.error(f"更新用户会话失败: {e}")
    
    def _is_session_valid(self, user_id: str, refresh_token: str) -> bool:
        """检查会话是否有效"""
        try:
            with self.data_service.get_session() as session:
                query = session.execute(text("""
                    SELECT 1 FROM user_sessions 
                    WHERE user_id = :user_id 
                    AND refresh_token_hash = :refresh_token_hash 
                    AND is_active = true 
                    AND expires_at > CURRENT_TIMESTAMP
                """), {
                    'user_id': user_id,
                    'refresh_token_hash': self._hash_token(refresh_token)
                })
                return query.fetchone() is not None
        except:
            return False
    
    def _invalidate_user_sessions(self, user_id: str):
        """使用户所有会话失效"""
        try:
            with self.data_service.get_session() as session:
                session.execute(text("""
                    UPDATE user_sessions 
                    SET is_active = false, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id
                """), {'user_id': user_id})
                session.commit()
        except Exception as e:
            logger.error(f"使用户会话失效失败: {e}")
    
    def _generate_reset_token(self, user_id: str) -> str:
        """生成密码重置令牌"""
        # 这里简化处理，实际应该使用更安全的方式
        payload = {
            'sub': user_id,
            'type': 'reset',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _verify_reset_token(self, reset_token: str) -> Optional[str]:
        """验证密码重置令牌"""
        try:
            payload = jwt.decode(reset_token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            if payload.get('type') == 'reset':
                return payload.get('sub')
        except:
            pass
        return None
    
    def close(self):
        """关闭服务"""
        if self.data_service:
            self.data_service.close() 