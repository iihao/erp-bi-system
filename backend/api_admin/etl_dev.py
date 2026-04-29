"""
数据开发 API
提供 SQL 编辑器、脚本管理、测试运行等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from api.database import execute_query, execute_update, get_db_connection
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/etl/dev", tags=["数据开发"])

security = HTTPBearer()


# ===========================================
# 响应模型
# ===========================================

class DevScriptResponse(BaseModel):
    """开发脚本响应"""
    script_id: int
    script_name: str
    description: str
    script_type: str
    content: str
    status: str
    created_at: str
    updated_at: Optional[str]


class DevScriptCreateRequest(BaseModel):
    """创建脚本请求"""
    script_name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    script_type: str = Field(default="sql", pattern="^(sql|python)$")
    content: str


class DevScriptUpdateRequest(BaseModel):
    """更新脚本请求"""
    script_name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class DevScriptListResponse(BaseModel):
    """脚本列表响应"""
    items: List[DevScriptResponse]
    total: int


class SQLExecuteRequest(BaseModel):
    """SQL 执行请求"""
    sql: str
    limit: int = Field(default=100, ge=1, le=1000)


class SQLExecuteResponse(BaseModel):
    """SQL 执行响应"""
    success: bool
    columns: List[str]
    data: List[Dict[str, Any]]
    row_count: int
    execute_time: float


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

@router.get("/scripts", response_model=DevScriptListResponse)
async def get_dev_scripts(
    script_type: Optional[str] = Query(None, description="脚本类型：sql/python"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取开发脚本列表"""
    where_clauses = []
    params = []

    if script_type:
        where_clauses.append("script_type = ?")
        params.append(script_type)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT * FROM dev_scripts
        WHERE {where_sql}
        ORDER BY script_id DESC
    """
    scripts = execute_query(sql, tuple(params))

    items = []
    for script in scripts:
        items.append(DevScriptResponse(
            script_id=script["script_id"],
            script_name=script["script_name"],
            description=script.get("description", ""),
            script_type=script["script_type"],
            content=script.get("content", ""),
            status=script.get("status", "draft"),
            created_at=str(script["created_at"])[:19] if script.get("created_at") else "",
            updated_at=str(script["updated_at"])[:19] if script.get("updated_at") else None
        ))

    return DevScriptListResponse(items=items, total=len(items))


@router.get("/scripts/{script_id}", response_model=DevScriptResponse)
async def get_dev_script(
    script_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取单个脚本"""
    sql = "SELECT * FROM dev_scripts WHERE script_id = ?"
    scripts = execute_query(sql, (script_id,))

    if not scripts:
        raise HTTPException(status_code=404, detail="脚本不存在")

    script = scripts[0]
    return DevScriptResponse(
        script_id=script["script_id"],
        script_name=script["script_name"],
        description=script.get("description", ""),
        script_type=script["script_type"],
        content=script.get("content", ""),
        status=script.get("status", "draft"),
        created_at=str(script["created_at"])[:19] if script.get("created_at") else "",
        updated_at=str(script["updated_at"])[:19] if script.get("updated_at") else None
    )


