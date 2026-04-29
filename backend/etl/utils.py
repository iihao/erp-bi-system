"""
ETL 工具函数模块
提供通用的数据库操作、数据质量检查、日志记录等功能
"""
import sqlite3
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple, ContextManager
from contextlib import contextmanager
from datetime import datetime, date
import logging
import time
from functools import wraps

from .config import etl_config, get_config

logger = logging.getLogger(__name__)


# ============================================
# 数据库连接管理
# ============================================

@contextmanager
def sqlite_connection(db_path: Optional[str] = None):
    """SQLite 连接上下文管理器"""
    if not db_path:
        db_path = etl_config.db.SQLITE_DB_PATH
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.debug(f"✅ SQLite 连接成功：{db_path}")
        yield conn
    except Exception as e:
        logger.error(f"❌ SQLite 连接失败：{e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("SQLite 连接已关闭")


@contextmanager
def mysql_connection():
    """MySQL 连接上下文管理器"""
    conn = None
    try:
        conn = mysql.connector.connect(
            host=etl_config.db.MYSQL_HOST,
            port=etl_config.db.MYSQL_PORT,
            user=etl_config.db.MYSQL_USER,
            password=etl_config.db.MYSQL_PASSWORD,
            database=etl_config.db.MYSQL_DATABASE,
            charset='utf8mb4',
            use_unicode=True,
            connection_timeout=etl_config.db.POOL_TIMEOUT
        )
        logger.debug(f"✅ MySQL 连接成功：{etl_config.db.MYSQL_HOST}:{etl_config.db.MYSQL_PORT}")
        yield conn
    except Error as e:
        logger.error(f"❌ MySQL 连接失败：{e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()
            logger.debug("MySQL 连接已关闭")


# ============================================
# 重试装饰器
# ============================================

def retry_on_failure(max_retries: int = None, delay: int = None):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    if max_retries is None:
        max_retries = etl_config.MAX_RETRIES
    if delay is None:
        delay = etl_config.RETRY_DELAY
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"⚠️  {func.__name__} 失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} 最终失败：{e}")
            
            raise last_exception
        return wrapper
    return decorator


# ============================================
# 数据质量检查
# ============================================

class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def check_null_values(self, data: List[Dict], columns: List[str], table_name: str) -> bool:
        """检查空值"""
        error_count = 0
        for row in data:
            for col in columns:
                if row.get(col) is None:
                    self.errors.append(f"{table_name}.{col} 发现空值")
                    error_count += 1
        
        if error_count > 0:
            logger.error(f"❌ {table_name} 发现 {error_count} 个空值错误")
            return False
        
        logger.info(f"✅ {table_name} 空值检查通过")
        return True
    
    def check_duplicate_keys(self, data: List[Dict], key_column: str, table_name: str) -> bool:
        """检查主键重复"""
        keys = [row.get(key_column) for row in data if row.get(key_column)]
        unique_keys = set(keys)
        
        if len(keys) != len(unique_keys):
            dup_count = len(keys) - len(unique_keys)
            self.errors.append(f"{table_name}.{key_column} 发现 {dup_count} 个重复键")
            logger.error(f"❌ {table_name} 主键重复：{dup_count}")
            return False
        
        logger.info(f"✅ {table_name} 主键唯一性检查通过")
        return True
    
    def check_data_range(self, data: List[Dict], column: str, 
                         min_val: Any = None, max_val: Any = None, 
                         table_name: str = None) -> bool:
        """检查数据范围"""
        error_count = 0
        
        for row in data:
            val = row.get(column)
            if val is not None:
                if min_val is not None and val < min_val:
                    self.errors.append(f"{table_name}.{column} 值 {val} 小于最小值 {min_val}")
                    error_count += 1
                if max_val is not None and val > max_val:
                    self.errors.append(f"{table_name}.{column} 值 {val} 大于最大值 {max_val}")
                    error_count += 1
        
        if error_count > 0:
            logger.error(f"❌ {table_name}.{column} 发现 {error_count} 个范围错误")
            return False
        
        logger.info(f"✅ {table_name}.{column} 范围检查通过")
        return True
    
    def check_referential_integrity(self, child_data: List[Dict], child_column: str,
                                     parent_data: List[Dict], parent_column: str,
                                     child_table: str, parent_table: str) -> bool:
        """检查参照完整性"""
        parent_keys = set(row.get(parent_column) for row in parent_data if row.get(parent_column))
        error_count = 0
        
        for row in child_data:
            child_key = row.get(child_column)
            if child_key and child_key not in parent_keys:
                self.errors.append(f"{child_table}.{child_column}={child_key} 在 {parent_table} 中不存在")
                error_count += 1
        
        if error_count > 0:
            logger.error(f"❌ 参照完整性检查失败：{error_count} 个外键错误")
            return False
        
        logger.info(f"✅ {child_table} → {parent_table} 参照完整性检查通过")
        return True
    
    def get_report(self) -> Dict[str, Any]:
        """获取检查报告"""
        return {
            'passed': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }


# ============================================
# 批量处理工具
# ============================================

def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分块"""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


@retry_on_failure()
def batch_insert(cursor, sql: str, data: List[Tuple], batch_size: int = None):
    """
    批量插入数据
    
    Args:
        cursor: 数据库游标
        sql: 插入 SQL
        data: 数据列表
        batch_size: 批次大小
    """
    if not batch_size:
        batch_size = etl_config.BATCH_SIZE
    
    chunks = chunk_list(data, batch_size)
    total_inserted = 0
    
    for i, chunk in enumerate(chunks):
        cursor.executemany(sql, chunk)
        total_inserted += len(chunk)
        logger.debug(f"  批次 {i + 1}/{len(chunks)}: 插入 {len(chunk)} 条记录")
    
    return total_inserted


# ============================================
# 日期工具
# ============================================

def get_date_key(dt: date = None) -> str:
    """获取日期键（格式：YYYYMMDD）"""
    if dt is None:
        dt = etl_config.DT
    return dt.strftime('%Y%m%d')


def get_date_range(start_date: date, end_date: date) -> List[date]:
    """获取日期范围"""
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


def parse_date_key(date_key: str) -> date:
    """解析日期键"""
    return datetime.strptime(date_key, '%Y%m%d').date()


# ============================================
# 性能监控
# ============================================

class ETLMetrics:
    """ETL 性能指标"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.start_time = None
        self.end_time = None
        self.records_processed = 0
        self.errors = []
    
    def start(self):
        """开始计时"""
        self.start_time = datetime.now()
        logger.info(f"🚀 {self.task_name} 开始执行")
    
    def stop(self):
        """停止计时"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"✅ {self.task_name} 完成，耗时 {duration:.2f}秒，处理 {self.records_processed} 条记录")
        return duration
    
    def add_records(self, count: int):
        """增加处理记录数"""
        self.records_processed += count
    
    def add_error(self, error: str):
        """添加错误记录"""
        self.errors.append(error)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'task_name': self.task_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'records_processed': self.records_processed,
            'error_count': len(self.errors),
            'errors': self.errors[:10]  # 只返回前 10 个错误
        }
