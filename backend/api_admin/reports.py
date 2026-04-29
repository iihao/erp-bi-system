"""
报表配置 API
提供报表定义、配置管理、发布等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/reports", tags=["报表配置"])

security = HTTPBearer()


# ===========================================
# 响应模型
# ===========================================

class ReportConfigResponse(BaseModel):
    """报表配置响应"""
    report_id: int
    report_name: str
    report_code: str
    description: str
    report_type: str
    config: Dict[str, Any]
    status: str
    published_at: Optional[str]
    created_at: str
    updated_at: Optional[str]


class ReportConfigCreateRequest(BaseModel):
    """创建报表配置请求"""
    report_name: str = Field(..., min_length=2, max_length=200)
    report_code: str = Field(..., min_length=2, max_length=50)
    description: str = ""
    report_type: str = Field(default="table", pattern="^(table|chart|dashboard)$")
    config: Dict[str, Any] = Field(default_factory=dict)


class ReportConfigUpdateRequest(BaseModel):
    """更新报表配置请求"""
    report_name: Optional[str] = None
    description: Optional[str] = None
    report_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ReportConfigListResponse(BaseModel):
    """报表配置列表响应"""
    items: List[ReportConfigResponse]
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

@router.get("", response_model=ReportConfigListResponse)
async def get_report_configs(
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    report_type: Optional[str] = Query(None, description="类型筛选"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取报表配置列表"""
    where_clauses = []
    params = []

    if status_filter:
        where_clauses.append("status = ?")
        params.append(status_filter)

    if report_type:
        where_clauses.append("report_type = ?")
        params.append(report_type)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT * FROM report_configs
        WHERE {where_sql}
        ORDER BY report_id DESC
    """
    reports = execute_query(sql, tuple(params))

    items = []
    for report in reports:
        # 解析 config JSON
        import json
        config = {}
        if report.get("config"):
            try:
                config = json.loads(report["config"]) if isinstance(report["config"], str) else report["config"]
            except:
                config = {}

        items.append(ReportConfigResponse(
            report_id=report["report_id"],
            report_name=report["report_name"],
            report_code=report["report_code"],
            description=report.get("description", ""),
            report_type=report["report_type"],
            config=config,
            status=report.get("status", "draft"),
            published_at=str(report["published_at"])[:19] if report.get("published_at") else None,
            created_at=str(report["created_at"])[:19] if report.get("created_at") else "",
            updated_at=str(report["updated_at"])[:19] if report.get("updated_at") else None
        ))

    return ReportConfigListResponse(items=items, total=len(items))


@router.get("/{report_id}", response_model=ReportConfigResponse)
async def get_report_config(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取单个报表配置"""
    sql = "SELECT * FROM report_configs WHERE report_id = ?"
    reports = execute_query(sql, (report_id,))

    if not reports:
        raise HTTPException(status_code=404, detail="报表配置不存在")

    report = reports[0]
    import json
    config = {}
    if report.get("config"):
        try:
            config = json.loads(report["config"]) if isinstance(report["config"], str) else report["config"]
        except:
            config = {}

    return ReportConfigResponse(
        report_id=report["report_id"],
        report_name=report["report_name"],
        report_code=report["report_code"],
        description=report.get("description", ""),
        report_type=report["report_type"],
        config=config,
        status=report.get("status", "draft"),
        published_at=str(report["published_at"])[:19] if report.get("published_at") else None,
        created_at=str(report["created_at"])[:19] if report.get("created_at") else "",
        updated_at=str(report["updated_at"])[:19] if report.get("updated_at") else None
    )


