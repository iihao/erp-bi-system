"""
自定义异常和错误处理
提供统一的异常处理机制和错误响应格式
"""
from typing import Optional, Any, Dict
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


# ===========================================
# 错误码定义
# ===========================================

class ErrorCode:
    """错误码定义"""
    
    # 通用错误 (1000-1999)
    SUCCESS = 0
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    PERMISSION_DENIED = 1002
    NOT_FOUND = 1003
    DUPLICATE_DATA = 1004
    
    # 认证错误 (2000-2999)
    UNAUTHORIZED = 2000
    TOKEN_EXPIRED = 2001
    TOKEN_INVALID = 2002
    LOGIN_FAILED = 2003
    USER_DISABLED = 2004
    
    # 用户错误 (3000-3999)
    USER_NOT_FOUND = 3000
    USER_EXISTS = 3001
    PASSWORD_ERROR = 3002
    PASSWORD_WEAK = 3003
    
    # 数据错误 (4000-4999)
    DATA_NOT_FOUND = 4000
    DATA_EXISTS = 4001
    DATA_INVALID = 4002
    
    # 系统错误 (5000-5999)
    DATABASE_ERROR = 5000
    CACHE_ERROR = 5001
    EXTERNAL_SERVICE_ERROR = 5002
    TIMEOUT_ERROR = 5003
    
    # AI 服务错误 (6000-6999)
    AI_SERVICE_ERROR = 6000
    AI_TIMEOUT = 6001
    AI_TOKEN_LIMIT = 6002
    
    # ETL 错误 (7000-7999)
    ETL_ERROR = 7000
    ETL_JOB_FAILED = 7001
    ETL_CONFIG_ERROR = 7002


# ===========================================
# 自定义异常类
# ===========================================

class APIException(HTTPException):
    """API 基础异常类"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: int = ErrorCode.UNKNOWN_ERROR,
        message: str = "操作失败",
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.detail = detail
        self.data = data
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "detail": detail
            }
        )


class UnauthorizedException(APIException):
    """未认证异常"""
    
    def __init__(
        self,
        message: str = "未认证或令牌已过期",
        error_code: int = ErrorCode.UNAUTHORIZED
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=message
        )


class ForbiddenException(APIException):
    """禁止访问异常"""
    
    def __init__(
        self,
        message: str = "权限不足",
        error_code: int = ErrorCode.PERMISSION_DENIED
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            message=message
        )


class NotFoundException(APIException):
    """资源未找到异常"""
    
    def __init__(
        self,
        message: str = "资源不存在",
        error_code: int = ErrorCode.NOT_FOUND
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            message=message
        )


class BadRequestException(APIException):
    """请求错误异常"""
    
    def __init__(
        self,
        message: str = "请求参数错误",
        error_code: int = ErrorCode.VALIDATION_ERROR,
        detail: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=message,
            detail=detail
        )


class DuplicateDataException(APIException):
    """数据重复异常"""
    
    def __init__(
        self,
        message: str = "数据已存在",
        error_code: int = ErrorCode.DUPLICATE_DATA
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            message=message
        )


class DatabaseException(APIException):
    """数据库异常"""
    
    def __init__(
        self,
        message: str = "数据库操作失败",
        detail: Optional[str] = None,
        error_code: int = ErrorCode.DATABASE_ERROR
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=message,
            detail=detail
        )


class AIServiceException(APIException):
    """AI 服务异常"""
    
    def __init__(
        self,
        message: str = "AI 服务调用失败",
        detail: Optional[str] = None,
        error_code: int = ErrorCode.AI_SERVICE_ERROR
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=error_code,
            message=message,
            detail=detail
        )


# ===========================================
# 统一异常处理器
# ===========================================

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    API 异常处理器
    
    Args:
        request: 请求对象
        exc: APIException 实例
        
    Returns:
        JSON 响应
    """
    logger.error(
        f"API 异常：{exc.status_code} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "detail": exc.detail
            },
            "data": exc.data
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 异常处理器（处理 FastAPI 内置的 HTTPException）
    
    Args:
        request: 请求对象
        exc: HTTPException 实例
        
    Returns:
        JSON 响应
    """
    logger.warning(
        f"HTTP 异常：{exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": str(exc.detail),
                "detail": None
            },
            "data": None
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError | ValidationError
) -> JSONResponse:
    """
    验证异常处理器
    
    Args:
        request: 请求对象
        exc: 验证异常实例
        
    Returns:
        JSON 响应
    """
    logger.warning(
        f"验证失败：{exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    errors = []
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", "")
            })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "请求参数验证失败",
                "detail": errors
            },
            "data": None
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器（捕获所有未处理的异常）
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSON 响应
    """
    logger.error(
        f"未处理的异常：{type(exc).__name__}: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.UNKNOWN_ERROR,
                "message": "服务器内部错误",
                "detail": "请稍后重试或联系管理员"
            },
            "data": None
        }
    )


# ===========================================
# 标准响应格式
# ===========================================

def success_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = status.HTTP_200_OK
) -> Dict[str, Any]:
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        status_code: HTTP 状态码
        
    Returns:
        标准成功响应字典
    """
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(
    message: str = "操作失败",
    error_code: int = ErrorCode.UNKNOWN_ERROR,
    detail: Optional[str] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> Dict[str, Any]:
    """
    错误响应
    
    Args:
        message: 错误消息
        error_code: 错误码
        detail: 错误详情
        status_code: HTTP 状态码
        
    Returns:
        标准错误响应字典
    """
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "detail": detail
        },
        "data": None
    }


def paginated_response(
    items: list,
    total: int,
    page: int = 1,
    page_size: int = 10,
    message: str = "查询成功"
) -> Dict[str, Any]:
    """
    分页响应
    
    Args:
        items: 数据列表
        total: 总数
        page: 页码
        page_size: 每页数量
        message: 成功消息
        
    Returns:
        标准分页响应字典
    """
    return {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }
