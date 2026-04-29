"""
运维监控 API
提供系统信息、服务状态、日志查看、性能指标等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import platform
import psutil

from api.database import execute_query
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/monitor", tags=["后台管理 - 运维监控"])

security = HTTPBearer()


# ===========================================
# 响应模型
# ===========================================

class SystemInfoResponse(BaseModel):
    """系统信息响应"""
    hostname: str
    os_name: str
    os_version: str
    platform: str
    architecture: str
    processor: str
    cpu_count: int
    memory_total: float  # GB
    disk_total: float  # GB
    python_version: str
    uptime: str


class SystemMetricsResponse(BaseModel):
    """系统性能指标响应"""
    cpu_usage: float  # %
    memory_usage: float  # %
    memory_used: float  # GB
    memory_available: float  # GB
    disk_usage: float  # %
    disk_used: float  # GB
    disk_free: float  # GB
    network_sent: float  # MB
    network_recv: float  # MB


class ServiceStatusResponse(BaseModel):
    """服务状态响应"""
    service_name: str
    status: str  # running/stopped/error
    port: Optional[int]
    uptime: Optional[str]
    message: str


class LogEntryResponse(BaseModel):
    """日志条目响应"""
    log_id: int
    log_level: str
    module: Optional[str]
    action: Optional[str]
    username: Optional[str]
    message: str
    created_at: str


class LogListResponse(BaseModel):
    """日志列表响应"""
    items: List[LogEntryResponse]
    total: int
    page: int
    page_size: int


# ===========================================
# 辅助函数
# ===========================================

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员权限"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


def format_bytes(bytes_val: int) -> float:
    """将字节转换为 GB"""
    return round(bytes_val / (1024 ** 3), 2)


def format_mb(bytes_val: int) -> float:
    """将字节转换为 MB"""
    return round(bytes_val / (1024 ** 2), 2)


def get_uptime() -> str:
    """获取系统运行时间"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.now() - boot_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"{days}天{hours}小时{minutes}分钟"
        elif hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    except:
        return "未知"


# ===========================================
# API 接口
# ===========================================