@router.post("", response_model=ReportConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_report_config(
    request: ReportConfigCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建新的报表配置"""
    # 检查编码是否重复
    check_sql = "SELECT report_id FROM report_configs WHERE report_code = ?"
    if execute_query(check_sql, (request.report_code,)):
        raise HTTPException(status_code=400, detail="报表编码已存在")

    # 插入新配置
    import json
    insert_sql = """
        INSERT INTO report_configs (report_name, report_code, description, report_type, config, status)
        VALUES (?, ?, ?, ?, ?, 'draft')
    """
    execute_update(insert_sql, (
        request.report_name,
        request.report_code,
        request.description,
        request.report_type,
        json.dumps(request.config)
    ))

    # 获取新创建的配置
    reports = execute_query("SELECT * FROM report_configs WHERE report_code = ?", (request.report_code,))
    report = reports[0]

    config = {}
    if report.get("config"):
        try:
            config = json.loads(report["config"]) if isinstance(report["config"], str) else report["config"]
        except:
            config = {}

    return ReportConfigResponse(
        report_id=report["report_id"],
        report_name=report["report_name"],
        report_code=report["report_code"],
        description=report.get("description", ""),
        report_type=report["report_type"],
        config=config,
        status=report.get("status", "draft"),
        published_at=None,
        created_at=str(report["created_at"])[:19] if report.get("created_at") else "",
        updated_at=None
    )


@router.put("/{report_id}", response_model=ReportConfigResponse)
async def update_report_config(
    report_id: int,
    request: ReportConfigUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新报表配置"""
    # 检查配置是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表配置不存在")

    # 构建更新字段
    update_fields = []
    params = []

    if request.report_name is not None:
        update_fields.append("report_name = ?")
        params.append(request.report_name)

    if request.description is not None:
        update_fields.append("description = ?")
        params.append(request.description)

    if request.report_type is not None:
        update_fields.append("report_type = ?")
        params.append(request.report_type)

    if request.config is not None:
        import json
        update_fields.append("config = ?")
        params.append(json.dumps(request.config))

    if request.status is not None:
        update_fields.append("status = ?")
        params.append(request.status)
        # 如果发布，设置发布时间
        if request.status == "published":
            update_fields.append("published_at = CURRENT_TIMESTAMP")

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(report_id)

        update_sql = f"""
            UPDATE report_configs
            SET {", ".join(update_fields)}
            WHERE report_id = ?
        """
        execute_update(update_sql, tuple(params))

    # 返回更新后的配置
    reports = execute_query("SELECT * FROM report_configs WHERE report_id = ?", (report_id,))
    report = reports[0]

    import json
    config = {}
    if report.get("config"):
        try:
            config = json.loads(report["config"]) if isinstance(report["config"], str) else report["config"]
        except:
            config = {}

    return ReportConfigResponse(
        report_id=report["report_id"],
        report_name=report["report_name"],
        report_code=report["report_code"],
        description=report.get("description", ""),
        report_type=report["report_type"],
        config=config,
        status=report.get("status", "draft"),
        published_at=str(report["published_at"])[:19] if report.get("published_at") else None,
        created_at=str(report["created_at"])[:19] if report.get("created_at") else "",
        updated_at=str(report["updated_at"])[:19] if report.get("updated_at") else ""
    )


@router.delete("/{report_id}")
async def delete_report_config(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除报表配置"""
    # 检查配置是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表配置不存在")

    # 删除配置
    delete_sql = "DELETE FROM report_configs WHERE report_id = ?"
    execute_update(delete_sql, (report_id,))

    return {"message": "报表配置删除成功"}


@router.post("/{report_id}/publish")
async def publish_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """发布报表"""
    # 检查配置是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表配置不存在")

    # 更新状态为已发布
    update_sql = """
        UPDATE report_configs
        SET status = 'published', published_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE report_id = ?
    """
    execute_update(update_sql, (report_id,))

    return {"message": "报表发布成功"}


@router.post("/{report_id}/unpublish")
async def unpublish_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """下线报表"""
    # 检查配置是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表配置不存在")

    # 更新状态为草稿
    update_sql = """
        UPDATE report_configs
        SET status = 'draft', updated_at = CURRENT_TIMESTAMP
        WHERE report_id = ?
    """
    execute_update(update_sql, (report_id,))

    return {"message": "报表已下线"}


@router.get("/types/options")
async def get_report_type_options(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取报表类型选项"""
    return [
        {"value": "table", "label": "表格报表"},
        {"value": "chart", "label": "图表报表"},
        {"value": "dashboard", "label": "仪表板"}
    ]
