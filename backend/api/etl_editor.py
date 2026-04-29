"""
ETL 编辑器 API
提供 ETL 工作流的设计、保存、执行等功能
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

router = APIRouter(prefix="/api/admin/etl-editor", tags=["后台管理 - ETL 编辑器"])

security = HTTPBearer()


# ===========================================
# 请求/响应模型
# ===========================================

class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    name: str
    description: Optional[str] = None
    layer: str
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]


class WorkflowUpdateRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    layer: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    connections: Optional[List[Dict[str, Any]]] = None


class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    workflow_id: int
    variables: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: int
    name: str
    description: Optional[str]
    layer: str
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str]


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    items: List[WorkflowResponse]
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


def validate_workflow_data(nodes: List[Dict], connections: List[Dict]) -> bool:
    """验证工作流数据的有效性"""
    # 检查节点ID唯一性
    node_ids = [node.get('id') for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        return False

    # 检查连接的有效性
    for conn in connections:
        if conn.get('from') not in node_ids or conn.get('to') not in node_ids:
            return False

    return True


# ===========================================
# API 接口
# ===========================================

@router.get("/workflows", response_model=WorkflowListResponse)
async def get_workflows(
    layer: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取工作流列表"""
    where_clauses = []
    params = []

    if layer:
        where_clauses.append("layer = ?")
        params.append(layer)

    if search:
        where_clauses.append("name LIKE ?")
        params.append(f"%{search}%")

    where_clause = " AND ".join(where_clauses)
    if where_clause:
        where_clause = f"WHERE {where_clause}"

    # 查询总数
    count_sql = f"SELECT COUNT(*) as total FROM etl_workflows {where_clause}"
    count_result = execute_query(count_sql, tuple(params))
    total = count_result[0]["total"] if count_result else 0

    # 查询工作流列表
    offset = (page - 1) * page_size
    workflows_sql = f"""
        SELECT * FROM etl_workflows
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    workflows = execute_query(workflows_sql, tuple(params + [page_size, offset]))

    items = []
    for wf in workflows:
        items.append(WorkflowResponse(
            workflow_id=wf["workflow_id"],
            name=wf["name"],
            description=wf.get("description"),
            layer=wf["layer"],
            nodes=json.loads(wf["nodes"]) if wf.get("nodes") else [],
            connections=json.loads(wf["connections"]) if wf.get("connections") else [],
            created_at=str(wf["created_at"])[:19] if wf.get("created_at") else "",
            updated_at=str(wf["updated_at"])[:19] if wf.get("updated_at") else ""
        ))

    return WorkflowListResponse(items=items, total=total)


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建工作流"""
    # 验证工作流数据
    if not validate_workflow_data(request.nodes, request.connections):
        raise HTTPException(status_code=400, detail="工作流数据无效")

    # 检查同名工作流是否已存在
    check_sql = "SELECT workflow_id FROM etl_workflows WHERE name = ?"
    existing = execute_query(check_sql, (request.name,))
    if existing:
        raise HTTPException(status_code=400, detail="工作流名称已存在")

    # 插入工作流
    insert_sql = """
        INSERT INTO etl_workflows (name, description, layer, nodes, connections)
        VALUES (?, ?, ?, ?, ?)
    """
    execute_update(insert_sql, (
        request.name,
        request.description,
        request.layer,
        json.dumps(request.nodes),
        json.dumps(request.connections)
    ))

    # 获取新创建的工作流
    workflow = execute_query("SELECT * FROM etl_workflows WHERE name = ? ORDER BY created_at DESC LIMIT 1", (request.name,))
    wf = workflow[0]

    return WorkflowResponse(
        workflow_id=wf["workflow_id"],
        name=wf["name"],
        description=wf.get("description"),
        layer=wf["layer"],
        nodes=json.loads(wf["nodes"]) if wf.get("nodes") else [],
        connections=json.loads(wf["connections"]) if wf.get("connections") else [],
        created_at=str(wf["created_at"])[:19] if wf.get("created_at") else "",
        updated_at=str(wf["updated_at"])[:19] if wf.get("updated_at") else ""
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取工作流详情"""
    workflow = execute_query("SELECT * FROM etl_workflows WHERE workflow_id = ?", (workflow_id,))
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    wf = workflow[0]
    return WorkflowResponse(
        workflow_id=wf["workflow_id"],
        name=wf["name"],
        description=wf.get("description"),
        layer=wf["layer"],
        nodes=json.loads(wf["nodes"]) if wf.get("nodes") else [],
        connections=json.loads(wf["connections"]) if wf.get("connections") else [],
        created_at=str(wf["created_at"])[:19] if wf.get("created_at") else "",
        updated_at=str(wf["updated_at"])[:19] if wf.get("updated_at") else ""
    )


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    request: WorkflowUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新工作流"""
    # 检查工作流是否存在
    workflow = execute_query("SELECT * FROM etl_workflows WHERE workflow_id = ?", (workflow_id,))
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 准备更新字段
    update_fields = []
    params = []

    if request.name is not None:
        # 检查新名称是否与其他工作流冲突
        check_sql = "SELECT workflow_id FROM etl_workflows WHERE name = ? AND workflow_id != ?"
        existing = execute_query(check_sql, (request.name, workflow_id))
        if existing:
            raise HTTPException(status_code=400, detail="工作流名称已存在")
        update_fields.append("name = ?")
        params.append(request.name)

    if request.description is not None:
        update_fields.append("description = ?")
        params.append(request.description)

    if request.layer is not None:
        update_fields.append("layer = ?")
        params.append(request.layer)

    if request.nodes is not None:
        # 验证节点数据
        connections = json.loads(workflow[0]["connections"]) if workflow[0].get("connections") else []
        if not validate_workflow_data(request.nodes, connections):
            raise HTTPException(status_code=400, detail="工作流节点数据无效")
        update_fields.append("nodes = ?")
        params.append(json.dumps(request.nodes))

    if request.connections is not None:
        # 验证连接数据
        nodes = json.loads(workflow[0]["nodes"]) if workflow[0].get("nodes") else []
        if not validate_workflow_data(nodes, request.connections):
            raise HTTPException(status_code=400, detail="工作流连接数据无效")
        update_fields.append("connections = ?")
        params.append(json.dumps(request.connections))

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(workflow_id)

        update_sql = f"""
            UPDATE etl_workflows
            SET {", ".join(update_fields)}
            WHERE workflow_id = ?
        """
        execute_update(update_sql, tuple(params))

    # 返回更新后的工作流
    workflow = execute_query("SELECT * FROM etl_workflows WHERE workflow_id = ?", (workflow_id,))
    wf = workflow[0]

    return WorkflowResponse(
        workflow_id=wf["workflow_id"],
        name=wf["name"],
        description=wf.get("description"),
        layer=wf["layer"],
        nodes=json.loads(wf["nodes"]) if wf.get("nodes") else [],
        connections=json.loads(wf["connections"]) if wf.get("connections") else [],
        created_at=str(wf["created_at"])[:19] if wf.get("created_at") else "",
        updated_at=str(wf["updated_at"])[:19] if wf.get("updated_at") else ""
    )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除工作流"""
    # 检查工作流是否存在
    workflow = execute_query("SELECT * FROM etl_workflows WHERE workflow_id = ?", (workflow_id,))
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 删除工作流
    delete_sql = "DELETE FROM etl_workflows WHERE workflow_id = ?"
    execute_update(delete_sql, (workflow_id,))

    return {"message": "工作流删除成功"}


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    request: WorkflowExecuteRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """执行工作流"""
    # 检查工作流是否存在
    workflow = execute_query("SELECT * FROM etl_workflows WHERE workflow_id = ?", (workflow_id,))
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 这里是模拟执行工作流的过程
    # 实际实现中，这里会解析工作流定义并执行相应的ETL任务

    # 创建执行记录
    execution_id = str(uuid.uuid4())
    start_time = datetime.now()

    insert_sql = """
        INSERT INTO etl_executions (execution_id, workflow_id, status, start_time, variables)
        VALUES (?, ?, 'running', ?, ?)
    """
    execute_update(insert_sql, (
        execution_id,
        workflow_id,
        start_time,
        json.dumps(request.variables) if request.variables else None
    ))

    # 模拟执行过程（实际实现中会根据工作流定义执行具体的ETL任务）
    import time
    time.sleep(2)  # 模拟执行时间

    end_time = datetime.now()
    duration = int((end_time - start_time).total_seconds())

    # 更新执行状态
    update_sql = """
        UPDATE etl_executions
        SET status = 'success', end_time = ?, duration_seconds = ?
        WHERE execution_id = ?
    """
    execute_update(update_sql, (end_time, duration, execution_id))

    return {
        "message": "工作流执行成功",
        "execution_id": execution_id,
        "duration": duration
    }


@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取工作流执行记录"""
    offset = (page - 1) * page_size

    # 查询总数
    count_sql = "SELECT COUNT(*) as total FROM etl_executions WHERE workflow_id = ?"
    count_result = execute_query(count_sql, (workflow_id,))
    total = count_result[0]["total"] if count_result else 0

    # 查询执行记录
    executions_sql = """
        SELECT * FROM etl_executions
        WHERE workflow_id = ?
        ORDER BY start_time DESC
        LIMIT ? OFFSET ?
    """
    executions = execute_query(executions_sql, (workflow_id, page_size, offset))

    items = []
    for exec_record in executions:
        items.append({
            "execution_id": exec_record["execution_id"],
            "workflow_id": exec_record["workflow_id"],
            "status": exec_record["status"],
            "start_time": str(exec_record["start_time"])[:19] if exec_record.get("start_time") else "",
            "end_time": str(exec_record["end_time"])[:19] if exec_record.get("end_time") else "",
            "duration_seconds": exec_record.get("duration_seconds"),
            "variables": json.loads(exec_record["variables"]) if exec_record.get("variables") else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }