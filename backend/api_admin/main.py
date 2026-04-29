"""
AI数据融合后台 API
运行端口：8001
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import timedelta
import os

# 导入认证模块
from api.auth import get_current_user, create_access_token, verify_password, get_password_hash, decode_token
from api.database import execute_query, execute_update

# 导入后台管理路由
from .users import router as users_router
from .roles import router as roles_router
from .permissions import router as permissions_router
from .etl_jobs import router as etl_jobs_router
from .etl_dev import router as etl_dev_router
from .reports import router as reports_router
from .monitor import router as monitor_router
from .logs import router as logs_router
from .ai_records import router as ai_records_router
from .dashboard import router as dashboard_router
from api.etl_manager import router as etl_manager_router
from api.etl_transform import router as etl_transform_router
from api.etl_datasource import router as etl_datasource_router

app = FastAPI(
    title="AI数据融合后台 API",
    description="AI数据融合后台管理系统",
    version="1.0.0"
)

# CORS 配置 - 允许管理前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "admin-api", "port": 8001}


@app.get("/api/status")
async def api_status():
    """API 状态"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "erp-bi-admin"
    }


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """管理员登录"""
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

    access_token = create_access_token(
        data={"sub": str(user["user_id"])},
        expires_delta=timedelta(hours=24)
    )

    return TokenResponse(token=access_token)


@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# 注册所有后台管理路由
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(permissions_router)
app.include_router(etl_jobs_router)
app.include_router(etl_dev_router)
app.include_router(etl_manager_router)
app.include_router(etl_transform_router)
app.include_router(etl_datasource_router)
app.include_router(reports_router)
app.include_router(monitor_router)
app.include_router(logs_router)
app.include_router(ai_records_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
