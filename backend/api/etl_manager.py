"""
ETL 管理 API
提供 ETL 任务管理、运行、日志查看、调度配置等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/etl", tags=["后台管理 - ETL 管理"])

security = HTTPBearer()


# ===========================================
# 请求/响应模型
# ===========================================

class ScheduleCreateRequest(BaseModel):
    """创建调度配置请求"""
    task_name: str = Field(..., min_length=2, max_length=100, description="任务名称")
    cron_expression: str = Field(..., min_length=5, max_length=50, description="Cron 表达式")
    is_enabled: bool = Field(True, description="是否启用")


class ScheduleUpdateRequest(BaseModel):
    """更新调度配置请求"""
    cron_expression: Optional[str] = Field(None, min_length=5, max_length=50, description="Cron 表达式")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class ETLTaskResponse(BaseModel):
    """ETL 任务响应"""
    task_id: int
    task_name: str
    description: str
    layer: str
    status: str
    last_run_at: Optional[str] = None
    last_duration: Optional[str] = None
    script: str
    schedule_enabled: bool = False
    schedule_cron: Optional[str] = None


class ETLTaskCreateRequest(BaseModel):
    """ETL 任务创建请求"""
    task_name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    layer: str = Field(..., pattern="^(ODS|DWD|DWS|ADS)$")
    script_path: str = Field(..., min_length=1, max_length=255)
    schedule_enabled: bool = False
    schedule_cron: str = ""


class ETLTaskUpdateRequest(BaseModel):
    """ETL 任务更新请求"""
    task_name: Optional[str] = None
    description: Optional[str] = None
    layer: Optional[str] = Field(default=None, pattern="^(ODS|DWD|DWS|ADS)$")
    script_path: Optional[str] = None
    status: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    schedule_cron: Optional[str] = None


class ETLTaskLogResponse(BaseModel):
    """ETL 任务日志响应"""
    log_id: int
    task_name: str
    task_layer: Optional[str]
    status: str
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[int]
    message: Optional[str]
    error_message: Optional[str]


class ETLScheduleResponse(BaseModel):
    """ETL 调度配置响应"""
    schedule_id: int
    task_name: str
    cron_expression: str
    is_enabled: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    created_at: str
    updated_at: Optional[str]


class ETLTaskListResponse(BaseModel):
    """ETL 任务列表响应"""
    items: List[ETLTaskResponse]
    total: int


class ETLStatsResponse(BaseModel):
    """ETL 统计响应"""
    totalJobs: int
    todaySuccess: int
    todayFailed: int
    successRate: float


class ETLLogListResponse(BaseModel):
    """ETL 日志列表响应"""
    items: List[ETLTaskLogResponse]
    total: int
    page: int
    page_size: int


class ETLScheduleListResponse(BaseModel):
    """ETL 调度列表响应"""
    items: List[ETLScheduleResponse]
    total: int


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


def get_task_status(task_name: str) -> str:
    """获取任务最新状态"""
    sql = """
        SELECT status FROM etl_task_logs
        WHERE task_name = ?
        ORDER BY log_id DESC
        LIMIT 1
    """
    results = execute_query(sql, (task_name,))
    return results[0]["status"] if results else "pending"


def get_task_last_run(task_name: str) -> Optional[Dict]:
    """获取任务最新运行记录"""
    sql = """
        SELECT * FROM etl_task_logs
        WHERE task_name = ?
        ORDER BY log_id DESC
        LIMIT 1
    """
    results = execute_query(sql, (task_name,))
    return results[0] if results else None


def get_schedule_for_task(task_name: str) -> Optional[Dict[str, Any]]:
    """获取任务的最新调度配置"""
    schedules = execute_query(
        "SELECT * FROM etl_schedules WHERE task_name = ? ORDER BY schedule_id DESC LIMIT 1",
        (task_name,)
    )
    return schedules[0] if schedules else None


def get_task_rows(layer: Optional[str] = None) -> List[Dict[str, Any]]:
    """从数据库读取 ETL 任务"""
    where_sql = ""
    params: List[Any] = []
    if layer:
        where_sql = "WHERE layer = ?"
        params.append(layer)

    jobs = execute_query(
        f"""
        SELECT * FROM etl_jobs
        {where_sql}
        ORDER BY job_id
        """,
        tuple(params)
    )

    if jobs:
        return jobs

    # 兜底：保留旧的静态任务，避免空表时页面无法展示
    fallback = [
        {
            "job_id": 1,
            "job_name": "ODS 数据抽取",
            "description": "从 MySQL 业务库抽取原始数据到 ODS 层",
            "layer": "ODS",
            "script_path": "ods_extract.py",
            "status": "active",
        },
        {
            "job_id": 2,
            "job_name": "DWD 数据清洗",
            "description": "清洗和标准化 ODS 层数据",
            "layer": "DWD",
            "script_path": "dwd_clean.py",
            "status": "active",
        },
        {
            "job_id": 3,
            "job_name": "DWS 数据聚合",
            "description": "轻度聚合生成汇总数据",
            "layer": "DWS",
            "script_path": "dws_aggregate.py",
            "status": "active",
        },
        {
            "job_id": 4,
            "job_name": "ADS 报表生成",
            "description": "生成面向应用的报表指标",
            "layer": "ADS",
            "script_path": "ads_report.py",
            "status": "active",
        }
    ]
    return [job for job in fallback if not layer or job["layer"] == layer]


def map_job_to_task_response(job: Dict[str, Any]) -> ETLTaskResponse:
    """将作业记录转换为前端任务响应"""
    task_name = job["job_name"]
    last_run = get_task_last_run(task_name)
    schedule = get_schedule_for_task(task_name)
    status = get_task_status(task_name)

    if status == "pending" and job.get("status") in {"running", "paused", "active"}:
        status = "pending" if job.get("status") == "active" else job.get("status")

    return ETLTaskResponse(
        task_id=job["job_id"],
        task_name=task_name,
        description=job.get("description", ""),
        layer=job["layer"],
        status=status,
        last_run_at=str(last_run["start_time"])[:19] if last_run and last_run.get("start_time") else None,
        last_duration=f"{last_run['duration_seconds']}s" if last_run and last_run.get("duration_seconds") else None,
        script=job.get("script_path", ""),
        schedule_enabled=bool(schedule["is_enabled"]) if schedule else False,
        schedule_cron=schedule["cron_expression"] if schedule else None
    )


def upsert_task_schedule(task_name: str, enabled: bool, cron_expression: str) -> None:
    """创建或更新任务调度"""
    existing = get_schedule_for_task(task_name)
    next_run = datetime.now() + timedelta(hours=1)

    if existing:
        execute_update(
            """
            UPDATE etl_schedules
            SET cron_expression = ?, is_enabled = ?, next_run_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE schedule_id = ?
            """,
            (cron_expression, 1 if enabled else 0, next_run, existing["schedule_id"])
        )
        return

    execute_update(
        """
        INSERT INTO etl_schedules (task_name, cron_expression, is_enabled, next_run_at)
        VALUES (?, ?, ?, ?)
        """,
        (task_name, cron_expression, 1 if enabled else 0, next_run)
    )


def update_latest_task_log(task_name: str, status: str, end_time: datetime, message: Optional[str] = None, error_message: Optional[str] = None, duration_seconds: Optional[int] = None) -> None:
    """更新最近一条任务日志，兼容 SQLite 不支持的 UPDATE ... ORDER BY LIMIT"""
    latest = execute_query(
        """
        SELECT log_id FROM etl_task_logs
        WHERE task_name = ? AND status = 'running'
        ORDER BY log_id DESC
        LIMIT 1
        """,
        (task_name,)
    )
    if not latest:
        return

    fields = ["status = ?", "end_time = ?"]
    params: List[Any] = [status, end_time]

    if duration_seconds is not None:
        fields.append("duration_seconds = ?")
        params.append(duration_seconds)
    if message is not None:
        fields.append("message = ?")
        params.append(message)
    if error_message is not None:
        fields.append("error_message = ?")
        params.append(error_message)

    params.append(latest[0]["log_id"])
    execute_update(
        f"UPDATE etl_task_logs SET {', '.join(fields)} WHERE log_id = ?",
        tuple(params)
    )


# ===========================================
# API 接口
# ===========================================

@router.get("/tasks", response_model=ETLTaskListResponse)
async def get_etl_tasks(
    layer: Optional[str] = Query(None, description="数仓分层筛选：ODS/DWD/DWS/ADS"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 ETL 任务列表"""
    rows = get_task_rows(layer)
    items = [map_job_to_task_response(row) for row in rows]
    return ETLTaskListResponse(items=items, total=len(items))


