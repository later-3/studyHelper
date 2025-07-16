"""
AuthService 测试用例
测试用户认证服务功能
"""

import os
import sys
import pytest
import jwt
import bcrypt
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from services.data_service_v3 import DataServiceV3
from core.logger_config import setup_logger

logger = setup_logger('test_auth_service', level='DEBUG')

class TestAuthService:
    """AuthService 测试类"""
    
    @pytest.fixture
    def mock_data_service(self):
        """模拟数据服务"""
        return Mock(spec=DataServiceV3)
    
    @pytest.fixture
    def auth_service(self, mock_data_service):
        """创建测试用的AuthService实例"""
        with patch.dict(os.environ, {
            'JWT_SECRET': 'test-secret-key',
            'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
            'REFRESH_TOKEN_EXPIRE_DAYS': '7'
        }):
            service = AuthService(mock_data_service)
            return service
    
    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            'name': '测试用户',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'role': 'student',
            'phone': '13800138000',
            'school_id': 'school_01',
            'grade_id': 'grade_05',
            'class_id': 'class_01'
        }
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = Mock()
        session.execute.return_value = Mock()
        session.commit.return_value = None
        return session

    def test_init_with_default_config(self, mock_data_service):
        """测试使用默认配置初始化"""
        with patch.dict(os.environ, {}, clear=True):
            service = AuthService(mock_data_service)
            
            assert service.jwt_secret == 'your-secret-key-change-in-production'
            assert service.access_token_expire_minutes == 30
            assert service.refresh_token_expire_days == 7

    def test_init_with_custom_config(self, mock_data_service):
        """测试使用自定义配置初始化"""
        with patch.dict(os.environ, {
            'JWT_SECRET': 'custom-secret',
            'ACCESS_TOKEN_EXPIRE_MINUTES': '60',
            'REFRESH_TOKEN_EXPIRE_DAYS': '14'
        }):
            service = AuthService(mock_data_service)
            
            assert service.jwt_secret == 'custom-secret'
            assert service.access_token_expire_minutes == 60
            assert service.refresh_token_expire_days == 14

    def test_hash_password(self, auth_service):
        """测试密码哈希"""
        password = "testpassword123"
        password_hash, salt = auth_service.hash_password(password)
        
        # 验证哈希结果
        assert isinstance(password_hash, str)
        assert isinstance(salt, str)
        assert len(password_hash) > 0
        assert len(salt) > 0
        
        # 验证密码验证
        assert auth_service.verify_password(password, password_hash, salt) is True
        assert auth_service.verify_password("wrongpassword", password_hash, salt) is False

    def test_verify_password_with_invalid_salt(self, auth_service):
        """测试使用无效盐值验证密码"""
        password = "testpassword123"
        password_hash, salt = auth_service.hash_password(password)
        
        # 使用错误的盐值
        assert auth_service.verify_password(password, password_hash, "wrong_salt") is False

    def test_create_access_token(self, auth_service):
        """测试创建访问令牌"""
        user_id = "user_001"
        role = "student"
        permissions = ["read", "write"]
        
        token = auth_service.create_access_token(user_id, role, permissions)
        
        # 验证令牌格式
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 解码并验证令牌内容
        payload = jwt.decode(token, auth_service.jwt_secret, algorithms=[auth_service.jwt_algorithm])
        assert payload['sub'] == user_id
        assert payload['role'] == role
        assert payload['permissions'] == permissions
        assert payload['type'] == 'access'
        assert 'exp' in payload

    def test_create_refresh_token(self, auth_service):
        """测试创建刷新令牌"""
        user_id = "user_001"
        
        token = auth_service.create_refresh_token(user_id)
        
        # 验证令牌格式
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 解码并验证令牌内容
        payload = jwt.decode(token, auth_service.jwt_secret, algorithms=[auth_service.jwt_algorithm])
        assert payload['sub'] == user_id
        assert payload['type'] == 'refresh'
        assert 'exp' in payload

    def test_verify_token_valid(self, auth_service):
        """测试验证有效令牌"""
        user_id = "user_001"
        token = auth_service.create_access_token(user_id, "student")
        
        payload = auth_service.verify_token(token)
        
        assert payload is not None
        assert payload['sub'] == user_id
        assert payload['type'] == 'access'

    def test_verify_token_invalid(self, auth_service):
        """测试验证无效令牌"""
        # 无效的令牌
        payload = auth_service.verify_token("invalid_token")
        assert payload is None
        
        # 使用错误密钥签名的令牌
        wrong_token = jwt.encode(
            {'sub': 'user_001', 'type': 'access'},
            'wrong_secret',
            algorithm='HS256'
        )
        payload = auth_service.verify_token(wrong_token)
        assert payload is None

    def test_verify_token_expired(self, auth_service):
        """测试验证过期令牌"""
        # 创建过期的令牌
        payload = {
            'sub': 'user_001',
            'type': 'access',
            'exp': datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(payload, auth_service.jwt_secret, algorithm=auth_service.jwt_algorithm)
        
        result = auth_service.verify_token(expired_token)
        assert result is None

    def test_register_user_success(self, auth_service, sample_user_data, mock_session):
        """测试成功注册用户"""
        # 模拟邮箱不存在
        auth_service._email_exists = Mock(return_value=False)
        
        # 模拟数据库会话
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message, user_info = auth_service.register_user(sample_user_data)
        
        assert success is True
        assert message == "注册成功"
        assert user_info is not None
        assert user_info['name'] == sample_user_data['name']
        assert user_info['email'] == sample_user_data['email']
        assert user_info['role'] == sample_user_data['role']
        assert 'password_hash' not in user_info
        assert 'salt' not in user_info

    def test_register_user_missing_fields(self, auth_service):
        """测试注册用户缺少必需字段"""
        incomplete_data = {
            'name': '测试用户',
            'email': 'test@example.com'
            # 缺少 password 和 role
        }
        
        success, message, user_info = auth_service.register_user(incomplete_data)
        
        assert success is False
        assert "缺少必需字段" in message
        assert user_info is None

    def test_register_user_invalid_email(self, auth_service):
        """测试注册用户无效邮箱"""
        invalid_data = {
            'name': '测试用户',
            'email': 'invalid-email',
            'password': 'testpassword123',
            'role': 'student'
        }
        
        success, message, user_info = auth_service.register_user(invalid_data)
        
        assert success is False
        assert "邮箱格式无效" in message
        assert user_info is None

    def test_register_user_weak_password(self, auth_service):
        """测试注册用户弱密码"""
        weak_password_data = {
            'name': '测试用户',
            'email': 'test@example.com',
            'password': '123',  # 太短
            'role': 'student'
        }
        
        success, message, user_info = auth_service.register_user(weak_password_data)
        
        assert success is False
        assert "密码强度不足" in message
        assert user_info is None

    def test_register_user_email_exists(self, auth_service, sample_user_data):
        """测试注册用户邮箱已存在"""
        auth_service._email_exists = Mock(return_value=True)
        
        success, message, user_info = auth_service.register_user(sample_user_data)
        
        assert success is False
        assert "邮箱已被注册" in message
        assert user_info is None

    def test_register_user_database_error(self, auth_service, sample_user_data, mock_session):
        """测试注册用户数据库错误"""
        auth_service._email_exists = Mock(return_value=False)
        mock_session.execute.side_effect = Exception("Database error")
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message, user_info = auth_service.register_user(sample_user_data)
        
        assert success is False
        assert "注册失败" in message
        assert user_info is None

    def test_login_user_success(self, auth_service, mock_session):
        """测试成功登录用户"""
        # 模拟用户数据
        user_data = {
            'id': 'user_001',
            'name': '测试用户',
            'email': 'test@example.com',
            'role': 'student',
            'password_hash': bcrypt.hashpw('testpassword123'.encode(), bcrypt.gensalt()).decode(),
            'salt': bcrypt.gensalt().decode(),
            'permissions': ['read'],
            'status': 'active'
        }
        
        # 模拟数据库查询
        mock_result = Mock()
        mock_result._mapping = user_data
        mock_session.execute.return_value.fetchone.return_value = mock_result
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message, auth_data = auth_service.login_user('test@example.com', 'testpassword123')
        
        assert success is True
        assert message == "登录成功"
        assert auth_data is not None
        assert 'access_token' in auth_data
        assert 'refresh_token' in auth_data
        assert auth_data['user']['id'] == 'user_001'
        assert auth_data['user']['email'] == 'test@example.com'

    def test_login_user_invalid_credentials(self, auth_service, mock_session):
        """测试登录用户无效凭据"""
        # 模拟用户不存在
        mock_session.execute.return_value.fetchone.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message, auth_data = auth_service.login_user('nonexistent@example.com', 'password')
        
        assert success is False
        assert "邮箱或密码错误" in message
        assert auth_data is None

    def test_login_user_wrong_password(self, auth_service, mock_session):
        """测试登录用户错误密码"""
        # 模拟用户数据
        user_data = {
            'id': 'user_001',
            'name': '测试用户',
            'email': 'test@example.com',
            'role': 'student',
            'password_hash': bcrypt.hashpw('correctpassword'.encode(), bcrypt.gensalt()).decode(),
            'salt': bcrypt.gensalt().decode(),
            'permissions': ['read'],
            'status': 'active'
        }
        
        mock_result = Mock()
        mock_result._mapping = user_data
        mock_session.execute.return_value.fetchone.return_value = mock_result
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message, auth_data = auth_service.login_user('test@example.com', 'wrongpassword')
        
        assert success is False
        assert "邮箱或密码错误" in message
        assert auth_data is None

    def test_login_user_inactive_account(self, auth_service, mock_session):
        """测试登录用户非活跃账户"""
        # 模拟非活跃用户
        user_data = {
            'id': 'user_001',
            'name': '测试用户',
            'email': 'test@example.com',
            'role': 'student',
            'password_hash': bcrypt.hashpw('testpassword123'.encode(), bcrypt.gensalt()).decode(),
            'salt': bcrypt.gensalt().decode(),
            'permissions': ['read'],
            'status': 'inactive'
        }
        
        mock_result = Mock()
        mock_result._mapping = user_data
        mock_session.execute.return_value.fetchone.return_value = mock_result
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message, auth_data = auth_service.login_user('test@example.com', 'testpassword123')
        
        assert success is False
        assert "账户已被禁用" in message
        assert auth_data is None

    def test_refresh_token_success(self, auth_service, mock_session):
        """测试成功刷新令牌"""
        user_id = "user_001"
        refresh_token = auth_service.create_refresh_token(user_id)
        
        # 模拟会话验证
        auth_service._is_session_valid = Mock(return_value=True)
        
        # 模拟用户数据
        user_data = {
            'id': user_id,
            'name': '测试用户',
            'email': 'test@example.com',
            'role': 'student',
            'permissions': ['read'],
            'status': 'active'
        }
        
        mock_result = Mock()
        mock_result._mapping = user_data
        mock_session.execute.return_value.fetchone.return_value = mock_result
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message, auth_data = auth_service.refresh_token(refresh_token)
        
        assert success is True
        assert message == "令牌刷新成功"
        assert auth_data is not None
        assert 'access_token' in auth_data
        assert 'refresh_token' not in auth_data  # 刷新时只返回新的访问令牌

    def test_refresh_token_invalid_token(self, auth_service):
        """测试刷新无效令牌"""
        success, message, auth_data = auth_service.refresh_token("invalid_token")
        
        assert success is False
        assert "无效的刷新令牌" in message
        assert auth_data is None

    def test_refresh_token_expired_session(self, auth_service):
        """测试刷新过期会话令牌"""
        user_id = "user_001"
        refresh_token = auth_service.create_refresh_token(user_id)
        
        # 模拟会话已过期
        auth_service._is_session_valid = Mock(return_value=False)
        
        success, message, auth_data = auth_service.refresh_token(refresh_token)
        
        assert success is False
        assert "会话已过期" in message
        assert auth_data is None

    def test_logout_user_success(self, auth_service, mock_session):
        """测试成功登出用户"""
        user_id = "user_001"
        access_token = auth_service.create_access_token(user_id, "student")
        
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success = auth_service.logout_user(user_id, access_token)
        
        assert success is True

    def test_change_password_success(self, auth_service, mock_session):
        """测试成功修改密码"""
        user_id = "user_001"
        old_password = "oldpassword123"
        new_password = "newpassword123"
        
        # 模拟当前密码哈希
        old_password_hash, old_salt = auth_service.hash_password(old_password)
        
        # 模拟数据库查询
        user_data = {
            'password_hash': old_password_hash,
            'salt': old_salt
        }
        
        mock_result = Mock()
        mock_result._mapping = user_data
        mock_session.execute.return_value.fetchone.return_value = mock_result
        mock_session.commit.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message = auth_service.change_password(user_id, old_password, new_password)
        
        assert success is True
        assert message == "密码修改成功"

    def test_change_password_weak_new_password(self, auth_service):
        """测试修改密码新密码太弱"""
        success, message = auth_service.change_password("user_001", "oldpassword", "123")
        
        assert success is False
        assert "密码强度不足" in message

    def test_change_password_wrong_old_password(self, auth_service, mock_session):
        """测试修改密码旧密码错误"""
        user_id = "user_001"
        old_password = "oldpassword123"
        new_password = "newpassword123"
        
        # 模拟当前密码哈希
        old_password_hash, old_salt = auth_service.hash_password("correctpassword")
        
        user_data = {
            'password_hash': old_password_hash,
            'salt': old_salt
        }
        
        mock_result = Mock()
        mock_result._mapping = user_data
        mock_session.execute.return_value.fetchone.return_value = mock_result
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message = auth_service.change_password(user_id, old_password, new_password)
        
        assert success is False
        assert "旧密码错误" in message

    def test_reset_password_request_success(self, auth_service, mock_session):
        """测试成功请求密码重置"""
        # 模拟用户存在
        user_data = {
            'id': 'user_001',
            'name': '测试用户'
        }
        
        mock_result = Mock()
        mock_result._mapping = user_data
        mock_session.execute.return_value.fetchone.return_value = mock_result
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message = auth_service.reset_password_request('test@example.com')
        
        assert success is True
        assert "如果邮箱存在" in message

    def test_reset_password_request_user_not_found(self, auth_service, mock_session):
        """测试请求密码重置用户不存在"""
        # 模拟用户不存在
        mock_session.execute.return_value.fetchone.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message = auth_service.reset_password_request('nonexistent@example.com')
        
        assert success is True  # 为了安全，即使用户不存在也返回成功
        assert "如果邮箱存在" in message

    def test_reset_password_success(self, auth_service, mock_session):
        """测试成功重置密码"""
        user_id = "user_001"
        new_password = "newpassword123"
        
        # 创建重置令牌
        reset_token = auth_service._generate_reset_token(user_id)
        
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        success, message = auth_service.reset_password(reset_token, new_password)
        
        assert success is True
        assert message == "密码重置成功"

    def test_reset_password_invalid_token(self, auth_service):
        """测试重置密码无效令牌"""
        success, message = auth_service.reset_password("invalid_token", "newpassword123")
        
        assert success is False
        assert "无效或已过期的重置令牌" in message

    def test_reset_password_weak_password(self, auth_service):
        """测试重置密码弱密码"""
        user_id = "user_001"
        reset_token = auth_service._generate_reset_token(user_id)
        
        success, message = auth_service.reset_password(reset_token, "123")
        
        assert success is False
        assert "密码强度不足" in message

    def test_is_valid_email(self, auth_service):
        """测试邮箱格式验证"""
        # 有效邮箱
        assert auth_service._is_valid_email("test@example.com") is True
        assert auth_service._is_valid_email("user.name@domain.co.uk") is True
        assert auth_service._is_valid_email("test+tag@example.com") is True
        
        # 无效邮箱
        assert auth_service._is_valid_email("invalid-email") is False
        assert auth_service._is_valid_email("@example.com") is False
        assert auth_service._is_valid_email("test@") is False
        assert auth_service._is_valid_email("") is False

    def test_is_valid_password(self, auth_service):
        """测试密码强度验证"""
        # 有效密码
        assert auth_service._is_valid_password("password123") is True
        assert auth_service._is_valid_password("12345678") is True
        assert auth_service._is_valid_password("a" * 8) is True
        
        # 无效密码
        assert auth_service._is_valid_password("123") is False
        assert auth_service._is_valid_password("") is False
        assert auth_service._is_valid_password("a" * 7) is False

    def test_email_exists(self, auth_service, mock_session):
        """测试邮箱存在检查"""
        # 模拟邮箱存在
        mock_session.execute.return_value.fetchone.return_value = Mock()
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        assert auth_service._email_exists("test@example.com") is True
        
        # 模拟邮箱不存在
        mock_session.execute.return_value.fetchone.return_value = None
        
        assert auth_service._email_exists("nonexistent@example.com") is False

    def test_generate_user_id(self, auth_service):
        """测试用户ID生成"""
        # 测试不同角色的ID生成
        student_id = auth_service._generate_user_id("student")
        teacher_id = auth_service._generate_user_id("teacher")
        admin_id = auth_service._generate_user_id("admin")
        
        assert student_id.startswith("student_")
        assert teacher_id.startswith("teacher_")
        assert admin_id.startswith("admin_")
        
        # 验证ID唯一性
        assert student_id != teacher_id
        assert teacher_id != admin_id

    def test_hash_token(self, auth_service):
        """测试令牌哈希"""
        token = "test_token_string"
        hashed = auth_service._hash_token(token)
        
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256哈希长度
        assert hashed != token

    def test_save_user_session(self, auth_service, mock_session):
        """测试保存用户会话"""
        user_id = "user_001"
        access_token = "access_token_123"
        refresh_token = "refresh_token_456"
        
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        auth_service._save_user_session(user_id, access_token, refresh_token)
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_user_session(self, auth_service, mock_session):
        """测试更新用户会话"""
        user_id = "user_001"
        new_access_token = "new_access_token_123"
        
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        auth_service._update_user_session(user_id, new_access_token)
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_is_session_valid(self, auth_service, mock_session):
        """测试会话有效性检查"""
        user_id = "user_001"
        refresh_token = "refresh_token_123"
        
        # 模拟有效会话
        mock_session.execute.return_value.fetchone.return_value = Mock()
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        assert auth_service._is_session_valid(user_id, refresh_token) is True
        
        # 模拟无效会话
        mock_session.execute.return_value.fetchone.return_value = None
        
        assert auth_service._is_session_valid(user_id, refresh_token) is False

    def test_invalidate_user_sessions(self, auth_service, mock_session):
        """测试使用户会话失效"""
        user_id = "user_001"
        
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        auth_service.data_service.get_session.return_value.__enter__.return_value = mock_session
        
        auth_service._invalidate_user_sessions(user_id)
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_generate_reset_token(self, auth_service):
        """测试生成重置令牌"""
        user_id = "user_001"
        reset_token = auth_service._generate_reset_token(user_id)
        
        # 验证令牌格式
        assert isinstance(reset_token, str)
        assert len(reset_token) > 0
        
        # 解码并验证令牌内容
        payload = jwt.decode(reset_token, auth_service.jwt_secret, algorithms=[auth_service.jwt_algorithm])
        assert payload['sub'] == user_id
        assert payload['type'] == 'reset'
        assert 'exp' in payload

    def test_verify_reset_token_valid(self, auth_service):
        """测试验证有效重置令牌"""
        user_id = "user_001"
        reset_token = auth_service._generate_reset_token(user_id)
        
        verified_user_id = auth_service._verify_reset_token(reset_token)
        
        assert verified_user_id == user_id

    def test_verify_reset_token_invalid(self, auth_service):
        """测试验证无效重置令牌"""
        # 无效令牌
        assert auth_service._verify_reset_token("invalid_token") is None
        
        # 错误类型的令牌
        access_token = auth_service.create_access_token("user_001", "student")
        assert auth_service._verify_reset_token(access_token) is None

    def test_close(self, auth_service):
        """测试关闭认证服务"""
        auth_service.close()
        
        # 验证数据服务被关闭
        auth_service.data_service.close.assert_called_once()

    def test_error_handling(self, auth_service):
        """测试错误处理"""
        # 测试密码哈希错误
        with patch('bcrypt.hashpw') as mock_hashpw:
            mock_hashpw.side_effect = Exception("Hash error")
            
            success = auth_service.verify_password("password", "hash", "salt")
            assert success is False
        
        # 测试令牌验证错误
        with patch('jwt.decode') as mock_decode:
            mock_decode.side_effect = Exception("Decode error")
            
            payload = auth_service.verify_token("token")
            assert payload is None

    def test_performance_with_large_tokens(self, auth_service):
        """测试大量令牌的性能"""
        # 生成大量令牌
        tokens = []
        for i in range(1000):
            token = auth_service.create_access_token(f"user_{i}", "student")
            tokens.append(token)
        
        # 验证所有令牌
        for i, token in enumerate(tokens):
            payload = auth_service.verify_token(token)
            assert payload is not None
            assert payload['sub'] == f"user_{i}"

    def test_edge_cases(self, auth_service):
        """测试边界情况"""
        # 测试空字符串输入
        assert auth_service._is_valid_email("") is False
        assert auth_service._is_valid_password("") is False
        
        # 测试None输入
        assert auth_service.verify_token(None) is None
        
        # 测试特殊字符
        assert auth_service._is_valid_email("test@#$%.com") is False
        assert auth_service._is_valid_password("a" * 1000) is True  # 长密码应该有效

    def test_security_features(self, auth_service):
        """测试安全特性"""
        # 测试密码哈希的唯一性
        password = "testpassword"
        hash1, salt1 = auth_service.hash_password(password)
        hash2, salt2 = auth_service.hash_password(password)
        
        assert hash1 != hash2  # 每次哈希应该不同
        assert salt1 != salt2  # 每次盐值应该不同
        
        # 测试令牌的唯一性
        user_id = "user_001"
        token1 = auth_service.create_access_token(user_id, "student")
        token2 = auth_service.create_access_token(user_id, "student")
        
        assert token1 != token2  # 每次生成的令牌应该不同 