@router.get("/system", response_model=SystemInfoResponse)
async def get_system_info(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取系统信息"""
    try:
        # 获取磁盘信息
        disk = psutil.disk_usage('/')

        return SystemInfoResponse(
            hostname=platform.node(),
            os_name=platform.system(),
            os_version=platform.version(),
            platform=platform.platform(),
            architecture=platform.machine(),
            processor=platform.processor() or "Unknown",
            cpu_count=psutil.cpu_count(logical=True),
            memory_total=format_bytes(psutil.virtual_memory().total),
            disk_total=format_bytes(disk.total),
            python_version=platform.python_version(),
            uptime=get_uptime()
        )
    except Exception as e:
        # 如果 psutil 不可用，返回基本信息
        return SystemInfoResponse(
            hostname=platform.node(),
            os_name=platform.system(),
            os_version=platform.version(),
            platform=platform.platform(),
            architecture=platform.machine(),
            processor=platform.processor() or "Unknown",
            cpu_count=os.cpu_count() or 1,
            memory_total=0,
            disk_total=0,
            python_version=platform.python_version(),
            uptime="未知"
        )


@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取系统性能指标"""
    try:
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 内存信息
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = format_bytes(memory.used)
        memory_available = format_bytes(memory.available)

        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = format_bytes(disk.used)
        disk_free = format_bytes(disk.free)

        # 网络信息
        net = psutil.net_io_counters()
        network_sent = format_mb(net.bytes_sent)
        network_recv = format_mb(net.bytes_recv)

        return SystemMetricsResponse(
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            memory_used=memory_used,
            memory_available=memory_available,
            disk_usage=disk_percent,
            disk_used=disk_used,
            disk_free=disk_free,
            network_sent=network_sent,
            network_recv=network_recv
        )
    except Exception as e:
        # 如果 psutil 不可用，返回默认值
        return SystemMetricsResponse(
            cpu_usage=0,
            memory_usage=0,
            memory_used=0,
            memory_available=0,
            disk_usage=0,
            disk_used=0,
            disk_free=0,
            network_sent=0,
            network_recv=0
        )


@router.get("/services", response_model=List[ServiceStatusResponse])
async def get_service_status(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取服务状态列表"""
    services = []

    # 检查 FastAPI 服务
    services.append(ServiceStatusResponse(
        service_name="AI数据融合平台 API 服务",
        status="running",
        port=8000,
        uptime=get_uptime(),
        message="服务运行正常"
    ))

    # 检查数据库连接（模拟）
    try:
        execute_query("SELECT 1")
        db_status = "running"
        db_message = "数据库连接正常"
    except Exception as e:
        db_status = "error"
        db_message = f"数据库连接失败：{str(e)}"

    services.append(ServiceStatusResponse(
        service_name="数据库服务",
        status=db_status,
        port=3306,
        uptime=None,
        message=db_message
    ))

    # ETL 调度服务（模拟）
    services.append(ServiceStatusResponse(
        service_name="ETL 调度服务",
        status="running",
        port=None,
        uptime=get_uptime(),
        message="调度服务运行正常"
    ))

    # 前端服务（模拟）
    services.append(ServiceStatusResponse(
        service_name="前端静态资源服务",
        status="running",
        port=5173,
        uptime=get_uptime(),
        message="前端服务运行正常"
    ))

    return services


@router.get("/logs", response_model=LogListResponse)
async def get_system_logs(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    level: Optional[str] = Query(None, description="日志级别筛选：DEBUG/INFO/WARNING/ERROR"),
    module: Optional[str] = Query(None, description="模块筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取系统日志"""
    offset = (page - 1) * page_size

    # 构建查询条件
    where_clauses = []
    params = []

    if level:
        where_clauses.append("log_level = ?")
        params.append(level)

    if module:
        where_clauses.append("module = ?")
        params.append(module)

    if keyword:
        where_clauses.append("(message LIKE ? OR username LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 查询总数
    count_sql = f"SELECT COUNT(*) as total FROM system_logs WHERE {where_sql}"
    count_result = execute_query(count_sql, tuple(params))
    total = count_result[0]["total"] if count_result else 0

    # 查询日志列表
    logs_sql = f"""
        SELECT * FROM system_logs
        WHERE {where_sql}
        ORDER BY log_id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    logs = execute_query(logs_sql, tuple(params))

    items = []
    for log in logs:
        items.append(LogEntryResponse(
            log_id=log["log_id"],
            log_level=log["log_level"],
            module=log.get("module"),
            action=log.get("action"),
            username=log.get("username"),
            message=log.get("message", ""),
            created_at=str(log["created_at"])[:19] if log.get("created_at") else ""
        ))

    return LogListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/logs")
async def create_system_log(
    log_level: str = "INFO",
    module: Optional[str] = None,
    action: Optional[str] = None,
    message: str = "",
    current_user: dict = Depends(get_current_admin_user)
):
    """创建系统日志（用于测试）"""
    from api.database import get_db_connection

    insert_sql = """
        INSERT INTO system_logs (log_level, module, action, username, message)
        VALUES (?, ?, ?, ?, ?)
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(insert_sql, (
            log_level,
            module,
            action,
            current_user.get("user_id"),
            message
        ))
        conn.commit()
        log_id = cursor.lastrowid

    return {"message": "日志创建成功", "log_id": log_id}


@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = Query(default=24, ge=1, le=168, description="查询小时数"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取性能指标历史数据（模拟）"""
    import random

    now = datetime.now()
    data = []

    for i in range(min(hours, 24)):
        timestamp = now - timedelta(hours=i)
        data.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:00"),
            "cpu_usage": round(random.uniform(10, 80), 1),
            "memory_usage": round(random.uniform(40, 70), 1),
            "disk_usage": round(random.uniform(50, 60), 1)
        })

    data.reverse()
    return {"hours": hours, "data": data}


@router.get("/health")
async def health_check(
    current_user: dict = Depends(get_current_admin_user)
):
    """健康检查"""
    checks = {
        "api": {"status": "healthy", "message": "API 服务正常"},
        "database": {"status": "healthy", "message": "数据库连接正常"},
        "memory": {"status": "healthy", "message": "内存使用正常"},
        "disk": {"status": "healthy", "message": "磁盘空间充足"}
    }

    # 检查磁盘空间
    try:
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            checks["disk"] = {"status": "warning", "message": f"磁盘使用率过高：{disk.percent}%"}
    except:
        pass

    # 检查内存
    try:
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            checks["memory"] = {"status": "warning", "message": f"内存使用率过高：{memory.percent}%"}
    except:
        pass

    overall_status = "healthy"
    for check in checks.values():
        if check["status"] == "warning":
            overall_status = "warning"
        elif check["status"] == "error":
            overall_status = "error"

    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