@router.post("/scripts", response_model=DevScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_dev_script(
    request: DevScriptCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建新的开发脚本"""
    # 检查名称是否重复
    check_sql = "SELECT script_id FROM dev_scripts WHERE script_name = ?"
    if execute_query(check_sql, (request.script_name,)):
        raise HTTPException(status_code=400, detail="脚本名称已存在")

    # 插入新脚本
    insert_sql = """
        INSERT INTO dev_scripts (script_name, description, script_type, content, status)
        VALUES (?, ?, ?, ?, 'draft')
    """
    execute_update(insert_sql, (
        request.script_name,
        request.description,
        request.script_type,
        request.content
    ))

    # 获取新创建的脚本
    scripts = execute_query("SELECT * FROM dev_scripts WHERE script_name = ?", (request.script_name,))
    script = scripts[0]

    return DevScriptResponse(
        script_id=script["script_id"],
        script_name=script["script_name"],
        description=script.get("description", ""),
        script_type=script["script_type"],
        content=script.get("content", ""),
        status=script.get("status", "draft"),
        created_at=str(script["created_at"])[:19] if script.get("created_at") else "",
        updated_at=None
    )


@router.put("/scripts/{script_id}", response_model=DevScriptResponse)
async def update_dev_script(
    script_id: int,
    request: DevScriptUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新开发脚本"""
    # 检查脚本是否存在
    check_sql = "SELECT script_id FROM dev_scripts WHERE script_id = ?"
    if not execute_query(check_sql, (script_id,)):
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 构建更新字段
    update_fields = []
    params = []

    if request.script_name is not None:
        update_fields.append("script_name = ?")
        params.append(request.script_name)

    if request.description is not None:
        update_fields.append("description = ?")
        params.append(request.description)

    if request.content is not None:
        update_fields.append("content = ?")
        params.append(request.content)

    if request.status is not None:
        update_fields.append("status = ?")
        params.append(request.status)

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(script_id)

        update_sql = f"""
            UPDATE dev_scripts
            SET {", ".join(update_fields)}
            WHERE script_id = ?
        """
        execute_update(update_sql, tuple(params))

    # 返回更新后的脚本
    scripts = execute_query("SELECT * FROM dev_scripts WHERE script_id = ?", (script_id,))
    script = scripts[0]

    return DevScriptResponse(
        script_id=script["script_id"],
        script_name=script["script_name"],
        description=script.get("description", ""),
        script_type=script["script_type"],
        content=script.get("content", ""),
        status=script.get("status", "draft"),
        created_at=str(script["created_at"])[:19] if script.get("created_at") else "",
        updated_at=str(script["updated_at"])[:19] if script.get("updated_at") else ""
    )


@router.delete("/scripts/{script_id}")
async def delete_dev_script(
    script_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除开发脚本"""
    # 检查脚本是否存在
    check_sql = "SELECT script_id FROM dev_scripts WHERE script_id = ?"
    if not execute_query(check_sql, (script_id,)):
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 删除脚本
    delete_sql = "DELETE FROM dev_scripts WHERE script_id = ?"
    execute_update(delete_sql, (script_id,))

    return {"message": "脚本删除成功"}


@router.post("/sql/execute", response_model=SQLExecuteResponse)
async def execute_sql(
    request: SQLExecuteRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """执行 SQL 查询（只读）"""
    import time

    # 安全检查：禁止危险操作
    dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE", "REPLACE"]
    sql_upper = request.sql.upper()
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            raise HTTPException(
                status_code=400,
                detail=f"禁止执行包含 {keyword} 的操作，仅支持 SELECT 查询"
            )

    try:
        start_time = time.time()

        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(request.sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(request.limit)
            execute_time = time.time() - start_time

        # 转换为字典列表
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            data.append(row_dict)

        return SQLExecuteResponse(
            success=True,
            columns=columns,
            data=data,
            row_count=len(data),
            execute_time=round(execute_time, 3)
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL 执行失败：{str(e)}")


@router.get("/tables")
async def get_tables(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取数据库表列表"""
    try:
        tables = execute_query("SHOW TABLES")
        table_names = [list(t.values())[0] for t in tables]
    except Exception:
        tables = execute_query("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        table_names = [t["name"] for t in tables]

    return {"tables": table_names}


@router.get("/tables/{table_name}/schema")
async def get_table_schema(
    table_name: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取表结构"""
    try:
        columns = execute_query(f"DESCRIBE {table_name}")
        normalized = []
        for column in columns:
            normalized.append({
                "name": column.get("Field") or column.get("name"),
                "type": column.get("Type") or column.get("type"),
                "nullable": column.get("Null") or column.get("nullable"),
                "default": column.get("Default") or column.get("default"),
                "key": column.get("Key") or column.get("key"),
            })
    except Exception:
        columns = execute_query(f"PRAGMA table_info({table_name})")
        normalized = []
        for column in columns:
            normalized.append({
                "name": column.get("name"),
                "type": column.get("type"),
                "nullable": "NO" if column.get("notnull") else "YES",
                "default": column.get("dflt_value"),
                "key": "PRI" if column.get("pk") else "",
            })

    return {"table_name": table_name, "columns": normalized}
