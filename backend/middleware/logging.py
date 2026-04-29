"""
请求日志中间件
记录所有 HTTP 请求的详细信息
"""
import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("uvicorn.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理函数
            
        Returns:
            响应对象
        """
        # 记录请求开始时间
        start_time = time.time()
        
        # 提取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # 获取请求头（脱敏处理）
        headers = dict(request.headers)
        self._sanitize_headers(headers)
        
        # 尝试读取请求体（不消耗流）
        body = await self._get_request_body(request)
        
        # 记录请求
        logger.info(
            f"请求开始：{method} {url}",
            extra={
                "request_method": method,
                "request_url": url,
                "client_host": client_host,
                "request_headers": headers,
                "request_body": body[:500] if body else None  # 限制长度
            }
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应
            logger.info(
                f"请求完成：{method} {url} - {response.status_code}",
                extra={
                    "request_method": method,
                    "request_url": url,
                    "response_status": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_host": client_host
                }
            )
            
            # 添加响应头（处理时间）
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常
            logger.error(
                f"请求失败：{method} {url} - {str(e)}",
                extra={
                    "request_method": method,
                    "request_url": url,
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_host": client_host
                },
                exc_info=True
            )
            
            raise
    
    async def _get_request_body(self, request: Request) -> str:
        """
        获取请求体（不消耗流）
        
        Args:
            request: 请求对象
            
        Returns:
            请求体字符串
        """
        try:
            # 只处理 JSON 请求
            content_type = request.headers.get("content-type", "")
            if "application/json" not in content_type:
                return ""
            
            # 读取请求体
            body = await request.body()
            
            # 尝试解析 JSON
            if body:
                try:
                    parsed = json.loads(body)
                    # 脱敏处理
                    self._sanitize_data(parsed)
                    return json.dumps(parsed, ensure_ascii=False)
                except json.JSONDecodeError:
                    return body.decode('utf-8', errors='ignore')
            
            return ""
            
        except Exception as e:
            logger.debug(f"读取请求体失败：{e}")
            return ""
    
    def _sanitize_headers(self, headers: dict) -> None:
        """
        脱敏请求头中的敏感信息
        
        Args:
            headers: 请求头字典（原地修改）
        """
        sensitive_keys = [
            'authorization',
            'cookie',
            'set-cookie',
            'x-api-key',
            'x-auth-token'
        ]
        
        for key in sensitive_keys:
            if key in headers:
                headers[key] = "***"
    
    def _sanitize_data(self, data: dict) -> None:
        """
        脱敏数据中的敏感字段
        
        Args:
            data: 数据字典（原地修改）
        """
        sensitive_fields = [
            'password',
            'token',
            'secret',
            'api_key',
            'apikey',
            'authorization',
            'credential'
        ]
        
        for key in data:
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                data[key] = "***"
            elif isinstance(data[key], dict):
                self._sanitize_data(data[key])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        添加安全响应头
        
        Args:
            request: 请求对象
            call_next: 下一个处理函数
            
        Returns:
            响应对象
        """
        response = await call_next(request)
        
        # 添加安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