@router.get("/stats", response_model=ETLStatsResponse)
async def get_etl_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 ETL 统计数据"""
    total_jobs_result = execute_query("SELECT COUNT(*) as total FROM etl_jobs")
    total_jobs = total_jobs_result[0]["total"] if total_jobs_result else 0

    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)

    success_result = execute_query(
        """
        SELECT COUNT(*) as total FROM etl_task_logs
        WHERE status = 'success' AND start_time >= ? AND start_time < ?
        """,
        (start_time, end_time)
    )
    failed_result = execute_query(
        """
        SELECT COUNT(*) as total FROM etl_task_logs
        WHERE status = 'failed' AND start_time >= ? AND start_time < ?
        """,
        (start_time, end_time)
    )

    today_success = success_result[0]["total"] if success_result else 0
    today_failed = failed_result[0]["total"] if failed_result else 0
    total_runs = today_success + today_failed
    success_rate = round((today_success / total_runs) * 100, 2) if total_runs else 0

    return ETLStatsResponse(
        totalJobs=total_jobs,
        todaySuccess=today_success,
        todayFailed=today_failed,
        successRate=success_rate
    )


@router.post("/tasks", response_model=ETLTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_etl_task(
    request: ETLTaskCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建 ETL 任务"""
    if execute_query("SELECT job_id FROM etl_jobs WHERE job_name = ?", (request.task_name,)):
        raise HTTPException(status_code=400, detail="任务名称已存在")

    execute_update(
        """
        INSERT INTO etl_jobs (job_name, description, layer, script_path, status)
        VALUES (?, ?, ?, ?, 'active')
        """,
        (request.task_name, request.description, request.layer, request.script_path)
    )

    if request.schedule_enabled:
        upsert_task_schedule(request.task_name, True, request.schedule_cron or "0 2 * * *")

    job = execute_query("SELECT * FROM etl_jobs WHERE job_name = ?", (request.task_name,))[0]
    return map_job_to_task_response(job)


