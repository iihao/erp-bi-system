"""
AI数据融合平台 Backend API
主应用入口
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field

# 导入核心模块
from core.config import settings
from core.security import get_current_user, get_password_hash, verify_password, create_access_token
from core.exceptions import (
    HTTPException,
    success_response,
    ErrorCode
)
from core.logging_config import setup_logging, get_logger
from utils.cache import init_cache, close_cache
from utils.database import init_database

# 导入中间件
from middleware.logging import RequestLoggingMiddleware, SecurityHeadersMiddleware
from middleware.rate_limit import RateLimitMiddleware

# 导入路由
from api.reports import router as reports_router
from api.ai_query import router as ai_query_router
from api.ai_config import router as ai_config_router
from api.ai_records import router as ai_records_router, router_portal as portal_ai_query_router, router_standard as standard_sql_router
from api.users import router as users_router
from api.roles import router as roles_router
from api.permissions import router as permissions_router
from api.report_manager import router as report_manager_router
from api.etl_manager import router as etl_manager_router
from api.etl_editor import router as etl_editor_router
from api.etl_datasource import router as etl_datasource_router
from api.etl_transform import router as etl_transform_router
from api.report_designer import router as report_designer_router
from api.monitor import router as monitor_router
from api.dashboard import router as dashboard_router
from api.datasources import router as datasources_router
from api.realestate import router as realestate_router
from api.portal import router as portal_router
from api.auth import router as auth_router

# 初始化日志
setup_logging()
logger = get_logger(__name__)


# ===========================================
# 生命周期管理
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    Args:
        app: FastAPI 应用
    """
    # 启动时执行
    logger.info("🚀 应用启动中...")
    
    # 初始化数据库
    try:
        init_database()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败：{e}")
    
    # 初始化缓存
    try:
        await init_cache()
        logger.info("✅ 缓存初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ 缓存初始化失败：{e}")
    
    logger.info(f"✅ 应用启动完成 - {settings.APP_NAME} v{settings.APP_VERSION}")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 应用关闭中...")
    
    # 关闭缓存连接
    try:
        await close_cache()
        logger.info("✅ 缓存连接已关闭")
    except Exception as e:
        logger.error(f"❌ 缓存关闭失败：{e}")
    
    logger.info("✅ 应用已关闭")


# ===========================================
# 创建 FastAPI 应用
# ===========================================

app = FastAPI(
    title=settings.APP_NAME,
    description="ERP Business Intelligence System Backend",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ===========================================
# 注册中间件
# ===========================================

# 1. 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 2. 安全响应头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 3. 速率限制中间件
app.add_middleware(RateLimitMiddleware)

# 4. CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

logger.info("✅ 中间件注册完成")


# ===========================================
# 请求/响应模型
# ===========================================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, description="密码")
    email: str = Field(default="", max_length=100, description="邮箱")


class TokenResponse(BaseModel):
    """Token 响应"""
    token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户响应"""
    username: str
    email: str


# ===========================================
# 公共端点
# ===========================================

@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return success_response(
        data={"status": "healthy", "message": "服务运行正常"},
        message="健康检查成功"
    )


@app.get("/api/v1/status", tags=["健康检查"])
async def api_status():
    """API 状态检查"""
    return success_response(
        data={
            "status": "ok",
            "version": settings.APP_VERSION,
            "service": settings.APP_NAME,
            "environment": settings.ENVIRONMENT
        },
        message="API 状态正常"
    )


# ===========================================
# 认证端点
# ===========================================

@app.post("/api/auth/login", response_model=TokenResponse, tags=["认证"])
async def login(request: LoginRequest):
    """
    用户登录
    
    Args:
        request: 登录请求
        
    Returns:
        Token 响应
        
    Raises:
        HTTPException: 认证失败
    """
    from utils.database import execute_query, execute_update
    
    # 从数据库查询用户
    users = execute_query(
        "SELECT * FROM users WHERE username = ?",
        (request.username,)
    )

    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.LOGIN_FAILED,
                "message": "用户名或密码错误"
            }
        )

    user = users[0]
    
    # 验证密码（使用 bcrypt）
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.LOGIN_FAILED,
                "message": "用户名或密码错误"
            }
        )

    # 检查用户状态
    if user.get("status") != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ErrorCode.USER_DISABLED,
                "message": "用户已被禁用"
            }
        )

    # 更新最后登录时间
    execute_update(
        "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (user["user_id"],)
    )

    # 创建 token
    access_token = create_access_token(
        data={"sub": str(user["user_id"])},
    )

    return TokenResponse(token=access_token)


@app.post("/api/auth/register", response_model=UserResponse, tags=["认证"])
async def register(request: RegisterRequest):
    """
    用户注册
    
    Args:
        request: 注册请求
        
    Returns:
        用户信息
        
    Raises:
        HTTPException: 注册失败
    """
    from utils.database import execute_query, execute_update
    
    # 检查用户名是否存在
    check_sql = "SELECT user_id FROM users WHERE username = ?"
    if execute_query(check_sql, (request.username,)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ErrorCode.USER_EXISTS,
                "message": "用户名已存在"
            }
        )

    # 创建新用户
    insert_sql = """
        INSERT INTO users (username, password_hash, email, real_name, role_id, status)
        VALUES (?, ?, ?, ?, 3, 1)
    """
    execute_update(
        insert_sql,
        (
            request.username,
            get_password_hash(request.password),
            request.email,
            request.email
        )
    )

    return UserResponse(username=request.username, email=request.email)


@app.get("/api/auth/me", tags=["认证"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    username = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    return success_response(
        data={"username": username},
        message="获取用户信息成功"
    )


# ===========================================
# 注册路由
# ===========================================

# 认证路由
if 'auth_router' in locals():
    app.include_router(auth_router)

# 报表和 AI 路由
app.include_router(reports_router)
app.include_router(ai_query_router)

# 后台管理路由
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(permissions_router)
app.include_router(report_manager_router)
app.include_router(etl_manager_router)
app.include_router(etl_editor_router)
app.include_router(etl_datasource_router)
app.include_router(etl_transform_router)
app.include_router(report_designer_router)
app.include_router(monitor_router)
app.include_router(dashboard_router)
app.include_router(ai_config_router)
app.include_router(ai_records_router)
app.include_router(standard_sql_router)
app.include_router(datasources_router)

# 地产 ERP 报表路由
app.include_router(realestate_router)

# 前台报表路由
app.include_router(portal_router)
app.include_router(portal_ai_query_router)

logger.info("✅ 路由注册完成")


# ===========================================
# 静态文件
# ===========================================

class SPAStaticFiles(StaticFiles):
    """支持 Vue Router history 模式的静态文件服务。"""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            accept = dict(scope.get("headers") or []).get(b"accept", b"").decode()
            if exc.status_code == 404 and "text/html" in accept:
                return await super().get_response("index.html", scope)
            raise


# 挂载静态文件目录（前端构建产物）
static_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if os.path.exists(static_dir):
    app.mount("/", SPAStaticFiles(directory=static_dir, html=True), name="static")
    logger.info(f"✅ 静态文件已挂载：{static_dir}")
else:
    logger.warning(f"⚠️ 前端静态文件目录不存在：{static_dir}")


# ===========================================
# 异常处理
# ===========================================

from core.exceptions import (
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from fastapi.exceptions import RequestValidationError

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

logger.info("✅ 异常处理器注册完成")


# ===========================================
# 主程序入口
# ===========================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 启动服务：{settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
