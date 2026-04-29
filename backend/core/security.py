"""
安全模块
提供密码哈希、JWT 令牌生成/验证等安全功能
"""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# ===========================================
# 密码哈希配置
# ===========================================
# 使用 bcrypt 进行密码哈希（比 SHA256 更安全）
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


# ===========================================
# 密码哈希函数
# ===========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    支持两种格式:
    1. bcrypt 格式 (以 $2a$ 或 $2b$ 开头)
    2. SHA256 格式 (64 位十六进制，向后兼容)
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        密码是否匹配
    """
    # 向后兼容：检测 SHA256 哈希 (64 个十六进制字符)
    if len(hashed_password) == 64 and all(c in '0123456789abcdef' for c in hashed_password.lower()):
        # SHA256 哈希
        sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return sha256_hash == hashed_password
    
    # bcrypt 哈希
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # 如果 bcrypt 验证失败，返回 False
        return False


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password: 待验证的密码
        
    Returns:
        (是否有效，错误信息)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"密码长度必须至少为 {settings.PASSWORD_MIN_LENGTH} 个字符"
    
    # 生产环境可以添加更多规则
    # if not re.search(r"[A-Z]", password):
    #     return False, "密码必须包含大写字母"
    # if not re.search(r"[a-z]", password):
    #     return False, "密码必须包含小写字母"
    # if not re.search(r"\d", password):
    #     return False, "密码必须包含数字"
    
    return True, ""


# ===========================================
# JWT 令牌管理
# ===========================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 JWT Access Token
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT 令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 JWT Refresh Token
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT 令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码 JWT 令牌
    
    Args:
        token: JWT 令牌
        
    Returns:
        解码后的 payload
        
    Raises:
        HTTPException: 令牌无效或已过期
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌或令牌已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    验证令牌类型
    
    Args:
        payload: 解码后的 payload
        expected_type: 期望的令牌类型 (access/refresh)
        
    Returns:
        令牌类型是否匹配
    """
    return payload.get("type") == expected_type


# ===========================================
# 用户认证
# ===========================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP Bearer 凭证
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 未认证或令牌无效
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌 payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证令牌类型
    if not validate_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"user_id": user_id, "payload": payload}


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    获取当前活跃用户（可扩展用于检查用户状态）
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        用户信息字典
    """
    # 这里可以添加用户状态检查逻辑
    # 例如：从数据库查询用户并检查是否被禁用
    return current_user


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    获取当前管理员用户（需要管理员权限）
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 用户无管理员权限
    """
    # 这里可以添加角色检查逻辑
    # 例如：从数据库查询用户角色并验证是否为管理员
    return current_user