@router.put("/tasks/{task_id}", response_model=ETLTaskResponse)
async def update_etl_task(
    task_id: int,
    request: ETLTaskUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新 ETL 任务"""
    jobs = execute_query("SELECT * FROM etl_jobs WHERE job_id = ?", (task_id,))
    if not jobs:
        raise HTTPException(status_code=404, detail="任务不存在")

    job = jobs[0]
    new_name = request.task_name or job["job_name"]

    if request.task_name and request.task_name != job["job_name"]:
        if execute_query(
            "SELECT job_id FROM etl_jobs WHERE job_name = ? AND job_id != ?",
            (request.task_name, task_id)
        ):
            raise HTTPException(status_code=400, detail="任务名称已存在")

    update_fields = []
    params: List[Any] = []

    if request.task_name is not None:
        update_fields.append("job_name = ?")
        params.append(request.task_name)
    if request.description is not None:
        update_fields.append("description = ?")
        params.append(request.description)
    if request.layer is not None:
        update_fields.append("layer = ?")
        params.append(request.layer)
    if request.script_path is not None:
        update_fields.append("script_path = ?")
        params.append(request.script_path)
    if request.status is not None:
        update_fields.append("status = ?")
        params.append(request.status)

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)
        execute_update(
            f"UPDATE etl_jobs SET {', '.join(update_fields)} WHERE job_id = ?",
            tuple(params)
        )

    if request.schedule_enabled is not None or request.schedule_cron is not None:
        existing_schedule = get_schedule_for_task(job["job_name"])
        cron_expression = request.schedule_cron
        if cron_expression is None and existing_schedule:
            cron_expression = existing_schedule["cron_expression"]
        if cron_expression is None:
            cron_expression = "0 2 * * *"

        upsert_task_schedule(
            new_name,
            bool(request.schedule_enabled) if request.schedule_enabled is not None else bool(existing_schedule["is_enabled"]) if existing_schedule else False,
            cron_expression
        )

    updated_job = execute_query("SELECT * FROM etl_jobs WHERE job_id = ?", (task_id,))[0]
    return map_job_to_task_response(updated_job)


@router.post("/tasks/{task_id}/run")
async def run_etl_task(
    task_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """运行 ETL 任务（执行 script_sql）"""
    jobs = execute_query("SELECT * FROM etl_jobs WHERE job_id = ?", (task_id,))
    task = jobs[0] if jobs else None

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    script_sql = task.get("script_sql", "").strip()
    if not script_sql:
        raise HTTPException(status_code=400, detail="该任务未配置 SQL 脚本")

    start_time = datetime.now()

    try:
        # 创建日志记录
        execute_update(
            "INSERT INTO etl_task_logs (task_name, task_layer, status, start_time, message) VALUES (?, ?, 'running', ?, ?)",
            (task["job_name"], task["layer"], start_time, f"开始执行 {task['script_path']}")
        )

        # 分割并执行 SQL 语句
        from api.database import get_db_connection
        import sqlite3
        with get_db_connection() as conn:
            cursor = conn.cursor()
            statements = [s.strip() for s in script_sql.split(";") if s.strip()]
            total_affected = 0
            for stmt in statements:
                cursor.execute(stmt)
                total_affected += cursor.rowcount
            conn.commit()

        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())

        # 更新日志
        update_latest_task_log(
            task["job_name"],
            "success",
            end_time,
            message=f"执行成功，影响 {total_affected} 行，耗时 {duration}s",
            duration_seconds=duration
        )

        return {
            "message": "任务执行成功",
            "task_name": task["job_name"],
            "affected_rows": total_affected,
            "duration_seconds": duration
        }

    except Exception as e:
        update_latest_task_log(
            task["job_name"],
            "failed",
            datetime.now(),
            error_message=str(e)
        )

        raise HTTPException(status_code=500, detail=f"任务执行失败：{str(e)}")


@router.get("/tasks/{task_id}/log", response_model=ETLLogListResponse)
async def get_etl_task_logs(
    task_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 ETL 任务日志"""
    jobs = execute_query("SELECT * FROM etl_jobs WHERE job_id = ?", (task_id,))
    task = jobs[0] if jobs else None

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    offset = (page - 1) * page_size

    # 查询总数
    count_sql = "SELECT COUNT(*) as total FROM etl_task_logs WHERE task_name = ?"
    count_result = execute_query(count_sql, (task["job_name"],))
    total = count_result[0]["total"] if count_result else 0

    # 查询日志列表
    logs_sql = """
        SELECT * FROM etl_task_logs
        WHERE task_name = ?
        ORDER BY log_id DESC
        LIMIT ? OFFSET ?
    """
    logs = execute_query(logs_sql, (task["job_name"], page_size, offset))

    items = []
    for log in logs:
        items.append(ETLTaskLogResponse(
            log_id=log["log_id"],
            task_name=log["task_name"],
            task_layer=log.get("task_layer"),
            status=log["status"],
            start_time=str(log["start_time"])[:19] if log.get("start_time") else "",
            end_time=str(log["end_time"])[:19] if log.get("end_time") else "",
            duration_seconds=log.get("duration_seconds"),
            message=log.get("message"),
            error_message=log.get("error_message")
        ))

    return ETLLogListResponse(items=items, total=total, page=page, page_size=page_size)


@router.put("/tasks/{task_id}/schedule")
async def update_etl_task_schedule(
    task_id: int,
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_admin_user)
):
    """更新 ETL 任务调度配置"""
    jobs = execute_query("SELECT * FROM etl_jobs WHERE job_id = ?", (task_id,))
    if not jobs:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = jobs[0]
    schedule_enabled = bool(request.get("schedule_enabled", False))
    schedule_cron = request.get("schedule_cron") or "0 2 * * *"

    upsert_task_schedule(task["job_name"], schedule_enabled, schedule_cron)

    return {
        "message": "调度配置保存成功",
        "task_name": task["job_name"],
        "schedule_enabled": schedule_enabled,
        "schedule_cron": schedule_cron
    }


