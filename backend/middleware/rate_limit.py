"""
速率限制中间件
防止 API 滥用和 DDoS 攻击
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from core.config import settings

logger = logging.getLogger("uvicorn.access")


class RateLimiter:
    """速率限制器（基于内存）"""
    
    def __init__(self):
        # 存储每个 IP 的请求记录：{ip: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_ip: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        检查请求是否允许
        
        Args:
            client_ip: 客户端 IP
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
            
        Returns:
            (是否允许，剩余请求数)
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # 清理过期的请求记录
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if ts > window_start
        ]
        
        # 检查是否超过限制
        request_count = len(self.requests[client_ip])
        remaining = max_requests - request_count
        
        if request_count >= max_requests:
            return False, 0
        
        # 记录当前请求
        self.requests[client_ip].append(current_time)
        
        return True, remaining - 1
    
    def cleanup(self):
        """清理所有过期的请求记录"""
        current_time = time.time()
        # 默认清理 1 小时前的记录
        window_start = current_time - 3600
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                ts for ts in self.requests[ip]
                if ts > window_start
            ]
            if not self.requests[ip]:
                del self.requests[ip]


# 全局速率限制器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, max_requests: int = None, window_seconds: int = None):
        """
        初始化中间件
        
        Args:
            app: FastAPI 应用
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
        """
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW
        self.enabled = settings.RATE_LIMIT_ENABLED
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理函数
            
        Returns:
            响应对象
            
        Raises:
            HTTPException: 超过速率限制
        """
        # 如果未启用，直接跳过
        if not self.enabled:
            return await call_next(request)
        
        # 获取客户端 IP
        client_ip = self._get_client_ip(request)
        
        # 检查速率限制
        allowed, remaining = rate_limiter.is_allowed(
            client_ip,
            self.max_requests,
            self.window_seconds
        )
        
        if not allowed:
            # 记录超限请求
            logger.warning(
                f"速率限制：{client_ip} 超过限制 ({self.max_requests}/{self.window_seconds}s)"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": 1005,
                    "message": "请求过于频繁，请稍后重试",
                    "detail": f"限制：{self.max_requests} 请求/{self.window_seconds}秒",
                    "retry_after": self.window_seconds
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + self.window_seconds)
                }
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制响应头
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_seconds)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实 IP
        
        Args:
            request: 请求对象
            
        Returns:
            客户端 IP 地址
        """
        # 检查 X-Forwarded-For 头（经过代理的情况）
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # 取第一个 IP（最原始的客户端 IP）
            return forwarded_for.split(",")[0].strip()
        
        # 检查 X-Real-IP 头
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # 使用直接连接的 IP
        if request.client:
            return request.client.host
        
        return "unknown"


class SlidingWindowRateLimiter:
    """滑动窗口速率限制器（更精确）"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_ip: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        检查请求是否允许（滑动窗口算法）
        
        Args:
            client_ip: 客户端 IP
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
            
        Returns:
            (是否允许，剩余请求数，重置时间戳)
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # 清理过期的请求记录
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if ts > window_start
        ]
        
        # 计算当前窗口内的请求数
        request_count = len(self.requests[client_ip])
        remaining = max(0, max_requests - request_count)
        
        # 计算重置时间（窗口中最早的请求过期时间）
        if self.requests[client_ip]:
            reset_time = int(self.requests[client_ip][0] + window_seconds)
        else:
            reset_time = int(current_time + window_seconds)
        
        if request_count >= max_requests:
            return False, 0, reset_time
        
        # 记录当前请求
        self.requests[client_ip].append(current_time)
        
        return True, remaining - 1, reset_time
