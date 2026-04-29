"""
数据库工具模块
提供优化的数据库操作，支持连接池和查询优化
"""
import os
import sqlite3
import logging
from typing import Optional, Dict, Any, List, ContextManager
from contextlib import contextmanager
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# SQLite 连接管理
# ===========================================

class SQLiteConnectionPool:
    """SQLite 连接池（线程安全版）"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        """
        初始化连接池
        
        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小
        """
        import threading
        self.db_path = db_path
        self.pool_size = pool_size
        self._lock = threading.Lock()
        self._initialized = False
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（线程安全）"""
        # 每次创建新连接，SQLite 线程安全模式下是安全的
        # 使用 check_same_thread=False 允许跨线程使用
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # 启用 WAL 模式（提高并发性能）
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            # 设置同步模式（NORMAL 平衡性能和安全性）
            conn.execute("PRAGMA synchronous=NORMAL")
            # 设置缓存大小（2000 页）
            conn.execute("PRAGMA cache_size=-2000")
            # 设置忙超时（5 秒）
            conn.execute("PRAGMA busy_timeout=5000")
        except Exception as e:
            logger.warning(f"设置 SQLite 优化参数失败：{e}")
        
        return conn
    
    def return_connection(self, conn: sqlite3.Connection):
        """归还数据库连接"""
        try:
            conn.close()
        except Exception as e:
            logger.error(f"关闭连接失败：{e}")


# 全局连接池实例
_db_pool: Optional[SQLiteConnectionPool] = None


def get_db_pool() -> SQLiteConnectionPool:
    """获取数据库连接池"""
    global _db_pool
    if _db_pool is None:
        db_path = settings.SQLITE_DB_PATH
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        _db_pool = SQLiteConnectionPool(
            db_path=db_path,
            pool_size=settings.DB_POOL_SIZE
        )
    return _db_pool


@contextmanager
def get_db_connection() -> ContextManager[sqlite3.Connection]:
    """
    获取数据库连接（上下文管理器）
    
    Yields:
        sqlite3.Connection: 数据库连接
    """
    pool = get_db_pool()
    conn = pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"数据库操作失败：{e}", exc_info=True)
        raise
    finally:
        pool.return_connection(conn)


# ===========================================
# 通用数据库操作
# ===========================================

def dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    """
    将数据库行转换为字典
    
    Args:
        row: 数据库行
        
    Returns:
        字典
    """
    if row is None:
        return {}
    return dict(row)


def execute_query(
    sql: str,
    params: tuple = None,
    fetch_one: bool = False
) -> List[Dict[str, Any]]:
    """
    执行查询并返回结果
    
    Args:
        sql: SQL 查询语句
        params: 查询参数
        fetch_one: 是否只返回一条记录
        
    Returns:
        查询结果列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if fetch_one:
                row = cursor.fetchone()
                return [dict_from_row(row)] if row else []
            else:
                rows = cursor.fetchall()
                return [dict_from_row(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"查询执行失败：{sql}, 错误：{e}")
            raise


def execute_update(sql: str, params: tuple = None) -> int:
    """
    执行更新操作
    
    Args:
        sql: SQL 更新语句
        params: 更新参数
        
    Returns:
        影响的行数
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            return cursor.rowcount
            
        except sqlite3.Error as e:
            logger.error(f"更新执行失败：{sql}, 错误：{e}")
            raise


def execute_many(sql: str, params_list: List[tuple]) -> int:
    """
    批量执行操作
        
    Args:
        sql: SQL 语句
        params_list: 参数列表
        
    Returns:
        影响的行数
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.executemany(sql, params_list)
            return cursor.rowcount
            
        except sqlite3.Error as e:
            logger.error(f"批量执行失败：{sql}, 错误：{e}")
            raise


# ===========================================
# 事务管理
# ===========================================

@contextmanager
def transaction():
    """
    事务上下文管理器
    
    Yields:
        数据库连接
        
    Example:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    pool = get_db_pool()
    conn = pool.get_connection()
    
    try:
        yield conn
        conn.commit()
        logger.debug("事务提交成功")
    except Exception as e:
        conn.rollback()
        logger.error(f"事务回滚：{e}", exc_info=True)
        raise
    finally:
        pool.return_connection(conn)


# ===========================================
# 查询构建辅助函数
# ===========================================

def build_pagination(
    page: int = 1,
    page_size: int = 10
) -> tuple[str, tuple]:
    """
    构建分页子句
    
    Args:
        page: 页码
        page_size: 每页数量
        
    Returns:
        (LIMIT/OFFSET 子句，参数元组)
    """
    offset = (page - 1) * page_size
    return "LIMIT ? OFFSET ?", (page_size, offset)


def build_like_condition(
    value: Optional[str],
    *columns: str
) -> tuple[str, list]:
    """
    构建 LIKE 查询条件
    
    Args:
        value: 搜索值
        columns: 要搜索的列名
        
    Returns:
        (WHERE 子句，参数列表)
    """
    if not value or not columns:
        return "", []
    
    conditions = []
    params = []
    
    pattern = f"%{value}%"
    for column in columns:
        conditions.append(f"{column} LIKE ?")
        params.append(pattern)
    
    if len(conditions) == 1:
        return conditions[0], params
    else:
        return f"({' OR '.join(conditions)})", params


def build_in_condition(
    values: Optional[List[Any]],
    column: str
) -> tuple[str, list]:
    """
    构建 IN 查询条件
    
    Args:
        values: 值列表
        column: 列名
        
    Returns:
        (IN 子句，参数列表)
    """
    if not values:
        return "", []
    
    placeholders = ','.join(['?' for _ in values])
    return f"{column} IN ({placeholders})", list(values)


# ===========================================
# 数据库初始化
# ===========================================

def init_database():
    """初始化数据库（创建表结构）"""
    from api.database import init_db
    init_db()
    logger.info("数据库初始化完成")


# ===========================================
# 性能监控
# ===========================================

class QueryProfiler:
    """查询性能分析器"""
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
    
    def start(self):
        """开始性能分析"""
        self.start_time = datetime.now()
        self.queries = []
    
    def record_query(
        self,
        sql: str,
        params: tuple = None,
        duration_ms: float = 0
    ):
        """
        记录查询
        
        Args:
            sql: SQL 语句
            params: 参数
            duration_ms: 执行时间（毫秒）
        """
        self.queries.append({
            "sql": sql,
            "params": params,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        })
    
    def stop(self) -> Dict[str, Any]:
        """
        停止性能分析并返回报告
        
        Returns:
            性能报告
        """
        if not self.start_time:
            return {}
        
        total_time = (datetime.now() - self.start_time).total_seconds() * 1000
        
        return {
            "total_time_ms": round(total_time, 2),
            "query_count": len(self.queries),
            "queries": self.queries,
            "slow_queries": [
                q for q in self.queries if q["duration_ms"] > 100
            ]
        }