@router.get("/schedules", response_model=ETLScheduleListResponse)
async def get_etl_schedules(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 ETL 调度配置列表"""
    sql = "SELECT * FROM etl_schedules ORDER BY schedule_id"
    schedules = execute_query(sql)

    items = []
    for s in schedules:
        items.append(ETLScheduleResponse(
            schedule_id=s["schedule_id"],
            task_name=s["task_name"],
            cron_expression=s["cron_expression"],
            is_enabled=bool(s["is_enabled"]),
            last_run_at=str(s["last_run_at"])[:19] if s.get("last_run_at") else None,
            next_run_at=str(s["next_run_at"])[:19] if s.get("next_run_at") else None,
            created_at=str(s["created_at"])[:19] if s.get("created_at") else "",
            updated_at=str(s["updated_at"])[:19] if s.get("updated_at") else ""
        ))

    return ETLScheduleListResponse(items=items, total=len(items))


@router.post("/schedules", response_model=ETLScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_etl_schedule(
    request: ScheduleCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建 ETL 调度配置"""
    # 检查是否已存在
    check_sql = "SELECT schedule_id FROM etl_schedules WHERE task_name = ?"
    existing = execute_query(check_sql, (request.task_name,))

    if existing:
        raise HTTPException(status_code=400, detail="该任务的调度配置已存在")

    # 计算下次运行时间（简化处理）
    next_run = datetime.now() + timedelta(hours=1)

    # 插入调度配置
    insert_sql = """
        INSERT INTO etl_schedules (task_name, cron_expression, is_enabled, next_run_at)
        VALUES (?, ?, ?, ?)
    """
    execute_update(insert_sql, (
        request.task_name,
        request.cron_expression,
        1 if request.is_enabled else 0,
        next_run
    ))

    # 获取新创建的调度
    schedules = execute_query("SELECT * FROM etl_schedules WHERE task_name = ?", (request.task_name,))
    s = schedules[0]

    return ETLScheduleResponse(
        schedule_id=s["schedule_id"],
        task_name=s["task_name"],
        cron_expression=s["cron_expression"],
        is_enabled=bool(s["is_enabled"]),
        last_run_at=None,
        next_run_at=str(s["next_run_at"])[:19] if s.get("next_run_at") else None,
        created_at=str(s["created_at"])[:19] if s.get("created_at") else "",
        updated_at=None
    )


@router.put("/schedules/{schedule_id}", response_model=ETLScheduleResponse)
async def update_etl_schedule(
    schedule_id: int,
    request: ScheduleUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新 ETL 调度配置"""
    # 检查调度是否存在
    check_sql = "SELECT schedule_id FROM etl_schedules WHERE schedule_id = ?"
    if not execute_query(check_sql, (schedule_id,)):
        raise HTTPException(status_code=404, detail="调度配置不存在")

    # 构建更新字段
    update_fields = []
    params = []

    if request.cron_expression is not None:
        update_fields.append("cron_expression = ?")
        params.append(request.cron_expression)

    if request.is_enabled is not None:
        update_fields.append("is_enabled = ?")
        params.append(1 if request.is_enabled else 0)

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(schedule_id)

        update_sql = f"""
            UPDATE etl_schedules
            SET {", ".join(update_fields)}
            WHERE schedule_id = ?
        """
        execute_update(update_sql, tuple(params))

    # 返回更新后的调度
    schedules = execute_query("SELECT * FROM etl_schedules WHERE schedule_id = ?", (schedule_id,))
    s = schedules[0]

    return ETLScheduleResponse(
        schedule_id=s["schedule_id"],
        task_name=s["task_name"],
        cron_expression=s["cron_expression"],
        is_enabled=bool(s["is_enabled"]),
        last_run_at=str(s["last_run_at"])[:19] if s.get("last_run_at") else None,
        next_run_at=str(s["next_run_at"])[:19] if s.get("next_run_at") else None,
        created_at=str(s["created_at"])[:19] if s.get("created_at") else "",
        updated_at=str(s["updated_at"])[:19] if s.get("updated_at") else ""
    )


@router.delete("/schedules/{schedule_id}")
async def delete_etl_schedule(
    schedule_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除 ETL 调度配置"""
    # 检查调度是否存在
    check_sql = "SELECT schedule_id FROM etl_schedules WHERE schedule_id = ?"
    if not execute_query(check_sql, (schedule_id,)):
        raise HTTPException(status_code=404, detail="调度配置不存在")

    # 删除调度
    delete_sql = "DELETE FROM etl_schedules WHERE schedule_id = ?"
    execute_update(delete_sql, (schedule_id,))

    return {"message": "调度配置删除成功"}


@router.get("/layers/options")
async def get_layer_options(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取数仓分层选项"""
    return [
        {"value": "ODS", "label": "ODS - 原始数据层"},
        {"value": "DWD", "label": "DWD - 明细数据层"},
        {"value": "DWS", "label": "DWS - 汇总数据层"},
        {"value": "ADS", "label": "ADS - 应用数据层"}
    ]
