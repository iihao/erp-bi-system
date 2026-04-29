"""
权限管理 API
提供权限列表（树形结构）、菜单树等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from api.database import execute_query
from api.auth import decode_token

router = APIRouter(prefix="/api/admin", tags=["后台管理 - 权限管理"])

security = HTTPBearer()


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


def build_tree(items: List[Dict], parent_id: int = 0) -> List[Dict]:
    """将扁平列表转换为树形结构"""
    tree = []
    for item in items:
        if item.get("parent_id") == parent_id:
            children = build_tree(items, item["permission_id"])
            node = {
                "permission_id": item["permission_id"],
                "permission_code": item["permission_code"],
                "permission_name": item["permission_name"],
                "resource_type": item.get("resource_type", ""),
                "sort_order": item.get("sort_order", 0),
                "children": children
            }
            tree.append(node)
    # 按 sort_order 排序
    tree.sort(key=lambda x: x.get("sort_order", 0))
    return tree


def build_menu_tree(items: List[Dict], parent_id: int = 0) -> List[Dict]:
    """构建菜单树（只包含 menu 类型的权限）"""
    menu_items = [item for item in items if item.get("resource_type") == "menu"]
    tree = []
    for item in menu_items:
        if item.get("parent_id") == parent_id:
            children = build_menu_tree(menu_items, item["permission_id"])
            node = {
                "permission_id": item["permission_id"],
                "permission_code": item["permission_code"],
                "permission_name": item["permission_name"],
                "path": get_menu_path(item["permission_code"]),
                "icon": get_menu_icon(item["permission_code"]),
                "children": children
            }
            tree.append(node)
    tree.sort(key=lambda x: x.get("sort_order", 0))
    return tree


def get_menu_path(code: str) -> str:
    """根据权限代码获取菜单路径"""
    paths = {
        "admin:user": "/admin/users",
        "admin:role": "/admin/roles",
        "admin:report": "/admin/reports",
        "admin:etl": "/admin/etl",
        "admin:monitor": "/admin/monitor"
    }
    return paths.get(code, "")


def get_menu_icon(code: str) -> str:
    """根据权限代码获取菜单图标"""
    icons = {
        "admin:user": "User",
        "admin:role": "Role",
        "admin:report": "Document",
        "admin:etl": "DataLine",
        "admin:monitor": "Monitor"
    }
    return icons.get(code, "Folder")


# ===========================================
# API 接口
# ===========================================

@router.get("/permissions")
async def get_permissions(
    tree: bool = True,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取权限列表
    :param tree: 是否返回树形结构，默认 true
    :return: 权限列表或树形结构
    """
    sql = """
        SELECT permission_id, permission_code, permission_name,
               resource_type, parent_id, sort_order
        FROM permissions
        ORDER BY sort_order, permission_id
    """
    permissions = execute_query(sql)

    if tree:
        return build_tree(permissions)
    else:
        return permissions


@router.get("/menus")
async def get_menus(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取菜单树（只包含菜单类型的权限）
    用于前端动态生成侧边栏菜单
    """
    sql = """
        SELECT permission_id, permission_code, permission_name,
               resource_type, parent_id, sort_order
        FROM permissions
        WHERE resource_type = 'menu'
        ORDER BY sort_order, permission_id
    """
    menus = execute_query(sql)

    return build_menu_tree(menus)


@router.get("/permissions/options")
async def get_permission_options(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取权限选项列表（用于角色权限配置的下拉/树形选择器）
    """
    sql = """
        SELECT permission_id, permission_code, permission_name,
               resource_type, parent_id, sort_order
        FROM permissions
        ORDER BY sort_order, permission_id
    """
    permissions = execute_query(sql)

    # 构建带层级的选项列表
    def build_options(items: List[Dict], parent_id: int = 0, level: int = 0) -> List[Dict]:
        options = []
        for item in items:
            if item.get("parent_id") == parent_id:
                prefix = "└─ " * level
                options.append({
                    "permission_id": item["permission_id"],
                    "permission_name": f"{prefix}{item['permission_name']} ({item['resource_type']})",
                    "resource_type": item.get("resource_type", ""),
                    "children": build_options(items, item["permission_id"], level + 1)
                })
        options.sort(key=lambda x: len(x.get("children", [])), reverse=True)
        return options

    return build_options(permissions)


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取用户的权限列表（通过角色关联）
    """
    # 获取用户的角色
    user_sql = """
        SELECT u.role_id, r.role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        WHERE u.user_id = ?
    """
    users = execute_query(user_sql, (user_id,))

    if not users:
        raise HTTPException(status_code=404, detail="用户不存在")

    user = users[0]
    role_id = user.get("role_id")

    if not role_id:
        return {
            "user_id": user_id,
            "role_id": None,
            "role_name": None,
            "permissions": [],
            "permission_codes": []
        }

    # 获取角色的权限
    perm_sql = """
        SELECT DISTINCT p.permission_id, p.permission_code, p.permission_name,
                        p.resource_type, p.parent_id
        FROM permissions p
        JOIN role_permissions rp ON p.permission_id = rp.permission_id
        WHERE rp.role_id = ?
        ORDER BY p.sort_order
    """
    permissions = execute_query(perm_sql, (role_id,))

    return {
        "user_id": user_id,
        "role_id": role_id,
        "role_name": user.get("role_name"),
        "permissions": permissions,
        "permission_codes": [p["permission_code"] for p in permissions]
    }


@router.get("/roles/{role_id}/permissions/tree")
async def get_role_permission_tree(
    role_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取角色的权限树（用于权限配置界面）
    返回完整的权限树，并标记哪些权限已被选中
    """
    # 检查角色是否存在
    check_sql = "SELECT role_id FROM roles WHERE role_id = ?"
    if not execute_query(check_sql, (role_id,)):
        raise HTTPException(status_code=404, detail="角色不存在")

    # 获取所有权限
    all_perms_sql = """
        SELECT permission_id, permission_code, permission_name,
               resource_type, parent_id, sort_order
        FROM permissions
        ORDER BY sort_order, permission_id
    """
    all_permissions = execute_query(all_perms_sql)

    # 获取角色已有的权限 ID
    role_perms_sql = """
        SELECT permission_id FROM role_permissions WHERE role_id = ?
    """
    role_perms = execute_query(role_perms_sql, (role_id,))
    selected_ids = {p["permission_id"] for p in role_perms}

    # 构建树形结构并标记选中状态
    def build_tree_with_selection(items: List[Dict], parent_id: int = 0) -> List[Dict]:
        tree = []
        for item in items:
            if item.get("parent_id") == parent_id:
                children = build_tree_with_selection(items, item["permission_id"])
                node = {
                    "permission_id": item["permission_id"],
                    "permission_code": item["permission_code"],
                    "permission_name": item["permission_name"],
                    "resource_type": item.get("resource_type", ""),
                    "checked": item["permission_id"] in selected_ids,
                    "children": children
                }
                tree.append(node)
        tree.sort(key=lambda x: x.get("sort_order", 0))
        return tree

    return {
        "role_id": role_id,
        "selected_ids": list(selected_ids),
        "permission_tree": build_tree_with_selection(all_permissions)
    }
