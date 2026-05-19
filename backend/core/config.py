"""
核心配置模块
使用 Pydantic Settings 进行配置管理和验证
"""
import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ===========================================
    # 应用配置
    # ===========================================
    APP_NAME: str = Field(default="AI数据融合平台", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    ENVIRONMENT: str = Field(default="development", description="环境：development/production/testing")
    
    # ===========================================
    # 服务配置
    # ===========================================
    HOST: str = Field(default="0.0.0.0", description="服务主机")
    PORT: int = Field(default=8001, description="服务端口")
    WORKERS: int = Field(default=4, description="工作进程数")

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        """兼容 release/production 等非布尔环境值，避免启动失败。"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
                return False
        return bool(value)

    # ===========================================
    # JWT 配置
    # ===========================================
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production-at-least-32-chars",
        description="JWT 密钥"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="Access Token 过期时间 (分钟)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh Token 过期时间 (天)")
    
    # ===========================================
    # 数据库配置
    # ===========================================
    USE_SQLITE: bool = Field(default=True, description="是否使用 SQLite")
    SQLITE_DB_PATH: str = Field(default="./db/erp_bi.db", description="SQLite 数据库路径")
    
    # MySQL 配置（生产环境）
    MYSQL_HOST: str = Field(default="localhost", description="MySQL 主机")
    MYSQL_PORT: int = Field(default=3306, description="MySQL 端口")
    MYSQL_USER: str = Field(default="erp_bi_user", description="MySQL 用户名")
    MYSQL_PASSWORD: str = Field(default="erp_bi_pass", description="MySQL 密码")
    MYSQL_DATABASE: str = Field(default="erp_bi", description="MySQL 数据库名")
    
    # 连接池配置
    DB_POOL_SIZE: int = Field(default=5, description="数据库连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=10, description="数据库连接池最大溢出数")
    DB_POOL_TIMEOUT: int = Field(default=30, description="数据库连接池超时时间 (秒)")
    DB_POOL_RECYCLE: int = Field(default=1800, description="数据库连接回收时间 (秒)")
    
    # ===========================================
    # Redis 配置（缓存）
    # ===========================================
    REDIS_HOST: str = Field(default="localhost", description="Redis 主机")
    REDIS_PORT: int = Field(default=6379, description="Redis 端口")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis 密码")
    REDIS_DB: int = Field(default=0, description="Redis 数据库编号")
    REDIS_PREFIX: str = Field(default="erp_bi:", description="Redis 键前缀")
    CACHE_DEFAULT_TTL: int = Field(default=300, description="默认缓存过期时间 (秒)")
    
    # ===========================================
    # 安全配置
    # ===========================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://localhost:9098"],
        description="CORS 允许的源"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="CORS 允许凭证")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], description="CORS 允许的方法")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="CORS 允许的头部")
    
    # 密码策略
    PASSWORD_MIN_LENGTH: int = Field(default=6, description="密码最小长度")
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt 加密轮数")
    
    # 速率限制
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用速率限制")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="速率限制请求数")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="速率限制时间窗口 (秒)")
    
    # ===========================================
    # AI 配置（百炼 API）
    # ===========================================
    DASHSCOPE_API_KEY: Optional[str] = Field(default=None, description="百炼 API 密钥")
    DASHSCOPE_BASE_URL: str = Field(
        default="https://coding.dashscope.aliyuncs.com/v1",
        description="百炼 API 基础 URL"
    )
    DASHSCOPE_MODEL: str = Field(default="qwen3.5-plus", description="百炼 AI 模型")
    
    # ===========================================
    # 日志配置
    # ===========================================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件路径")
    LOG_MAX_BYTES: int = Field(default=10485760, description="日志文件最大大小 (10MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="日志文件备份数量")
    
    # ===========================================
    # 验证器
    # ===========================================
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """验证 JWT 密钥长度"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY 必须至少 32 个字符")
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证环境值"""
        allowed = ["development", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT 必须是 {allowed} 之一")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in allowed:
            raise ValueError(f"LOG_LEVEL 必须是 {allowed} 之一")
        return v
    
    # ===========================================
    # 辅助方法
    # ===========================================
    @property
    def database_url(self) -> str:
        """获取数据库 URL"""
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_DB_PATH}"
        else:
            return f"mysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def redis_url(self) -> str:
        """获取 Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.ENVIRONMENT == "testing"


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例（用于依赖注入）"""
    return settings
