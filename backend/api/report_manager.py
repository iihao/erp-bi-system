"""
报表管理 API
提供报表配置、发布、删除等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/reports", tags=["后台管理 - 报表管理"])

security = HTTPBearer()


# ===========================================
# 请求/响应模型
# ===========================================

class ReportCreateRequest(BaseModel):
    """创建报表请求"""
    report_code: Optional[str] = Field(None, max_length=50, description="报表编码")
    report_name: str = Field(..., min_length=2, max_length=100, description="报表名称")
    report_type: str = Field(..., description="报表类型：chart-图表，table-表格，kpi-指标")
    report_category: Optional[str] = Field("basic", description="报表分类：basic/analysis/advanced")
    description: Optional[str] = Field(None, max_length=200, description="报表描述")
    sql_query: Optional[str] = Field(None, description="SQL 查询语句")
    config_json: Optional[Dict[str, Any]] = Field(None, description="图表配置 JSON")


class ReportUpdateRequest(BaseModel):
    """更新报表请求"""
    report_code: Optional[str] = Field(None, max_length=50, description="报表编码")
    report_name: Optional[str] = Field(None, min_length=2, max_length=100, description="报表名称")
    report_type: Optional[str] = Field(None, description="报表类型")
    report_category: Optional[str] = Field(None, description="报表分类")
    description: Optional[str] = Field(None, max_length=200, description="报表描述")
    sql_query: Optional[str] = Field(None, description="SQL 查询语句")
    config_json: Optional[Dict[str, Any]] = Field(None, description="图表配置 JSON")


class ReportResponse(BaseModel):
    """报表响应"""
    report_id: int
    report_code: Optional[str]
    report_name: str
    report_type: str
    report_category: Optional[str]
    description: Optional[str]
    sql_query: Optional[str]
    config_json: Optional[Dict[str, Any]]
    status: str
    created_by: Optional[int]
    created_at: str
    updated_at: Optional[str]
    published_at: Optional[str]


class ReportListResponse(BaseModel):
    """报表列表响应"""
    items: List[ReportResponse]
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


def row_to_report_response(row: dict) -> ReportResponse:
    """将数据库行转换为报表响应"""
    import json
    config_json = row.get("config_json")
    if config_json and isinstance(config_json, str):
        try:
            config_json = json.loads(config_json)
        except:
            pass

    return ReportResponse(
        report_id=row["report_id"],
        report_code=row.get("report_code"),
        report_name=row["report_name"],
        report_type=row["report_type"],
        report_category=row.get("report_category"),
        description=row.get("description"),
        sql_query=row.get("sql_query"),
        config_json=config_json,
        status=row.get("status", "draft"),
        created_by=row.get("created_by"),
        created_at=str(row.get("created_at", ""))[:19] if row.get("created_at") else "",
        updated_at=str(row.get("updated_at", ""))[:19] if row.get("updated_at") else "",
        published_at=str(row.get("published_at", ""))[:19] if row.get("published_at") else ""
    )


# ===========================================
# API 接口
# ===========================================

@router.get("", response_model=ReportListResponse)
async def get_reports(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    report_type: Optional[str] = Query(None, description="报表类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选：draft/published/archived"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取报表列表"""
    offset = (page - 1) * page_size

    # 构建查询条件
    where_clauses = []
    params = []

    if keyword:
        where_clauses.append("(report_name LIKE ? OR description LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if report_type:
        where_clauses.append("report_type = ?")
        params.append(report_type)

    if status:
        where_clauses.append("status = ?")
        params.append(status)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 查询总数
    count_sql = f"SELECT COUNT(*) as total FROM report_configs WHERE {where_sql}"
    count_result = execute_query(count_sql, tuple(params))
    total = count_result[0]["total"] if count_result else 0

    # 查询报表列表
    reports_sql = f"""
        SELECT * FROM report_configs
        WHERE {where_sql}
        ORDER BY report_id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    reports = execute_query(reports_sql, tuple(params))

    items = [row_to_report_response(r) for r in reports]

    return ReportListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取报表详情"""
    sql = "SELECT * FROM report_configs WHERE report_id = ?"
    reports = execute_query(sql, (report_id,))

    if not reports:
        raise HTTPException(status_code=404, detail="报表不存在")

    return row_to_report_response(reports[0])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建新报表"""
    import json

    # 检查报表名是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_name = ?"
    existing = execute_query(check_sql, (request.report_name,))

    if existing:
        raise HTTPException(status_code=400, detail="报表名称已存在")

    # 插入新报表
    insert_sql = """
        INSERT INTO report_configs (report_code, report_name, report_type, report_category, description, sql_query, config_json, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    config_json_str = json.dumps(request.config_json) if request.config_json else None

    execute_update(insert_sql, (
        request.report_code,
        request.report_name,
        request.report_type,
        request.report_category or "basic",
        request.description,
        request.sql_query,
        config_json_str,
        current_user.get("user_id")
    ))

    # 获取新创建的报表
    reports = execute_query("SELECT * FROM report_configs WHERE report_name = ?", (request.report_name,))

    return row_to_report_response(reports[0])


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    request: ReportUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新报表配置"""
    import json

    # 检查报表是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表不存在")

    # 构建更新字段
    update_fields = []
    params = []

    if request.report_code is not None:
        update_fields.append("report_code = ?")
        params.append(request.report_code)

    if request.report_name is not None:
        update_fields.append("report_name = ?")
        params.append(request.report_name)

    if request.report_type is not None:
        update_fields.append("report_type = ?")
        params.append(request.report_type)

    if request.report_category is not None:
        update_fields.append("report_category = ?")
        params.append(request.report_category)

    if request.description is not None:
        update_fields.append("description = ?")
        params.append(request.description)

    if request.sql_query is not None:
        update_fields.append("sql_query = ?")
        params.append(request.sql_query)

    if request.config_json is not None:
        update_fields.append("config_json = ?")
        params.append(json.dumps(request.config_json))

    if not update_fields:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(report_id)

    update_sql = f"""
        UPDATE report_configs
        SET {", ".join(update_fields)}
        WHERE report_id = ?
    """
    execute_update(update_sql, tuple(params))

    return await get_report(report_id, current_user)


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除报表"""
    # 检查报表是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表不存在")

    # 删除报表
    delete_sql = "DELETE FROM report_configs WHERE report_id = ?"
    execute_update(delete_sql, (report_id,))

    return {"message": "报表删除成功"}


@router.post("/{report_id}/publish")
async def publish_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """发布报表"""
    # 检查报表是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表不存在")

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
    """取消发布报表（归档）"""
    # 检查报表是否存在
    check_sql = "SELECT report_id FROM report_configs WHERE report_id = ?"
    if not execute_query(check_sql, (report_id,)):
        raise HTTPException(status_code=404, detail="报表不存在")

    # 更新状态为已归档
    update_sql = """
        UPDATE report_configs
        SET status = 'archived', updated_at = CURRENT_TIMESTAMP
        WHERE report_id = ?
    """
    execute_update(update_sql, (report_id,))

    return {"message": "报表已取消发布"}


@router.get("/types/options")
async def get_report_type_options(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取报表类型选项"""
    return [
        {"value": "chart", "label": "图表"},
        {"value": "table", "label": "表格"},
        {"value": "kpi", "label": "KPI 指标"},
        {"value": "dashboard", "label": "仪表板"}
    ]
