"""
报表编辑器 API
提供报表的设计、保存、预览等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import uuid
from datetime import datetime

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/report-designer", tags=["后台管理 - 报表编辑器"])

security = HTTPBearer()


# ===========================================
# 请求/响应模型
# ===========================================

class ReportCreateRequest(BaseModel):
    """创建报表请求"""
    name: str
    description: Optional[str] = None
    widgets: List[Dict[str, Any]]
    layout: Optional[Dict[str, Any]] = None


class ReportUpdateRequest(BaseModel):
    """更新报表请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    layout: Optional[Dict[str, Any]] = None


class WidgetConfigRequest(BaseModel):
    """组件配置请求"""
    widget_id: str
    config: Dict[str, Any]


class ReportPreviewRequest(BaseModel):
    """报表预览请求"""
    widgets: List[Dict[str, Any]]
    filters: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """报表响应"""
    report_id: int
    name: str
    description: Optional[str]
    widgets: List[Dict[str, Any]]
    layout: Optional[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str]


class ReportListResponse(BaseModel):
    """报表列表响应"""
    items: List[ReportResponse]
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


def validate_widget_config(widget_type: str, config: Dict[str, Any]) -> bool:
    """验证组件配置的有效性"""
    required_fields = {
        'bar': ['dimension_field', 'measure_field'],
        'line': ['dimension_field', 'measure_field'],
        'pie': ['dimension_field', 'measure_field'],
        'table': ['columns'],
        'area': ['dimension_field', 'measure_field']
    }

    if widget_type not in required_fields:
        return False

    required = required_fields[widget_type]
    for field in required:
        if field not in config or not config[field]:
            return False

    return True


