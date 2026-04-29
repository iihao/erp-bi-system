"""
角色管理 API
提供角色 CRUD、权限分配等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from api.database import get_db_connection, execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/roles", tags=["后台管理 - 角色管理"])

security = HTTPBearer()


# ===========================================
# 请求/响应模型
# ===========================================

class RoleCreateRequest(BaseModel):
    """创建角色请求"""
    role_name: str = Field(..., min_length=2, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")


class RoleUpdateRequest(BaseModel):
    """更新角色请求"""
    role_name: Optional[str] = Field(None, min_length=2, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")


class RolePermissionRequest(BaseModel):
    """设置角色权限请求"""
    permission_ids: List[int] = Field(..., description="权限 ID 列表")


class RoleResponse(BaseModel):
    """角色响应"""
    role_id: int
    role_name: str
    description: Optional[str]
    created_at: str
    updated_at: Optional[str]
    permission_count: int = 0


class RoleListResponse(BaseModel):
    """角色列表响应"""
    items: List[RoleResponse]
    total: int


class PermissionNode(BaseModel):
    """权限节点"""
    permission_id: int
    permission_code: str
    permission_name: str
    resource_type: str
    parent_id: int
    children: List["PermissionNode"] = []


# ===========================================
# 辅助函数
# ===========================================

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员权限"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


# ===========================================
# API 接口
# ===========================================

@router.get("", response_model=RoleListResponse)
async def get_roles(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=100, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取角色列表"""
    # 查询角色列表及其权限数量
    sql = """
        SELECT r.*, COUNT(rp.permission_id) as permission_count
        FROM roles r
        LEFT JOIN role_permissions rp ON r.role_id = rp.role_id
        GROUP BY r.role_id
        ORDER BY r.role_id
    """
    roles = execute_query(sql)

    items = []
    for role in roles:
        items.append(RoleResponse(
            role_id=role["role_id"],
            role_name=role["role_name"],
            description=role.get("description"),
            created_at=str(role.get("created_at", ""))[:19] if role.get("created_at") else "",
            updated_at=str(role.get("updated_at", ""))[:19] if role.get("updated_at") else "",
            permission_count=role.get("permission_count", 0)
        ))

    return RoleListResponse(items=items, total=len(items))


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取角色详情"""
    sql = """
        SELECT r.*, COUNT(rp.permission_id) as permission_count
        FROM roles r
        LEFT JOIN role_permissions rp ON r.role_id = rp.role_id
        WHERE r.role_id = ?
        GROUP BY r.role_id
    """
    roles = execute_query(sql, (role_id,))

    if not roles:
        raise HTTPException(status_code=404, detail="角色不存在")

    role = roles[0]
    return RoleResponse(
        role_id=role["role_id"],
        role_name=role["role_name"],
        description=role.get("description"),
        created_at=str(role.get("created_at", ""))[:19] if role.get("created_at") else "",
        updated_at=str(role.get("updated_at", ""))[:19] if role.get("updated_at") else "",
        permission_count=role.get("permission_count", 0)
    )


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建新角色"""
    # 检查角色名是否存在
    check_sql = "SELECT role_id FROM roles WHERE role_name = ?"
    existing = execute_query(check_sql, (request.role_name,))

    if existing:
        raise HTTPException(status_code=400, detail="角色名称已存在")

    # 插入新角色
    insert_sql = "INSERT INTO roles (role_name, description) VALUES (?, ?)"
    execute_update(insert_sql, (request.role_name, request.description))

    # 获取新创建的角色
    roles = execute_query("SELECT * FROM roles WHERE role_name = ?", (request.role_name,))

    role = roles[0]
    return RoleResponse(
        role_id=role["role_id"],
        role_name=role["role_name"],
        description=role.get("description"),
        created_at=str(role.get("created_at", ""))[:19] if role.get("created_at") else "",
        updated_at=None,
        permission_count=0
    )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新角色信息"""
    # 检查角色是否存在
    check_sql = "SELECT role_id FROM roles WHERE role_id = ?"
    if not execute_query(check_sql, (role_id,)):
        raise HTTPException(status_code=404, detail="角色不存在")

    # 检查新角色名是否与其他角色重复
    if request.role_name:
        check_name_sql = "SELECT role_id FROM roles WHERE role_name = ? AND role_id != ?"
        if execute_query(check_name_sql, (request.role_name, role_id)):
            raise HTTPException(status_code=400, detail="角色名称已存在")

    # 更新角色
    update_sql = """
        UPDATE roles
        SET role_name = COALESCE(?, role_name),
            description = COALESCE(?, description),
            updated_at = CURRENT_TIMESTAMP
        WHERE role_id = ?
    """
    execute_update(update_sql, (request.role_name, request.description, role_id))

    return await get_role(role_id, current_user)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除角色"""
    # 检查角色是否存在
    check_sql = "SELECT role_id FROM roles WHERE role_id = ?"
    if not execute_query(check_sql, (role_id,)):
        raise HTTPException(status_code=404, detail="角色不存在")

    # 检查是否有用户使用该角色
    user_check_sql = "SELECT user_id FROM users WHERE role_id = ? LIMIT 1"
    if execute_query(user_check_sql, (role_id,)):
        raise HTTPException(status_code=400, detail="该角色下有用户，无法删除")

    # 删除角色（级联删除权限关联）
    delete_sql = "DELETE FROM roles WHERE role_id = ?"
    execute_update(delete_sql, (role_id,))

    return {"message": "角色删除成功"}


