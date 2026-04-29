"""
数据源管理 API
支持多种数据源：MySQL, PostgreSQL, CSV, Excel, API 等
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import json

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/etl/datasource", tags=["ETL - 数据源管理"])

security = HTTPBearer()


# ===========================================
# 数据模型
# ===========================================

class DataSourceCreate(BaseModel):
    """创建数据源"""
    name: str = Field(..., description="数据源名称")
    type: str = Field(..., description="数据源类型：mysql/postgresql/csv/excel/api")
    host: Optional[str] = Field(None, description="主机地址")
    port: Optional[int] = Field(None, description="端口")
    database: Optional[str] = Field(None, description="数据库名")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    connection_string: Optional[str] = Field(None, description="连接字符串")
    file_path: Optional[str] = Field(None, description="文件路径（CSV/Excel）")
    api_url: Optional[str] = Field(None, description="API 地址")
    description: Optional[str] = Field(None, description="描述")
    config_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="扩展配置")


class DataSourceUpdate(BaseModel):
    """更新数据源"""
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None
    file_path: Optional[str] = None
    api_url: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None


class DataSourceTest(BaseModel):
    """测试连接"""
    type: str
    host: str
    port: int
    database: str
    username: str
    password: str


# ===========================================
# 辅助函数
# ===========================================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证用户"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except Exception:
        raise HTTPException(status_code=401, detail="未授权")


def test_mysql_connection(host: str, port: int, database: str, username: str, password: str) -> Dict[str, Any]:
    """测试 MySQL 连接"""
    try:
        import pymysql
        connection = pymysql.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            connect_timeout=5
        )
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        return {"success": True, "message": "MySQL 连接成功"}
    except Exception as e:
        return {"success": False, "message": f"MySQL 连接失败：{str(e)}"}


def test_postgresql_connection(host: str, port: int, database: str, username: str, password: str) -> Dict[str, Any]:
    """测试 PostgreSQL 连接"""
    try:
        import psycopg2
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            connect_timeout=5
        )
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        return {"success": True, "message": "PostgreSQL 连接成功"}
    except Exception as e:
        return {"success": False, "message": f"PostgreSQL 连接失败：{str(e)}"}


def test_csv_file(file_path: str) -> Dict[str, Any]:
    """测试 CSV 文件"""
    try:
        import csv
        if not os.path.exists(file_path):
            return {"success": False, "message": "文件不存在"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            row_count = sum(1 for _ in reader)
        
        return {
            "success": True,
            "message": "CSV 文件读取成功",
            "columns": headers,
            "rows": row_count
        }
    except Exception as e:
        return {"success": False, "message": f"CSV 文件读取失败：{str(e)}"}


def get_mysql_tables(host: str, port: int, database: str, username: str, password: str) -> List[Dict[str, Any]]:
    """获取 MySQL 表结构"""
    try:
        import pymysql
        connection = pymysql.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        
        table_schemas = []
        for table in tables:
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            table_schemas.append({
                "table_name": table,
                "columns": [
                    {"name": col["Field"], "type": col["Type"], "nullable": col["Null"] == "YES"}
                    for col in columns
                ]
            })
        
        cursor.close()
        connection.close()
        return table_schemas
    except Exception as e:
        return []


# ===========================================
# API 接口
# ===========================================

@router.get("/list")
async def get_datasource_list(current_user: dict = Depends(get_current_user)):
    """获取数据源列表"""
    sources = execute_query("""
        SELECT id, name, type, host, port, database, description, 
               is_enabled, created_at, updated_at
        FROM etl_datasources
        ORDER BY created_at DESC
    """)
    
    return [dict(source) for source in sources]


@router.get("/{source_id}")
async def get_datasource_detail(source_id: int, current_user: dict = Depends(get_current_user)):
    """获取数据源详情"""
    source = execute_query("""
        SELECT * FROM etl_datasources WHERE id = ?
    """, (source_id,))
    
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    return dict(source[0])


@router.post("/create")
async def create_datasource(
    data: DataSourceCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建数据源"""
    try:
        execute_update("""
            INSERT INTO etl_datasources 
            (name, type, host, port, database, username, password, 
             connection_string, file_path, api_url, description, config_json, is_enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            data.name, data.type, data.host, data.port, data.database,
            data.username, data.password, data.connection_string,
            data.file_path, data.api_url, data.description, json.dumps(data.config_json)
        ))
        
        return {"message": "数据源创建成功", "name": data.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")


@router.put("/{source_id}/update")
async def update_datasource(
    source_id: int,
    data: DataSourceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新数据源"""
    updates = []
    params = []
    
    if data.name is not None:
        updates.append("name = ?")
        params.append(data.name)
    if data.host is not None:
        updates.append("host = ?")
        params.append(data.host)
    if data.port is not None:
        updates.append("port = ?")
        params.append(data.port)
    if data.database is not None:
        updates.append("database = ?")
        params.append(data.database)
    if data.username is not None:
        updates.append("username = ?")
        params.append(data.username)
    if data.password is not None:
        updates.append("password = ?")
        params.append(data.password)
    if data.description is not None:
        updates.append("description = ?")
        params.append(data.description)
    
    if not updates:
        raise HTTPException(status_code=400, detail="没有要更新的字段")
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(source_id)
    
    execute_update(f"""
        UPDATE etl_datasources SET {', '.join(updates)} WHERE id = ?
    """, tuple(params))
    
    return {"message": "数据源更新成功"}


@router.delete("/{source_id}/delete")
async def delete_datasource(source_id: int, current_user: dict = Depends(get_current_user)):
    """删除数据源"""
    execute_update("DELETE FROM etl_datasources WHERE id = ?", (source_id,))
    return {"message": "数据源删除成功"}


@router.post("/test")
async def test_datasource_connection(
    data: DataSourceTest,
    current_user: dict = Depends(get_current_user)
):
    """测试数据源连接"""
    if data.type == "mysql":
        result = test_mysql_connection(data.host, data.port, data.database, data.username, data.password)
    elif data.type == "postgresql":
        result = test_postgresql_connection(data.host, data.port, data.database, data.username, data.password)
    elif data.type == "csv":
        result = test_csv_file(data.host)  # host 字段用于存储文件路径
    else:
        result = {"success": False, "message": f"不支持的数据源类型：{data.type}"}
    
    return result


@router.get("/{source_id}/tables")
async def get_datasource_tables(source_id: int, current_user: dict = Depends(get_current_user)):
    """获取数据源表结构"""
    source = execute_query("SELECT * FROM etl_datasources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    source = dict(source[0])
    
    if source["type"] == "mysql":
        tables = get_mysql_tables(
            source["host"], source["port"], source["database"],
            source["username"], source["password"]
        )
        return {"tables": tables}
    elif source["type"] == "csv":
        result = test_csv_file(source["file_path"])
        if result["success"]:
            return {"tables": [{"table_name": os.path.basename(source["file_path"]), "columns": result["columns"]}]}
        return {"tables": []}
    
    return {"tables": []}


@router.put("/{source_id}/toggle")
async def toggle_datasource_status(source_id: int, current_user: dict = Depends(get_current_user)):
    """切换数据源状态"""
    source = execute_query("SELECT is_enabled FROM etl_datasources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    new_status = 0 if source[0]["is_enabled"] else 1
    execute_update("UPDATE etl_datasources SET is_enabled = ? WHERE id = ?", (new_status, source_id))
    
    return {"message": f"数据源已{'启用' if new_status else '禁用'}"}
