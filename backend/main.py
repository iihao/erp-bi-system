from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import os
import logging
from datetime import timedelta
from api.auth import get_current_user, create_access_token, verify_password, get_password_hash

logger = logging.getLogger(__name__)
from api.database import execute_query, execute_update
from api.reports import router as reports_router
from api.ai_query import router as ai_query_router
from api.ai_config import router as ai_config_router
from api.ai_records import router as ai_records_router, router_portal as portal_ai_query_router, router_standard as standard_sql_router
# 后台管理路由
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
from api_admin.dashboard import router as admin_dashboard_router
from api.datasources import router as datasources_router
from api.update_logs import router as update_logs_router
# 地产 ERP 报表路由
from api.realestate import router as realestate_router
# 前台报表路由
from api.portal import router as portal_router
# 社交功能路由
from api.likes import router as likes_router
from api.follows import router as follows_router
from api.comments import router as comments_router
from api.profile import router as profile_router
from api.treehole import router as treehole_router
from api.discovery import router as discovery_router
from api.messages import router as messages_router, announcement_router
# 后台管理补充路由
from api_admin.etl_jobs import router as admin_etl_jobs_router
from api_admin.etl_dev import router as admin_etl_dev_router

app = FastAPI(
    title="AI数据融合平台 API",
    description="AI数据融合平台后端服务",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# 全局异常处理
# ===========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器，捕获所有未处理的异常
    
    Args:
        request: 请求对象
        exc: 异常对象
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"未处理的异常：{exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "error_code": 5000,
                "message": "服务器内部错误",
                "detail": str(exc) if app.debug else None
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器
    
    Args:
        request: 请求对象
        exc: HTTP 异常对象
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "error_code": exc.status_code,
                "message": exc.detail,
            }
        }
    )

# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""

# 响应模型
class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    username: str
    email: str


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "Service is running"}


@app.get("/api/v1/status")
async def api_status():
    """API 状态检查"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "erp-bi-system"
    }


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    # 从数据库查询用户
    users = execute_query("SELECT * FROM users WHERE username = ?", (request.username,))

    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = users[0]
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间
    execute_update("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user["user_id"],))

    # 创建 token
    access_token = create_access_token(
        data={"sub": str(user["user_id"])},
        expires_delta=timedelta(hours=24)
    )

    return TokenResponse(token=access_token)


@app.post("/api/auth/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """用户注册"""
    # 检查用户名是否存在
    check_sql = "SELECT user_id FROM users WHERE username = ?"
    if execute_query(check_sql, (request.username,)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 创建新用户
    insert_sql = """
        INSERT INTO users (username, password_hash, email, real_name, role_id, status)
        VALUES (?, ?, ?, ?, 3, 1)
    """
    execute_update(insert_sql, (request.username, get_password_hash(request.password), request.email, request.email))

    return UserResponse(username=request.username, email=request.email)


@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    username = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    return {"username": username}


# 注册报表路由和 AI 查询路由
app.include_router(reports_router)
app.include_router(ai_query_router)
app.include_router(ai_query_router, prefix="/api")

# 注册后台管理路由
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(permissions_router)
app.include_router(report_manager_router)
app.include_router(etl_manager_router)
app.include_router(etl_editor_router)
app.include_router(etl_datasource_router)
app.include_router(etl_transform_router)
app.include_router(admin_etl_jobs_router)
app.include_router(admin_etl_dev_router)
app.include_router(report_designer_router)
app.include_router(monitor_router)
app.include_router(dashboard_router)
app.include_router(admin_dashboard_router)
app.include_router(ai_config_router)
app.include_router(ai_records_router)
app.include_router(standard_sql_router)
app.include_router(datasources_router)
app.include_router(update_logs_router)

# 注册地产 ERP 报表路由
app.include_router(realestate_router)

# 注册前台报表路由
app.include_router(portal_router)
app.include_router(portal_ai_query_router)

# 注册社交功能路由
app.include_router(likes_router)
app.include_router(follows_router)
app.include_router(comments_router)
app.include_router(profile_router)
app.include_router(treehole_router)
app.include_router(discovery_router)

# 注册消息功能路由
app.include_router(messages_router)
app.include_router(announcement_router)

# 挂载上传文件目录（头像等）
upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
if os.path.exists(upload_dir):
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
else:
    os.makedirs(upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

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
else:
    print(f"警告：前端静态文件目录不存在：{static_dir}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
