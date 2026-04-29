"""
认证模块
提供 JWT 令牌生成、验证和用户认证功能
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# 使用核心安全模块
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    get_current_user
)
from core.exceptions import UnauthorizedException

# 路由器
from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["认证"])

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


# ===========================================
# 请求/响应模型
# ===========================================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: str = Field(default="", max_length=100, description="邮箱")


class TokenResponse(BaseModel):
    """Token 响应"""
    token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=86400, description="过期时间（秒）")


class UserResponse(BaseModel):
    """用户响应"""
    username: str
    email: str


# ===========================================
# API 端点
# ===========================================

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    Args:
        request: 登录请求
        
    Returns:
        Token 响应
        
    Raises:
        HTTPException: 认证失败
    """
    from utils.database import execute_query, execute_update
    
    # 从数据库查询用户
    users = execute_query(
        "SELECT * FROM users WHERE username = ?",
        (request.username,)
    )

    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": 2003,
                "message": "用户名或密码错误"
            }
        )

    user = users[0]
    
    # 验证密码（使用 bcrypt）
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": 2003,
                "message": "用户名或密码错误"
            }
        )

    # 检查用户状态
    if user.get("status") != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": 2004,
                "message": "用户已被禁用"
            }
        )

    # 更新最后登录时间
    execute_update(
        "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (user["user_id"],)
    )

    # 创建 token
    access_token = create_access_token(
        data={"sub": str(user["user_id"])},
    )

    return TokenResponse(
        token=access_token,
        expires_in=86400  # 24 小时
    )


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """
    用户注册
    
    Args:
        request: 注册请求
        
    Returns:
        用户信息
        
    Raises:
        HTTPException: 注册失败
    """
    from utils.database import execute_query, execute_update
    
    # 检查用户名是否存在
    check_sql = "SELECT user_id FROM users WHERE username = ?"
    if execute_query(check_sql, (request.username,)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": 3001,
                "message": "用户名已存在"
            }
        )

    # 创建新用户
    insert_sql = """
        INSERT INTO users (username, password_hash, email, real_name, role_id, status)
        VALUES (?, ?, ?, ?, 3, 1)
    """
    execute_update(
        insert_sql,
        (
            request.username,
            get_password_hash(request.password),
            request.email,
            request.email
        )
    )

    return UserResponse(username=request.username, email=request.email)


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户（依赖注入）
        
    Returns:
        用户信息
    """
    username = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    return {
        "success": True,
        "data": {"username": username},
        "message": "获取用户信息成功"
    }