@router.get("/{role_id}/permissions")
async def get_role_permissions(
    role_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取角色权限"""
    # 检查角色是否存在
    check_sql = "SELECT role_id FROM roles WHERE role_id = ?"
    if not execute_query(check_sql, (role_id,)):
        raise HTTPException(status_code=404, detail="角色不存在")

    # 获取角色的所有权限 ID
    sql = """
        SELECT rp.permission_id, p.permission_code, p.permission_name,
               p.resource_type, p.parent_id
        FROM role_permissions rp
        JOIN permissions p ON rp.permission_id = p.permission_id
        WHERE rp.role_id = ?
        ORDER BY p.sort_order
    """
    permissions = execute_query(sql, (role_id,))

    return {
        "role_id": role_id,
        "permission_ids": [p["permission_id"] for p in permissions],
        "permissions": permissions
    }


@router.put("/{role_id}/permissions")
async def set_role_permissions(
    role_id: int,
    request: RolePermissionRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """设置角色权限"""
    # 检查角色是否存在
    check_sql = "SELECT role_id FROM roles WHERE role_id = ?"
    if not execute_query(check_sql, (role_id,)):
        raise HTTPException(status_code=404, detail="角色不存在")

    # 检查权限是否存在
    if request.permission_ids:
        placeholders = ",".join("?" * len(request.permission_ids))
        check_perms_sql = f"SELECT permission_id FROM permissions WHERE permission_id IN ({placeholders})"
        existing_perms = execute_query(check_perms_sql, tuple(request.permission_ids))
        existing_ids = {p["permission_id"] for p in existing_perms}

        invalid_ids = set(request.permission_ids) - existing_ids
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"无效的权限 ID: {list(invalid_ids)}"
            )

    # 删除旧权限
    delete_sql = "DELETE FROM role_permissions WHERE role_id = ?"
    execute_update(delete_sql, (role_id,))

    # 添加新权限
    if request.permission_ids:
        insert_sql = "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)"
        for perm_id in request.permission_ids:
            execute_update(insert_sql, (role_id, perm_id))

    return {"message": "权限设置成功", "permission_count": len(request.permission_ids)}


@router.get("/{role_id}/users")
async def get_role_users(
    role_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取角色下的用户列表"""
    # 检查角色是否存在
    check_sql = "SELECT role_id FROM roles WHERE role_id = ?"
    if not execute_query(check_sql, (role_id,)):
        raise HTTPException(status_code=404, detail="角色不存在")

    sql = """
        SELECT user_id, username, email, real_name, status, created_at
        FROM users
        WHERE role_id = ?
        ORDER BY user_id
    """
    users = execute_query(sql, (role_id,))

    return {
        "role_id": role_id,
        "user_count": len(users),
        "users": users
    }
