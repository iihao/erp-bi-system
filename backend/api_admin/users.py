"""
用户管理 API
提供用户 CRUD、密码重置、状态切换等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from api.database import get_db_connection, execute_query, execute_update, dict_from_row
from api.auth import get_password_hash, verify_password

router = APIRouter(prefix="/api/admin/users", tags=["后台管理 - 用户管理"])

security = HTTPBearer()


# ===========================================
# 请求/响应模型
# ===========================================

class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    real_name: Optional[str] = Field(None, max_length=50, description="真实姓名")
    role_id: Optional[int] = Field(None, description="角色 ID")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    real_name: Optional[str] = Field(None, max_length=50, description="真实姓名")
    role_id: Optional[int] = Field(None, description="角色 ID")


class UserResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6, description="新密码")


class UserToggleStatusRequest(BaseModel):
    """切换状态请求"""
    status: int = Field(..., ge=0, le=1, description="状态：1-启用，0-禁用")


class UserResponse(BaseModel):
    """用户响应"""
    user_id: int
    username: str
    email: Optional[str]
    real_name: Optional[str]
    role_id: Optional[int]
    role_name: Optional[str]
    status: int
    created_at: str
    updated_at: Optional[str]
    last_login_at: Optional[str]


class UserListResponse(BaseModel):
    """用户列表响应"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


# ===========================================
# 辅助函数
# ===========================================

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员权限"""
    from api.auth import decode_token
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


def row_to_user_response(row: dict) -> UserResponse:
    """将数据库行转换为用户响应"""
    return UserResponse(
        user_id=row["user_id"],
        username=row["username"],
        email=row.get("email"),
        real_name=row.get("real_name"),
        role_id=row.get("role_id"),
        role_name=row.get("role_name"),
        status=row.get("status", 1),
        created_at=str(row.get("created_at", ""))[:19] if row.get("created_at") else "",
        updated_at=str(row.get("updated_at", ""))[:19] if row.get("updated_at") else "",
        last_login_at=str(row.get("last_login_at", ""))[:19] if row.get("last_login_at") else ""
    )


# ===========================================
# API 接口
# ===========================================

@router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    role_id: Optional[int] = Query(None, description="角色 ID 筛选"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态筛选"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取用户列表（分页、搜索、筛选）"""
    offset = (page - 1) * page_size

    # 构建查询条件
    where_clauses = []
    params = []

    if keyword:
        where_clauses.append("(username LIKE ? OR email LIKE ? OR real_name LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

    if role_id is not None:
        where_clauses.append("role_id = ?")
        params.append(role_id)

    if status is not None:
        where_clauses.append("status = ?")
        params.append(status)

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # 查询总数
    count_sql = f"""
        SELECT COUNT(*) as total FROM users {where_sql}
    """
    count_result = execute_query(count_sql, tuple(params))
    total = count_result[0]["total"] if count_result else 0

    # 查询用户列表（关联角色表获取角色名称）
    users_sql = f"""
        SELECT u.*, r.role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        {where_sql}
        ORDER BY u.user_id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    users = execute_query(users_sql, tuple(params))

    items = [row_to_user_response(u) for u in users]

    return UserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取用户详情"""
    sql = """
        SELECT u.*, r.role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        WHERE u.user_id = ?
    """
    users = execute_query(sql, (user_id,))

    if not users:
        raise HTTPException(status_code=404, detail="用户不存在")

    return row_to_user_response(users[0])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建新用户"""
    # 检查用户名是否存在
    check_sql = "SELECT user_id FROM users WHERE username = ?"
    existing = execute_query(check_sql, (request.username,))

    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 插入新用户
    insert_sql = """
        INSERT INTO users (username, password_hash, email, real_name, role_id, status)
        VALUES (?, ?, ?, ?, ?, 1)
    """
    execute_update(insert_sql, (
        request.username,
        get_password_hash(request.password),
        request.email,
        request.real_name,
        request.role_id
    ))

    # 获取新创建的用户
    users = execute_query("SELECT * FROM users WHERE username = ?", (request.username,))

    return row_to_user_response(users[0])


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新用户信息"""
    # 检查用户是否存在
    check_sql = "SELECT user_id FROM users WHERE user_id = ?"
    if not execute_query(check_sql, (user_id,)):
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新用户
    update_sql = """
        UPDATE users
        SET email = ?, real_name = ?, role_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """
    execute_update(update_sql, (request.email, request.real_name, request.role_id, user_id))

    # 返回更新后的用户
    return await get_user(user_id, current_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除用户"""
    # 检查用户是否存在
    check_sql = "SELECT user_id FROM users WHERE user_id = ?"
    if not execute_query(check_sql, (user_id,)):
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许删除自己
    if current_user.get("user_id") == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    # 删除用户
    delete_sql = "DELETE FROM users WHERE user_id = ?"
    execute_update(delete_sql, (user_id,))

    return {"message": "用户删除成功"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    request: UserResetPasswordRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """重置用户密码"""
    # 检查用户是否存在
    check_sql = "SELECT user_id FROM users WHERE user_id = ?"
    if not execute_query(check_sql, (user_id,)):
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新密码
    update_sql = """
        UPDATE users
        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """
    execute_update(update_sql, (get_password_hash(request.new_password), user_id))

    return {"message": "密码重置成功"}


@router.post("/{user_id}/toggle-status")
async def toggle_status(
    user_id: int,
    request: UserToggleStatusRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """启用/禁用用户"""
    # 检查用户是否存在
    check_sql = "SELECT user_id FROM users WHERE user_id = ?"
    if not execute_query(check_sql, (user_id,)):
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许禁用自己
    if current_user.get("user_id") == user_id and request.status == 0:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")

    # 更新状态
    update_sql = """
        UPDATE users
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """
    execute_update(update_sql, (request.status, user_id))

    status_text = "启用" if request.status == 1 else "禁用"
    return {"message": f"用户已{status_text}"}


@router.get("/roles/options")
async def get_role_options(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取角色选项列表（用于下拉选择）"""
    sql = "SELECT role_id, role_name, description FROM roles ORDER BY role_id"
    roles = execute_query(sql)
    return roles
