"""
缓存工具模块
提供 Redis 缓存功能
"""
import json
import logging
from typing import Optional, Any, Dict, List, Union
from datetime import timedelta
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from core.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis 缓存客户端"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.prefix = settings.REDIS_PREFIX
        self.default_ttl = settings.CACHE_DEFAULT_TTL
        self._connected = False
    
    async def connect(self) -> bool:
        """
        连接到 Redis
        
        Returns:
            是否连接成功
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis 客户端未安装，缓存功能不可用")
            return False
        
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            await self.redis.ping()
            self._connected = True
            logger.info(f"Redis 连接成功：{settings.REDIS_HOST}:{settings.REDIS_PORT}")
            return True
            
        except Exception as e:
            logger.warning(f"Redis 连接失败：{e}，缓存功能将不可用")
            self._connected = False
            return False
    
    async def disconnect(self):
        """断开 Redis 连接"""
        if self.redis and self._connected:
            await self.redis.close()
            self._connected = False
            logger.info("Redis 连接已关闭")
    
    def _make_key(self, key: str) -> str:
        """
        生成带前缀的缓存键
        
        Args:
            key: 原始键
            
        Returns:
            带前缀的完整键
        """
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回 None
        """
        if not self._connected:
            return None
        
        try:
            full_key = self._make_key(key)
            value = await self.redis.get(full_key)
            
            if value is None:
                return None
            
            # 尝试解析 JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"获取缓存失败：{key}, 错误：{e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值
            
        Returns:
            是否设置成功
        """
        if not self._connected:
            return False
        
        try:
            full_key = self._make_key(key)
            
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value, ensure_ascii=False)
            else:
                serialized = str(value)
            
            # 设置过期时间
            expire = ttl if ttl is not None else self.default_ttl
            
            await self.redis.set(full_key, serialized, ex=expire)
            logger.debug(f"缓存设置：{key} (TTL={expire}s)")
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败：{key}, 错误：{e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self._connected:
            return False
        
        try:
            full_key = self._make_key(key)
            await self.redis.delete(full_key)
            logger.debug(f"缓存删除：{key}")
            return True
            
        except Exception as e:
            logger.error(f"删除缓存失败：{key}, 错误：{e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        批量删除匹配模式的缓存
        
        Args:
            pattern: 键模式（支持通配符 *）
            
        Returns:
            删除的键数量
        """
        if not self._connected:
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = []
            
            async for key in self.redis.scan_iter(match=full_pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"批量删除缓存：{pattern}, 删除 {deleted} 个键")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"批量删除缓存失败：{pattern}, 错误：{e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if not self._connected:
            return False
        
        try:
            full_key = self._make_key(key)
            return await self.redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"检查缓存失败：{key}, 错误：{e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """
        获取缓存剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余秒数，-1 表示永不过期，-2 表示不存在
        """
        if not self._connected:
            return -2
        
        try:
            full_key = self._make_key(key)
            return await self.redis.ttl(full_key)
        except Exception as e:
            logger.error(f"获取 TTL 失败：{key}, 错误：{e}")
            return -2
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增缓存值（数字）
        
        Args:
            key: 缓存键
            amount: 递增数量
            
        Returns:
            递增后的值，失败返回 None
        """
        if not self._connected:
            return None
        
        try:
            full_key = self._make_key(key)
            return await self.redis.incr(full_key, amount)
        except Exception as e:
            logger.error(f"递增缓存失败：{key}, 错误：{e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not self._connected:
            return False
        
        try:
            full_key = self._make_key(key)
            return await self.redis.expire(full_key, ttl)
        except Exception as e:
            logger.error(f"设置过期时间失败：{key}, 错误：{e}")
            return False


# 缓存装饰器
def cache(
    key_prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[callable] = None
):
    """
    缓存装饰器
    
    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
        key_func: 自定义键生成函数
        
    Returns:
        装饰器
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from core.config import settings
            
            # 如果未启用 Redis，直接调用函数
            if not settings.REDIS_HOST or not REDIS_AVAILABLE:
                return await func(*args, **kwargs)
            
            # 生成缓存键
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # 默认使用参数哈希
                import hashlib
                param_str = f"{args}:{kwargs}"
                param_hash = hashlib.md5(param_str.encode()).hexdigest()
                cache_key = f"{key_prefix}:{param_hash}"
            
            # 尝试从缓存获取
            cache_client = get_cache()
            cached_value = await cache_client.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"缓存命中：{cache_key}")
                return cached_value
            
            # 调用函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await cache_client.set(cache_key, result, ttl)
                logger.debug(f"缓存写入：{cache_key}")
            
            return result
        
        return wrapper
    return decorator


# 全局缓存客户端实例
_cache_client: Optional[CacheClient] = None


def get_cache() -> CacheClient:
    """获取缓存客户端实例"""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client


async def init_cache() -> bool:
    """初始化缓存连接"""
    cache_client = get_cache()
    return await cache_client.connect()


async def close_cache():
    """关闭缓存连接"""
    cache_client = get_cache()
    await cache_client.disconnect()