def get_mock_data(widget_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """获取模拟数据用于预览"""
    widget_type = widget_config.get('type', 'bar')
    dimension_field = widget_config.get('dimension_field', 'name')
    measure_field = widget_config.get('measure_field', 'value')

    # 根据不同的组件类型返回不同的模拟数据
    if widget_type in ['bar', 'line', 'area']:
        return [
            {dimension_field: '项目A', measure_field: 1200},
            {dimension_field: '项目B', measure_field: 900},
            {dimension_field: '项目C', measure_field: 750},
            {dimension_field: '项目D', measure_field: 600},
            {dimension_field: '项目E', measure_field: 450}
        ]
    elif widget_type == 'pie':
        return [
            {dimension_field: '类别A', measure_field: 35},
            {dimension_field: '类别B', measure_field: 25},
            {dimension_field: '类别C', measure_field: 20},
            {dimension_field: '类别D', measure_field: 15},
            {dimension_field: '其他', measure_field: 5}
        ]
    elif widget_type == 'table':
        return [
            {'id': 1, 'name': '产品A', 'category': '电子', 'price': 1200, 'sales': 150},
            {'id': 2, 'name': '产品B', 'category': '服装', 'price': 300, 'sales': 200},
            {'id': 3, 'name': '产品C', 'category': '食品', 'price': 50, 'sales': 500},
            {'id': 4, 'name': '产品D', 'category': '电子', 'price': 800, 'sales': 100},
            {'id': 5, 'name': '产品E', 'category': '图书', 'price': 80, 'sales': 300}
        ]

    # 默认返回柱状图数据
    return [
        {dimension_field: '项目A', measure_field: 1200},
        {dimension_field: '项目B', measure_field: 900},
        {dimension_field: '项目C', measure_field: 750}
    ]


# ===========================================
# API 接口
# ===========================================

@router.get("/reports", response_model=ReportListResponse)
async def get_reports(
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取报表列表"""
    where_clauses = []
    params = []

    if search:
        where_clauses.append("name LIKE ? OR description LIKE ?")
        params.extend([f"%{search}%", f"%{search}%"])

    where_clause = " AND ".join(where_clauses)
    if where_clause:
        where_clause = f"WHERE {where_clause}"

    # 查询总数
    count_sql = f"SELECT COUNT(*) as total FROM report_designs {where_clause}"
    count_result = execute_query(count_sql, tuple(params))
    total = count_result[0]["total"] if count_result else 0

    # 查询报表列表
    offset = (page - 1) * page_size
    reports_sql = f"""
        SELECT * FROM report_designs
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    reports = execute_query(reports_sql, tuple(params + [page_size, offset]))

    items = []
    for rpt in reports:
        items.append(ReportResponse(
            report_id=rpt["report_id"],
            name=rpt["name"],
            description=rpt.get("description"),
            widgets=json.loads(rpt["widgets"]) if rpt.get("widgets") else [],
            layout=json.loads(rpt["layout"]) if rpt.get("layout") else {},
            created_at=str(rpt["created_at"])[:19] if rpt.get("created_at") else "",
            updated_at=str(rpt["updated_at"])[:19] if rpt.get("updated_at") else ""
        ))

    return ReportListResponse(items=items, total=total)


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建报表"""
    # 检查报表名称是否已存在
    check_sql = "SELECT report_id FROM report_designs WHERE name = ?"
    existing = execute_query(check_sql, (request.name,))
    if existing:
        raise HTTPException(status_code=400, detail="报表名称已存在")

    # 验证组件配置（简单验证）
    for widget in request.widgets:
        if not validate_widget_config(widget.get('type', ''), widget.get('config', {})):
            raise HTTPException(status_code=400, detail=f"组件 {widget.get('id', '')} 配置无效")

    # 插入报表
    insert_sql = """
        INSERT INTO report_designs (name, description, widgets, layout)
        VALUES (?, ?, ?, ?)
    """
    execute_update(insert_sql, (
        request.name,
        request.description,
        json.dumps(request.widgets),
        json.dumps(request.layout) if request.layout else '{}'
    ))

    # 获取新创建的报表
    report = execute_query("SELECT * FROM report_designs WHERE name = ? ORDER BY created_at DESC LIMIT 1", (request.name,))
    rpt = report[0]

    return ReportResponse(
        report_id=rpt["report_id"],
        name=rpt["name"],
        description=rpt.get("description"),
        widgets=json.loads(rpt["widgets"]) if rpt.get("widgets") else [],
        layout=json.loads(rpt["layout"]) if rpt.get("layout") else {},
        created_at=str(rpt["created_at"])[:19] if rpt.get("created_at") else "",
        updated_at=str(rpt["updated_at"])[:19] if rpt.get("updated_at") else ""
    )


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取报表详情"""
    report = execute_query("SELECT * FROM report_designs WHERE report_id = ?", (report_id,))
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")

    rpt = report[0]
    return ReportResponse(
        report_id=rpt["report_id"],
        name=rpt["name"],
        description=rpt.get("description"),
        widgets=json.loads(rpt["widgets"]) if rpt.get("widgets") else [],
        layout=json.loads(rpt["layout"]) if rpt.get("layout") else {},
        created_at=str(rpt["created_at"])[:19] if rpt.get("created_at") else "",
        updated_at=str(rpt["updated_at"])[:19] if rpt.get("updated_at") else ""
    )


@router.put("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    request: ReportUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新报表"""
    # 检查报表是否存在
    report = execute_query("SELECT * FROM report_designs WHERE report_id = ?", (report_id,))
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 准备更新字段
    update_fields = []
    params = []

    if request.name is not None:
        # 检查新名称是否与其他报表冲突
        check_sql = "SELECT report_id FROM report_designs WHERE name = ? AND report_id != ?"
        existing = execute_query(check_sql, (request.name, report_id))
        if existing:
            raise HTTPException(status_code=400, detail="报表名称已存在")
        update_fields.append("name = ?")
        params.append(request.name)

    if request.description is not None:
        update_fields.append("description = ?")
        params.append(request.description)

    if request.widgets is not None:
        # 验证组件配置
        for widget in request.widgets:
            if not validate_widget_config(widget.get('type', ''), widget.get('config', {})):
                raise HTTPException(status_code=400, detail=f"组件 {widget.get('id', '')} 配置无效")
        update_fields.append("widgets = ?")
        params.append(json.dumps(request.widgets))

    if request.layout is not None:
        update_fields.append("layout = ?")
        params.append(json.dumps(request.layout))

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(report_id)

        update_sql = f"""
            UPDATE report_designs
            SET {", ".join(update_fields)}
            WHERE report_id = ?
        """
        execute_update(update_sql, tuple(params))

    # 返回更新后的报表
    report = execute_query("SELECT * FROM report_designs WHERE report_id = ?", (report_id,))
    rpt = report[0]

    return ReportResponse(
        report_id=rpt["report_id"],
        name=rpt["name"],
        description=rpt.get("description"),
        widgets=json.loads(rpt["widgets"]) if rpt.get("widgets") else [],
        layout=json.loads(rpt["layout"]) if rpt.get("layout") else {},
        created_at=str(rpt["created_at"])[:19] if rpt.get("created_at") else "",
        updated_at=str(rpt["updated_at"])[:19] if rpt.get("updated_at") else ""
    )


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除报表"""
    # 检查报表是否存在
    report = execute_query("SELECT * FROM report_designs WHERE report_id = ?", (report_id,))
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 删除报表
    delete_sql = "DELETE FROM report_designs WHERE report_id = ?"
    execute_update(delete_sql, (report_id,))

    return {"message": "报表删除成功"}


@router.post("/reports/{report_id}/preview")
async def preview_report(
    report_id: int,
    request: ReportPreviewRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """预览报表"""
    # 检查报表是否存在
    report = execute_query("SELECT * FROM report_designs WHERE report_id = ?", (report_id,))
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 为每个组件生成预览数据
    preview_data = []
    for widget in request.widgets:
        widget_data = {
            "widget_id": widget.get("id", ""),
            "type": widget.get("type", ""),
            "title": widget.get("title", ""),
            "data": get_mock_data(widget)
        }
        preview_data.append(widget_data)

    return {
        "report_id": report_id,
        "preview_data": preview_data,
        "filters": request.filters or {}
    }


@router.post("/reports/{report_id}/publish")
async def publish_report(
    report_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """发布报表（使其对用户可见）"""
    # 检查报表是否存在
    report = execute_query("SELECT * FROM report_designs WHERE report_id = ?", (report_id,))
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 更新发布状态
    update_sql = """
        UPDATE report_designs
        SET is_published = 1, published_at = CURRENT_TIMESTAMP
        WHERE report_id = ?
    """
    execute_update(update_sql, (report_id,))

    return {"message": "报表发布成功"}


@router.get("/reports/{report_id}/widgets/{widget_id}/data")
async def get_widget_data(
    report_id: int,
    widget_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取组件数据"""
    # 检查报表是否存在
    report = execute_query("SELECT * FROM report_designs WHERE report_id = ?", (report_id,))
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 查找指定组件
    widgets = json.loads(report[0]["widgets"]) if report[0].get("widgets") else []
    widget = None
    for w in widgets:
        if w.get("id") == widget_id:
            widget = w
            break

    if not widget:
        raise HTTPException(status_code=404, detail="组件不存在")

    # 返回组件数据
    return {
        "widget_id": widget_id,
        "data": get_mock_data(widget),
        "config": widget.get("config", {}),
        "options": widget.get("options", {})
    }