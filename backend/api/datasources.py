"""
数据源管理 API
提供数据源的增删改查、连接测试等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from api.database import execute_query, execute_update, get_db_connection
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/datasources", tags=["后台管理 - 数据源管理"])

security = HTTPBearer()


# ===========================================
# 请求/响应模型
# ===========================================

class DatasourceCreateRequest(BaseModel):
    """创建数据源请求"""
    name: str = Field(..., min_length=2, max_length=100, description="数据源名称")
    department: Optional[str] = Field(None, max_length=100, description="业务部门")
    system_name: Optional[str] = Field(None, max_length=100, description="业务系统")
    category: str = Field("business", description="数据源类别")
    db_type: str = Field(..., description="数据库类型")
    driver: Optional[str] = Field(None, description="驱动类")
    host: Optional[str] = Field("", description="IP 地址或域名")
    port: Optional[int] = Field(0, ge=0, le=65535, description="端口号")
    database_name: str = Field(..., description="数据库名（SQLite 为文件路径）")
    username: Optional[str] = Field("", description="用户名")
    password: Optional[str] = Field("", description="密码")
    collect_metadata: bool = Field(False, description="是否采集元数据")
    status_check: bool = Field(False, description="状态检查")
    description: Optional[str] = Field(None, max_length=500, description="描述信息")


class DatasourceUpdateRequest(BaseModel):
    """更新数据源请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    department: Optional[str] = None
    system_name: Optional[str] = None
    category: Optional[str] = None
    db_type: Optional[str] = None
    driver: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    collect_metadata: Optional[bool] = None
    status_check: Optional[bool] = None
    status: Optional[str] = None
    description: Optional[str] = None


class DatasourceTestRequest(BaseModel):
    """测试连接请求"""
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    password: str


class DatasourceResponse(BaseModel):
    """数据源响应"""
    id: int
    name: str
    department: Optional[str]
    system_name: Optional[str]
    category: str
    db_type: str
    driver: Optional[str]
    host: str
    port: int
    database_name: str
    username: str
    password: str  # 实际应该加密存储
    collect_metadata: bool
    status_check: bool
    status: str
    description: Optional[str]
    created_at: str
    updated_at: str


class DatasourceListResponse(BaseModel):
    """数据源列表响应"""
    items: List[DatasourceResponse]
    total: int
    page: int
    page_size: int


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

