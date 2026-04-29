"""
日志配置模块
提供结构化日志、日志轮转和敏感信息过滤
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from datetime import datetime

from core.config import settings


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（用于控制台输出）"""
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class SensitiveFilter(logging.Filter):
    """敏感信息过滤器"""
    
    # 需要脱敏的字段
    SENSITIVE_FIELDS = [
        'password',
        'token',
        'secret',
        'key',
        'authorization',
        'cookie',
        'session'
    ]
    
    # 脱敏替换文本
    MASK = '***'
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤敏感信息
        
        Args:
            record: 日志记录
            
        Returns:
            True (允许日志通过)
        """
        # 过滤消息中的敏感信息
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._mask_sensitive(record.msg)
        
        # 过滤参数中的敏感信息
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._mask_sensitive(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _mask_sensitive(self, text: str) -> str:
        """
        脱敏敏感信息
        
        Args:
            text: 待脱敏文本
            
        Returns:
            脱敏后的文本
        """
        result = text
        for field in self.SENSITIVE_FIELDS:
            # 匹配 key: value 或 key=value 格式
            patterns = [
                f'{field}["\']?\\s*[:=]\\s*["\']?[^"\'\\s,}}]+',
                f'{field}=["\'][^"\']+["\']',
            ]
            import re
            for pattern in patterns:
                result = re.sub(
                    pattern,
                    f'{field}={self.MASK}',
                    result,
                    flags=re.IGNORECASE
                )
        return result


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        log_format: 日志格式
    """
    # 使用配置中的默认值
    level = getattr(logging, log_level or settings.LOG_LEVEL)
    log_file_path = log_file or settings.LOG_FILE
    log_fmt = log_format or settings.LOG_FORMAT
    
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # ===========================================
    # 控制台处理器（彩色输出）
    # ===========================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加敏感信息过滤器
    sensitive_filter = SensitiveFilter()
    console_handler.addFilter(sensitive_filter)
    
    root_logger.addHandler(console_handler)
    
    # ===========================================
    # 文件处理器（带轮转）
    # ===========================================
    # 按大小轮转
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(sensitive_filter)
    
    root_logger.addHandler(file_handler)
    
    # ===========================================
    # 错误日志文件（单独记录错误）
    # ===========================================
    error_log_path = os.path.join(
        os.path.dirname(log_file_path),
        'error.log'
    )
    error_handler = RotatingFileHandler(
        filename=error_log_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    error_handler.addFilter(sensitive_filter)
    
    root_logger.addHandler(error_handler)
    
    # ===========================================
    # 访问日志文件（用于记录 HTTP 请求）
    # ===========================================
    access_log_path = os.path.join(
        os.path.dirname(log_file_path),
        'access.log'
    )
    access_logger = logging.getLogger('uvicorn.access')
    access_handler = RotatingFileHandler(
        filename=access_log_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    access_handler.setFormatter(file_formatter)
    access_logger.addHandler(access_handler)
    
    # 记录日志系统初始化完成
    logging.info("日志系统初始化完成")
    logging.info(f"日志级别：{logging.getLevelName(level)}")
    logging.info(f"日志文件：{log_file_path}")
    logging.info(f"错误日志：{error_log_path}")
    logging.info(f"访问日志：{access_log_path}")


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


# ===========================================
# 日志装饰器
# ===========================================

def log_function_call(logger: Optional[logging.Logger] = None):
    """
    记录函数调用的装饰器
    
    Args:
        logger: 日志记录器，如果为 None 则使用函数所在模块的日志
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            log.debug(f"调用函数：{func.__name__}")
            try:
                result = await func(*args, **kwargs)
                log.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                log.error(f"函数 {func.__name__} 执行失败：{e}", exc_info=True)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            log.debug(f"调用函数：{func.__name__}")
            try:
                result = func(*args, **kwargs)
                log.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                log.error(f"函数 {func.__name__} 执行失败：{e}", exc_info=True)
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 自动初始化日志
setup_logging()
