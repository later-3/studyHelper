"""
认证API端点
实现用户注册、登录、令牌刷新、登出等功能
"""

import os
import sys
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger_config import setup_logger
from services.auth_service import AuthService
from services.data_service_v3 import DataServiceV3

logger = setup_logger('auth_api', level=logging.INFO)

# 创建路由器
router = APIRouter(prefix="/api/v3/auth", tags=["认证"])

# 安全模式
security = HTTPBearer()

# 请求模型
class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    phone: Optional[str] = None
    school_id: Optional[str] = None
    grade_id: Optional[str] = None
    class_id: Optional[str] = None
    student_number: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    parent_phone: Optional[str] = None
    subject_teach: Optional[list] = None
    manages_classes: Optional[list] = None
    permissions: Optional[list] = None

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirmRequest(BaseModel):
    reset_token: str
    new_password: str

# 响应模型
class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict

# 依赖注入
def get_auth_service():
    """获取认证服务实例"""
    data_service = DataServiceV3()
    auth_service = AuthService(data_service)
    try:
        yield auth_service
    finally:
        auth_service.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                    auth_service: AuthService = Depends(get_auth_service)) -> Dict:
    """获取当前用户信息"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload or payload.get('type') != 'access':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

# API端点
@router.post("/register", response_model=AuthResponse)
async def register_user(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册
    
    - **name**: 用户姓名
    - **email**: 邮箱地址
    - **password**: 密码（至少8个字符）
    - **role**: 用户角色（student/teacher/grade_manager/principal/admin）
    - **phone**: 电话号码（可选）
    - **school_id**: 学校ID（可选）
    - **grade_id**: 年级ID（可选）
    - **class_id**: 班级ID（可选）
    - **student_number**: 学号（学生角色可选）
    - **gender**: 性别（可选）
    - **birth_date**: 出生日期（可选）
    - **parent_phone**: 家长电话（学生角色可选）
    - **subject_teach**: 教授学科（教师角色可选）
    - **manages_classes**: 管理的班级（教师角色可选）
    - **permissions**: 权限列表（可选）
    """
    try:
        user_data = request.dict()
        success, message, user_info = auth_service.register_user(user_data)
        
        if success:
            return AuthResponse(
                success=True,
                message=message,
                data=user_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误"
        )

@router.post("/login", response_model=AuthResponse)
async def login_user(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录
    
    - **email**: 邮箱地址
    - **password**: 密码
    """
    try:
        success, message, auth_data = auth_service.login_user(
            request.email, 
            request.password
        )
        
        if success:
            return AuthResponse(
                success=True,
                message=message,
                data=auth_data
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误"
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    try:
        success, message, auth_data = auth_service.refresh_token(request.refresh_token)
        
        if success:
            return AuthResponse(
                success=True,
                message=message,
                data=auth_data
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌刷新异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新过程中发生错误"
        )

@router.post("/logout", response_model=AuthResponse)
async def logout_user(
    current_user: Dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登出
    
    需要有效的访问令牌
    """
    try:
        user_id = current_user.get('sub')
        access_token = credentials.credentials
        
        success = auth_service.logout_user(user_id, access_token)
        
        if success:
            return AuthResponse(
                success=True,
                message="登出成功"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登出失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登出异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出过程中发生错误"
        )

@router.post("/change-password", response_model=AuthResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    修改密码
    
    - **old_password**: 旧密码
    - **new_password**: 新密码（至少8个字符）
    
    需要有效的访问令牌
    """
    try:
        user_id = current_user.get('sub')
        success, message = auth_service.change_password(
            user_id, 
            request.old_password, 
            request.new_password
        )
        
        if success:
            return AuthResponse(
                success=True,
                message=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码修改异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改过程中发生错误"
        )

@router.post("/reset-password-request", response_model=AuthResponse)
async def reset_password_request(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    请求密码重置
    
    - **email**: 邮箱地址
    
    如果邮箱存在，将发送重置链接到该邮箱
    """
    try:
        success, message = auth_service.reset_password_request(request.email)
        
        # 无论成功与否都返回相同消息，避免邮箱枚举攻击
        return AuthResponse(
            success=True,
            message="如果邮箱存在，重置链接将发送到该邮箱"
        )
        
    except Exception as e:
        logger.error(f"密码重置请求异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="请求失败，请稍后重试"
        )

@router.post("/reset-password-confirm", response_model=AuthResponse)
async def reset_password_confirm(
    request: ResetPasswordConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    确认密码重置
    
    - **reset_token**: 重置令牌
    - **new_password**: 新密码（至少8个字符）
    """
    try:
        success, message = auth_service.reset_password(
            request.reset_token, 
            request.new_password
        )
        
        if success:
            return AuthResponse(
                success=True,
                message=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码重置确认异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置过程中发生错误"
        )

@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    获取当前用户信息
    
    需要有效的访问令牌
    """
    try:
        user_id = current_user.get('sub')
        user_info = auth_service.data_service.get_user_info(user_id)
        
        if user_info:
            # 移除敏感信息
            safe_user_info = {k: v for k, v in user_info.items() 
                            if k not in ['password_hash', 'salt']}
            
            return AuthResponse(
                success=True,
                message="获取用户信息成功",
                data=safe_user_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息过程中发生错误"
        )

@router.post("/validate-token", response_model=AuthResponse)
async def validate_token(
    current_user: Dict = Depends(get_current_user)
):
    """
    验证访问令牌
    
    需要有效的访问令牌
    """
    return AuthResponse(
        success=True,
        message="令牌有效",
        data={
            'user_id': current_user.get('sub'),
            'role': current_user.get('role'),
            'permissions': current_user.get('permissions', [])
        }
    ) 