@router.get("", response_model=DatasourceListResponse)
async def get_datasources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db_type: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取数据源列表"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 构建 WHERE 子句
            where_clauses = []
            params = []
            
            if keyword:
                where_clauses.append("(name LIKE ? OR description LIKE ?)")
                keyword_pattern = f"%{keyword}%"
                params.extend([keyword_pattern, keyword_pattern])
            
            if db_type:
                where_clauses.append("db_type = ?")
                params.append(db_type)
            
            if category:
                where_clauses.append("category = ?")
                params.append(category)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM datasources WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 查询数据
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM datasources
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            cursor.execute(data_sql, params)
            records = cursor.fetchall()
            
            items = []
            for record in records:
                # 将 sqlite3.Row 转换为字典
                row_dict = dict(record) if hasattr(record, 'keys') else record
                items.append({
                    'id': row_dict['id'],
                    'name': row_dict['name'],
                    'department': row_dict['department'],
                    'system_name': row_dict['system_name'],
                    'category': row_dict['category'],
                    'db_type': row_dict['db_type'],
                    'driver': row_dict['driver'],
                    'host': row_dict['host'],
                    'port': row_dict['port'],
                    'database_name': row_dict['database_name'],
                    'username': row_dict['username'],
                    'password': row_dict['password'],
                    'collect_metadata': bool(row_dict['collect_metadata']),
                    'status_check': bool(row_dict['status_check']),
                    'status': row_dict['status'],
                    'description': row_dict['description'],
                    'created_at': str(row_dict['created_at'])[:19] if row_dict['created_at'] else "",
                    'updated_at': str(row_dict['updated_at'])[:19] if row_dict['updated_at'] else ""
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{datasource_id}", response_model=DatasourceResponse)
async def get_datasource(
    datasource_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取数据源详情"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasources WHERE id = ?", (datasource_id,))
            record = cursor.fetchone()
            
            if not record:
                raise HTTPException(status_code=404, detail="数据源不存在")
            
            # 将 sqlite3.Row 转换为字典
            row_dict = dict(record) if hasattr(record, 'keys') else record
            return {
                'id': row_dict['id'],
                'name': row_dict['name'],
                'department': row_dict['department'],
                'system_name': row_dict['system_name'],
                'category': row_dict['category'],
                'db_type': row_dict['db_type'],
                'driver': row_dict['driver'],
                'host': row_dict['host'],
                'port': row_dict['port'],
                'database_name': row_dict['database_name'],
                'username': row_dict['username'],
                'password': row_dict['password'],
                'collect_metadata': bool(row_dict['collect_metadata']),
                'status_check': bool(row_dict['status_check']),
                'status': row_dict['status'],
                'description': row_dict['description'],
                'created_at': str(row_dict['created_at'])[:19] if row_dict['created_at'] else "",
                'updated_at': str(row_dict['updated_at'])[:19] if row_dict['updated_at'] else ""
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=dict)
async def create_datasource(
    request: DatasourceCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建数据源"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查名称是否已存在
            cursor.execute("SELECT id FROM datasources WHERE name = ?", (request.name,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="数据源名称已存在")
            
            # 获取默认驱动
            driver = request.driver
            if not driver:
                driver = get_default_driver(request.db_type)
            
            # 插入数据
            cursor.execute("""
                INSERT INTO datasources 
                (name, department, system_name, category, db_type, driver, host, port, 
                 database_name, username, password, collect_metadata, status_check, status, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.name,
                request.department,
                request.system_name,
                request.category,
                request.db_type,
                driver,
                request.host,
                request.port,
                request.database_name,
                request.username,
                request.password,
                1 if request.collect_metadata else 0,
                1 if request.status_check else 0,
                'inactive',
                request.description
            ))
            
            datasource_id = cursor.lastrowid
            conn.commit()
            
            return {"id": datasource_id, "message": "创建成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{datasource_id}", response_model=dict)
async def update_datasource(
    datasource_id: int,
    request: DatasourceUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新数据源"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查数据源是否存在
            cursor.execute("SELECT id FROM datasources WHERE id = ?", (datasource_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="数据源不存在")
            
            # 准备更新字段
            update_fields = []
            params = []
            
            if request.name is not None:
                # 检查名称是否与其他数据源冲突
                cursor.execute("SELECT id FROM datasources WHERE name = ? AND id != ?", (request.name, datasource_id))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="数据源名称已存在")
                update_fields.append("name = ?")
                params.append(request.name)
            
            if request.department is not None:
                update_fields.append("department = ?")
                params.append(request.department)
            
            if request.system_name is not None:
                update_fields.append("system_name = ?")
                params.append(request.system_name)
            
            if request.category is not None:
                update_fields.append("category = ?")
                params.append(request.category)
            
            if request.db_type is not None:
                update_fields.append("db_type = ?")
                params.append(request.db_type)
            
            if request.driver is not None:
                update_fields.append("driver = ?")
                params.append(request.driver)
            
            if request.host is not None:
                update_fields.append("host = ?")
                params.append(request.host)
            
            if request.port is not None:
                update_fields.append("port = ?")
                params.append(request.port)
            
            if request.database_name is not None:
                update_fields.append("database_name = ?")
                params.append(request.database_name)
            
            if request.username is not None:
                update_fields.append("username = ?")
                params.append(request.username)
            
            if request.password is not None:
                update_fields.append("password = ?")
                params.append(request.password)
            
            if request.collect_metadata is not None:
                update_fields.append("collect_metadata = ?")
                params.append(1 if request.collect_metadata else 0)
            
            if request.status_check is not None:
                update_fields.append("status_check = ?")
                params.append(1 if request.status_check else 0)
            
            if request.status is not None:
                update_fields.append("status = ?")
                params.append(request.status)
            
            if request.description is not None:
                update_fields.append("description = ?")
                params.append(request.description)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(datasource_id)
                
                update_sql = f"""
                    UPDATE datasources
                    SET {", ".join(update_fields)}
                    WHERE id = ?
                """
                cursor.execute(update_sql, params)
                conn.commit()
            
            return {"message": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{datasource_id}", response_model=dict)
async def delete_datasource(
    datasource_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除数据源"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查数据源是否存在
            cursor.execute("SELECT id FROM datasources WHERE id = ?", (datasource_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="数据源不存在")
            
            cursor.execute("DELETE FROM datasources WHERE id = ?", (datasource_id,))
            conn.commit()
            
            return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection", response_model=dict)
async def test_connection(
    request: DatasourceTestRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """测试数据库连接"""
    try:
        # 根据数据库类型构建连接字符串
        if request.db_type.lower() == 'mysql':
            import pymysql
            connection = pymysql.connect(
                host=request.host,
                port=request.port,
                user=request.username,
                password=request.password,
                database=request.database_name,
                connect_timeout=5
            )
            connection.close()
        elif request.db_type.lower() == 'postgresql':
            import psycopg2
            connection = psycopg2.connect(
                host=request.host,
                port=request.port,
                user=request.username,
                password=request.password,
                database=request.database_name,
                connect_timeout=5
            )
            connection.close()
        elif request.db_type.lower() == 'oracle':
            import cx_Oracle
            dsn = cx_Oracle.makedsn(request.host, request.port, service_name=request.database_name)
            connection = cx_Oracle.connect(request.username, request.password, dsn)
            connection.close()
        elif request.db_type.lower() == 'sqlserver':
            import pyodbc
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={request.host},{request.port};DATABASE={request.database_name};UID={request.username};PWD={request.password}"
            connection = pyodbc.connect(connection_string, timeout=5)
            connection.close()
        elif request.db_type.lower() == 'sqlite':
            import sqlite3
            conn = sqlite3.connect(request.database_name, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据库类型：{request.db_type}")
        
        return {
            "success": True,
            "message": "连接成功"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败：{str(e)}"
        }


@router.get("/types", response_model=dict)
async def get_database_types(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取支持的数据库类型"""
    types = [
        {"value": "mysql", "label": "MySQL", "default_port": 3306, "driver": "com.mysql.cj.jdbc.Driver"},
        {"value": "mysql8", "label": "MySQL 8", "default_port": 3306, "driver": "com.mysql.cj.jdbc.Driver"},
        {"value": "postgresql", "label": "PostgreSQL", "default_port": 5432, "driver": "org.postgresql.Driver"},
        {"value": "oracle", "label": "Oracle", "default_port": 1521, "driver": "oracle.jdbc.OracleDriver"},
        {"value": "sqlserver", "label": "SQL Server", "default_port": 1433, "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"},
        {"value": "sqlite", "label": "SQLite", "default_port": 0, "driver": "org.sqlite.JDBC"},
        {"value": "mariadb", "label": "MariaDB", "default_port": 3306, "driver": "org.mariadb.jdbc.Driver"}
    ]
    return {"types": types}


@router.get("/categories", response_model=dict)
async def get_categories(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取数据源类别"""
    categories = [
        {"value": "business", "label": "业务系统数据源"},
        {"value": "ods", "label": "ODS 层数据源"},
        {"value": "dwd", "label": "DWD 层数据源"},
        {"value": "dws", "label": "DWS 层数据源"},
        {"value": "ads", "label": "ADS 层数据源"},
        {"value": "external", "label": "外部数据源"},
        {"value": "file", "label": "文件数据源"}
    ]
    return {"categories": categories}


def get_default_driver(db_type: str) -> str:
    """获取默认驱动"""
    drivers = {
        "mysql": "com.mysql.cj.jdbc.Driver",
        "mysql8": "com.mysql.cj.jdbc.Driver",
        "postgresql": "org.postgresql.Driver",
        "oracle": "oracle.jdbc.OracleDriver",
        "sqlserver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        "sqlite": "org.sqlite.JDBC",
        "mariadb": "org.mariadb.jdbc.Driver"
    }
    return drivers.get(db_type.lower(), "")


def get_database_connection(db_type: str, host: str, port: int, database: str, username: str, password: str):
    """根据数据库类型获取连接"""
    if db_type.lower() in ['mysql', 'mysql8', 'mariadb']:
        import pymysql
        return pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    elif db_type.lower() == 'postgresql':
        import psycopg2
        return psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database
        )
    elif db_type.lower() == 'sqlite':
        import sqlite3
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        return conn
    elif db_type.lower() == 'sqlserver':
        import pyodbc
        connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password}"
        return pyodbc.connect(connection_string)
    else:
        raise ValueError(f"不支持的数据库类型：{db_type}")


def sync_mysql_metadata(datasource_id: int, db_type: str, host: str, port: int, database: str, username: str, password: str):
    """同步 MySQL 元数据到数仓 ODS 层"""
    try:
        # 连接 MySQL 数据源
        mysql_conn = get_database_connection(db_type, host, port, database, username, password)
        mysql_cursor = mysql_conn.cursor()
        
        # 连接本地 SQLite 数仓
        with get_db_connection() as warehouse_conn:
            warehouse_cursor = warehouse_conn.cursor()
            
            # 获取 MySQL 所有表
            mysql_cursor.execute("SHOW TABLES")
            tables = [row[f"Tables_in_{database}"] for row in mysql_cursor.fetchall()]
            
            synced_count = 0
            
            for table in tables:
                # 获取表结构
                mysql_cursor.execute(f"DESCRIBE `{table}`")
                columns = mysql_cursor.fetchall()
                
                # 创建 ODS 表（如果不存在）
                ods_table_name = f"ods_{table}"
                
                # 构建列定义
                column_defs = []
                for col in columns:
                    col_name = col['Field']
                    col_type = col['Type']
                    is_nullable = col['Null'] == 'YES'
                    col_key = col['Key']
                    is_pk = 'PRI' in col_key if col_key else False
                    
                    # MySQL 到 SQLite 类型映射
                    sqlite_type = map_mysql_to_sqlite_type(col_type)
                    
                    col_def = f"`{col_name}` {sqlite_type}"
                    if is_pk:
                        col_def += " PRIMARY KEY"
                    elif not is_nullable:
                        col_def += " NOT NULL"
                    
                    column_defs.append(col_def)
                
                # 添加数仓标准字段
                column_defs.append("`dt` DATE COMMENT '数据分区日期'")
                column_defs.append("`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                # 创建 ODS 表
                create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {ods_table_name} (
                        {', '.join(column_defs)}
                    )
                """
                warehouse_cursor.execute(create_sql)
                
                # 同步数据（全量）
                try:
                    mysql_cursor.execute(f"SELECT * FROM `{table}` LIMIT 10000")
                    rows = mysql_cursor.fetchall()
                    
                    if rows:
                        # 获取列名
                        column_names = [col['Field'] for col in columns]
                        placeholders = ', '.join(['?' for _ in column_names + ['dt']])
                        insert_sql = f"""
                            INSERT OR REPLACE INTO {ods_table_name} 
                            ({', '.join([f'`{c}`' for c in column_names])}, dt)
                            VALUES ({placeholders})
                        """
                        
                        # 批量插入
                        from datetime import date
                        today = date.today().isoformat()
                        batch_data = []
                        for row in rows:
                            row_values = [row.get(col) for col in column_names]
                            row_values.append(today)
                            batch_data.append(tuple(row_values))
                        
                        warehouse_cursor.executemany(insert_sql, batch_data)
                        synced_count += 1
                        
                except Exception as e:
                    print(f"⚠️  表 {table} 数据同步失败：{e}")
                    continue
            
            warehouse_conn.commit()
            
            mysql_conn.close()
            
            return {
                "success": True,
                "tables_synced": synced_count,
                "total_tables": len(tables)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def map_mysql_to_sqlite_type(mysql_type: str) -> str:
    """MySQL 类型映射到 SQLite 类型"""
    mysql_type = mysql_type.lower()

    if 'int' in mysql_type or 'integer' in mysql_type:
        return 'INTEGER'
    elif 'decimal' in mysql_type or 'numeric' in mysql_type or 'float' in mysql_type or 'double' in mysql_type:
        return 'DECIMAL(15,2)'
    elif 'datetime' in mysql_type or 'timestamp' in mysql_type:
        return 'DATETIME'
    elif 'date' in mysql_type:
        return 'DATE'
    elif 'text' in mysql_type or 'char' in mysql_type or 'varchar' in mysql_type:
        return 'TEXT'
    else:
        return 'TEXT'


def sync_sqlite_metadata(datasource_id: int, db_path: str, local_id: int):
    """同步 SQLite 元数据到数仓 ODS 层"""
    import sqlite3
    try:
        # 连接 SQLite 数据源
        sqlite_conn = sqlite3.connect(db_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()

        # 连接本地 SQLite 数仓
        with get_db_connection() as warehouse_conn:
            warehouse_cursor = warehouse_conn.cursor()

            # 获取 SQLite 所有用户表
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            tables = [row['name'] for row in sqlite_cursor.fetchall()]

            synced_count = 0

            for table in tables:
                # 获取表结构
                sqlite_cursor.execute(f"PRAGMA table_info(`{table}`)")
                columns = sqlite_cursor.fetchall()

                # 创建 ODS 表（如果不存在）
                ods_table_name = f"ods_{table}"

                # 构建列定义
                column_defs = []
                for col in columns:
                    col_name = col['name']
                    col_type = col['type'] or 'TEXT'
                    is_pk = col['pk'] == 1

                    col_def = f"`{col_name}` {col_type}"
                    if is_pk:
                        col_def += " PRIMARY KEY"

                    column_defs.append(col_def)

                # 添加数仓标准字段
                column_defs.append("`dt` DATE")
                column_defs.append("`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                # 创建 ODS 表
                create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {ods_table_name} (
                        {', '.join(column_defs)}
                    )
                """
                warehouse_cursor.execute(create_sql)

                # 同步数据（全量）
                try:
                    sqlite_cursor.execute(f"SELECT * FROM `{table}` LIMIT 10000")
                    rows = sqlite_cursor.fetchall()

                    if rows:
                        column_names = [col['name'] for col in columns]
                        placeholders = ', '.join(['?' for _ in column_names + ['dt']])
                        insert_sql = f"""
                            INSERT OR REPLACE INTO {ods_table_name}
                            ({', '.join([f'`{c}`' for c in column_names])}, dt)
                            VALUES ({placeholders})
                        """

                        from datetime import date
                        today = date.today().isoformat()
                        batch_data = []
                        for row in rows:
                            row_values = [row[col] for col in column_names]
                            row_values.append(today)
                            batch_data.append(tuple(row_values))

                        warehouse_cursor.executemany(insert_sql, batch_data)
                        synced_count += 1

                except Exception as e:
                    print(f"⚠️  表 {table} 数据同步失败：{e}")
                    continue

            warehouse_conn.commit()
            sqlite_conn.close()

            return {
                "success": True,
                "tables_synced": synced_count,
                "total_tables": len(tables)
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/{datasource_id}/metadata", response_model=dict)
async def get_datasource_metadata(
    datasource_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取数据源元数据（表列表）"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasources WHERE id = ?", (datasource_id,))
            datasource = cursor.fetchone()
            
            if not datasource:
                raise HTTPException(status_code=404, detail="数据源不存在")
            
            ds_dict = dict(datasource) if hasattr(datasource, 'keys') else datasource
        
        # 连接数据源获取元数据
        db_conn = get_database_connection(
            ds_dict['db_type'],
            ds_dict['host'],
            ds_dict['port'],
            ds_dict['database_name'],
            ds_dict['username'],
            ds_dict['password']
        )
        
        try:
            cursor = db_conn.cursor()
            
            # 根据数据库类型获取表列表
            if ds_dict['db_type'].lower() in ['mysql', 'mysql8', 'mariadb']:
                cursor.execute("SHOW TABLES")
                tables = [row[f"Tables_in_{ds_dict['database_name']}"] for row in cursor.fetchall()]
            elif ds_dict['db_type'].lower() == 'postgresql':
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
            elif ds_dict['db_type'].lower() == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
            elif ds_dict['db_type'].lower() == 'sqlserver':
                cursor.execute("""
                    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE='BASE TABLE' 
                    ORDER BY TABLE_NAME
                """)
                tables = [row[0] for row in cursor.fetchall()]
            else:
                raise HTTPException(status_code=400, detail=f"不支持的数据库类型：{ds_dict['db_type']}")
            
            return {
                "datasource_id": datasource_id,
                "datasource_name": ds_dict['name'],
                "db_type": ds_dict['db_type'],
                "tables": tables,
                "table_count": len(tables)
            }
        finally:
            db_conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取元数据失败：{str(e)}")


@router.get("/{datasource_id}/table-schema/{table_name}", response_model=dict)
async def get_table_schema(
    datasource_id: int,
    table_name: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取表结构（字段信息）"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasources WHERE id = ?", (datasource_id,))
            datasource = cursor.fetchone()
            
            if not datasource:
                raise HTTPException(status_code=404, detail="数据源不存在")
            
            ds_dict = dict(datasource) if hasattr(datasource, 'keys') else datasource
        
        # 连接数据源获取表结构
        db_conn = get_database_connection(
            ds_dict['db_type'],
            ds_dict['host'],
            ds_dict['port'],
            ds_dict['database_name'],
            ds_dict['username'],
            ds_dict['password']
        )
        
        try:
            cursor = db_conn.cursor()
            
            # 根据数据库类型获取表结构
            if ds_dict['db_type'].lower() in ['mysql', 'mysql8', 'mariadb']:
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                schema = [
                    {
                        "field": col.get('Field', col[0]),
                        "type": col.get('Type', col[1]),
                        "nullable": col.get('Null', col[2]) == 'YES',
                        "key": col.get('Key', col[3]),
                        "default": col.get('Default', col[4]),
                        "extra": col.get('Extra', col[5] if len(col) > 5 else '')
                    }
                    for col in columns
                ]
            elif ds_dict['db_type'].lower() == 'postgresql':
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                schema = [
                    {
                        "field": col[0],
                        "type": col[1],
                        "nullable": col[2] == 'YES',
                        "default": col[3]
                    }
                    for col in columns
                ]
            elif ds_dict['db_type'].lower() == 'sqlite':
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = cursor.fetchall()
                schema = [
                    {
                        "field": col[1],
                        "type": col[2],
                        "nullable": col[3] == 0,
                        "key": "PK" if col[5] else "",
                        "default": col[4]
                    }
                    for col in columns
                ]
            elif ds_dict['db_type'].lower() == 'sqlserver':
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (table_name,))
                columns = cursor.fetchall()
                schema = [
                    {
                        "field": col[0],
                        "type": col[1],
                        "nullable": col[2] == 'YES',
                        "default": col[3]
                    }
                    for col in columns
                ]
            else:
                raise HTTPException(status_code=400, detail=f"不支持的数据库类型：{ds_dict['db_type']}")
            
            return {
                "datasource_id": datasource_id,
                "table_name": table_name,
                "columns": schema,
                "column_count": len(schema)
            }
        finally:
            db_conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表结构失败：{str(e)}")


@router.post("/{datasource_id}/sync-metadata", response_model=dict)
async def sync_metadata(
    datasource_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """同步数据源元数据到数仓"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasources WHERE id = ?", (datasource_id,))
            datasource = cursor.fetchone()

            if not datasource:
                raise HTTPException(status_code=404, detail="数据源不存在")

            ds_dict = dict(datasource) if hasattr(datasource, 'keys') else datasource

        # 根据数据库类型调用不同的同步函数
        if ds_dict['db_type'].lower() in ['mysql', 'mysql8', 'mariadb']:
            result = sync_mysql_metadata(
                datasource_id,
                ds_dict['db_type'],
                ds_dict['host'],
                ds_dict['port'],
                ds_dict['database_name'],
                ds_dict['username'],
                ds_dict['password']
            )

            if result['success']:
                # 更新数据源状态
                cursor.execute("""
                    UPDATE datasources
                    SET status = 'active',
                        collect_metadata = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (datasource_id,))
                conn.commit()

                return {
                    "success": True,
                    "message": f"元数据同步完成：{result['tables_synced']}/{result['total_tables']} 表",
                    "tables_synced": result['tables_synced'],
                    "total_tables": result['total_tables']
                }
            else:
                raise HTTPException(status_code=500, detail=f"同步失败：{result['error']}")
        elif ds_dict['db_type'].lower() == 'sqlite':
            result = sync_sqlite_metadata(
                datasource_id,
                ds_dict['database_name'],
                datasource_id
            )

            if result['success']:
                cursor.execute("""
                    UPDATE datasources
                    SET status = 'active',
                        collect_metadata = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (datasource_id,))
                conn.commit()

                return {
                    "success": True,
                    "message": f"元数据同步完成：{result['tables_synced']}/{result['total_tables']} 表",
                    "tables_synced": result['tables_synced'],
                    "total_tables": result['total_tables']
                }
            else:
                raise HTTPException(status_code=500, detail=f"同步失败：{result['error']}")
        else:
            raise HTTPException(status_code=400, detail=f"暂不支持 {ds_dict['db_type']} 的元数据同步")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败：{str(e)}")


@router.post("/{datasource_id}/query", response_model=dict)
async def execute_query_on_datasource(
    datasource_id: int,
    query: dict,
    current_user: dict = Depends(get_current_admin_user)
):
    """在数据源上执行 SQL 查询"""
    try:
        sql = query.get('sql', '').strip()
        limit = query.get('limit', 100)
        
        if not sql:
            raise HTTPException(status_code=400, detail="SQL 语句不能为空")
        
        # 安全检查：只允许 SELECT 语句
        if not sql.upper().startswith('SELECT'):
            raise HTTPException(status_code=400, detail="只允许执行 SELECT 查询语句")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasources WHERE id = ?", (datasource_id,))
            datasource = cursor.fetchone()
            
            if not datasource:
                raise HTTPException(status_code=404, detail="数据源不存在")
            
            ds_dict = dict(datasource) if hasattr(datasource, 'keys') else datasource
        
        # 连接数据源执行查询
        db_conn = get_database_connection(
            ds_dict['db_type'],
            ds_dict['host'],
            ds_dict['port'],
            ds_dict['database_name'],
            ds_dict['username'],
            ds_dict['password']
        )
        
        try:
            cursor = db_conn.cursor()
            
            # 添加 LIMIT 限制（如果用户没有指定）
            if 'LIMIT' not in sql.upper() and limit > 0:
                sql = f"{sql} LIMIT {limit}"
            
            # 执行查询
            import time
            start_time = time.time()
            cursor.execute(sql)
            execution_time = time.time() - start_time
            
            # 获取结果
            if ds_dict['db_type'].lower() in ['mysql', 'mysql8', 'mariadb', 'sqlite']:
                rows = cursor.fetchall()
                # 转换为字典列表
                if rows:
                    if hasattr(rows[0], 'keys'):
                        columns = list(rows[0].keys())
                    else:
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    data = [dict(row) if hasattr(row, 'keys') else row for row in rows]
                else:
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    data = []
            else:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                data = [list(row) for row in rows]
            
            # 获取受影响行数
            row_count = len(data)
            
            return {
                "success": True,
                "datasource_id": datasource_id,
                "sql": sql,
                "columns": columns,
                "data": data,
                "row_count": row_count,
                "execution_time_ms": round(execution_time * 1000, 2),
                "limit": limit
            }
        finally:
            db_conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
