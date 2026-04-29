"""
ETL 作业定义 API
提供作业列表、创建、更新、删除等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/etl/jobs", tags=["ETL 作业定义"])

security = HTTPBearer()


# ===========================================
# 响应模型
# ===========================================

class ETLJobResponse(BaseModel):
    """ETL 作业响应"""
    job_id: int
    job_name: str
    description: str
    layer: str
    script_path: str
    status: str
    created_at: str
    updated_at: Optional[str]


class ETLJobCreateRequest(BaseModel):
    """创建作业请求"""
    job_name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    layer: str = Field(..., pattern="^(ODS|DWD|DWS|ADS)$")
    script_path: str


class ETLJobUpdateRequest(BaseModel):
    """更新作业请求"""
    job_name: Optional[str] = None
    description: Optional[str] = None
    layer: Optional[str] = None
    script_path: Optional[str] = None
    status: Optional[str] = None


class ETLJobListResponse(BaseModel):
    """作业列表响应"""
    items: List[ETLJobResponse]
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


# ===========================================
# API 接口
# ===========================================

@router.get("", response_model=ETLJobListResponse)
async def get_etl_jobs(
    layer: Optional[str] = Query(None, description="数仓分层筛选"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 ETL 作业定义列表"""
    where_clauses = []
    params = []

    if layer:
        where_clauses.append("layer = ?")
        params.append(layer)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT * FROM etl_jobs
        WHERE {where_sql}
        ORDER BY job_id
    """
    jobs = execute_query(sql, tuple(params))

    items = []
    for job in jobs:
        items.append(ETLJobResponse(
            job_id=job["job_id"],
            job_name=job["job_name"],
            description=job.get("description", ""),
            layer=job["layer"],
            script_path=job.get("script_path", ""),
            status=job.get("status", "active"),
            created_at=str(job["created_at"])[:19] if job.get("created_at") else "",
            updated_at=str(job["updated_at"])[:19] if job.get("updated_at") else None
        ))

    return ETLJobListResponse(items=items, total=len(items))


@router.get("/{job_id}", response_model=ETLJobResponse)
async def get_etl_job(
    job_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取单个作业定义"""
    sql = "SELECT * FROM etl_jobs WHERE job_id = ?"
    jobs = execute_query(sql, (job_id,))

    if not jobs:
        raise HTTPException(status_code=404, detail="作业不存在")

    job = jobs[0]
    return ETLJobResponse(
        job_id=job["job_id"],
        job_name=job["job_name"],
        description=job.get("description", ""),
        layer=job["layer"],
        script_path=job.get("script_path", ""),
        status=job.get("status", "active"),
        created_at=str(job["created_at"])[:19] if job.get("created_at") else "",
        updated_at=str(job["updated_at"])[:19] if job.get("updated_at") else None
    )


@router.post("", response_model=ETLJobResponse, status_code=status.HTTP_201_CREATED)
async def create_etl_job(
    request: ETLJobCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建新的 ETL 作业"""
    # 检查名称是否重复
    check_sql = "SELECT job_id FROM etl_jobs WHERE job_name = ?"
    if execute_query(check_sql, (request.job_name,)):
        raise HTTPException(status_code=400, detail="作业名称已存在")

    # 插入新作业
    insert_sql = """
        INSERT INTO etl_jobs (job_name, description, layer, script_path, status)
        VALUES (?, ?, ?, ?, 'active')
    """
    execute_update(insert_sql, (
        request.job_name,
        request.description,
        request.layer,
        request.script_path
    ))

    # 获取新创建的作业
    jobs = execute_query("SELECT * FROM etl_jobs WHERE job_name = ?", (request.job_name,))
    job = jobs[0]

    return ETLJobResponse(
        job_id=job["job_id"],
        job_name=job["job_name"],
        description=job.get("description", ""),
        layer=job["layer"],
        script_path=job.get("script_path", ""),
        status=job.get("status", "active"),
        created_at=str(job["created_at"])[:19] if job.get("created_at") else "",
        updated_at=None
    )


@router.put("/{job_id}", response_model=ETLJobResponse)
async def update_etl_job(
    job_id: int,
    request: ETLJobUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新 ETL 作业"""
    # 检查作业是否存在
    check_sql = "SELECT job_id FROM etl_jobs WHERE job_id = ?"
    if not execute_query(check_sql, (job_id,)):
        raise HTTPException(status_code=404, detail="作业不存在")

    # 构建更新字段
    update_fields = []
    params = []

    if request.job_name is not None:
        update_fields.append("job_name = ?")
        params.append(request.job_name)

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
        params.append(job_id)

        update_sql = f"""
            UPDATE etl_jobs
            SET {", ".join(update_fields)}
            WHERE job_id = ?
        """
        execute_update(update_sql, tuple(params))

    # 返回更新后的作业
    jobs = execute_query("SELECT * FROM etl_jobs WHERE job_id = ?", (job_id,))
    job = jobs[0]

    return ETLJobResponse(
        job_id=job["job_id"],
        job_name=job["job_name"],
        description=job.get("description", ""),
        layer=job["layer"],
        script_path=job.get("script_path", ""),
        status=job.get("status", "active"),
        created_at=str(job["created_at"])[:19] if job.get("created_at") else "",
        updated_at=str(job["updated_at"])[:19] if job.get("updated_at") else ""
    )


@router.delete("/{job_id}")
async def delete_etl_job(
    job_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除 ETL 作业"""
    # 检查作业是否存在
    check_sql = "SELECT job_id FROM etl_jobs WHERE job_id = ?"
    if not execute_query(check_sql, (job_id,)):
        raise HTTPException(status_code=404, detail="作业不存在")

    # 删除作业
    delete_sql = "DELETE FROM etl_jobs WHERE job_id = ?"
    execute_update(delete_sql, (job_id,))

    return {"message": "作业删除成功"}


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
