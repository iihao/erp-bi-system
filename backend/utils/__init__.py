"""
工具模块
提供缓存、数据库等工具函数
"""
from utils.cache import (
    CacheClient,
    get_cache,
    init_cache,
    close_cache,
    cache
)
from utils.database import (
    get_db_connection,
    get_db_pool,
    execute_query,
    execute_update,
    execute_many,
    dict_from_row,
    transaction,
    build_pagination,
    build_like_condition,
    build_in_condition,
    init_database,
    QueryProfiler
)

__all__ = [
    # Cache
    "CacheClient",
    "get_cache",
    "init_cache",
    "close_cache",
    "cache",
    
    # Database
    "get_db_connection",
    "get_db_pool",
    "execute_query",
    "execute_update",
    "execute_many",
    "dict_from_row",
    "transaction",
    "build_pagination",
    "build_like_condition",
    "build_in_condition",
    "init_database",
    "QueryProfiler",
]
