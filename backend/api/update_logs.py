"""
系统更新日志 API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import json

from utils.database import execute_query, execute_update
from core.security import get_current_user

router = APIRouter(prefix="/api/admin/update-logs", tags=["系统更新日志"])


@router.get("")
async def get_update_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取更新日志列表"""
    try:
        offset = (page - 1) * page_size
        
        conditions = []
        params = []
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        if keyword:
            conditions.append("(title LIKE ? OR description LIKE ? OR content LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        count_sql = f"SELECT COUNT(*) as total FROM system_update_logs{where_clause}"
        total_result = execute_query(count_sql, params)
        total = total_result[0]["total"] if total_result else 0
        
        sql = f"""
            SELECT id, version, title, description, content, category, 
                   operator, files_changed, created_at, updated_at
            FROM system_update_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        rows = execute_query(sql, params + [page_size, offset])
        
        items = []
        for row in rows:
            items.append({
                "id": row["id"],
                "version": row["version"],
                "title": row["title"],
                "description": row["description"],
                "content": row["content"],
                "category": row["category"],
                "operator": row["operator"],
                "files_changed": json.loads(row["files_changed"]) if row["files_changed"] else [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{log_id}")
async def get_update_log(log_id: int, current_user: dict = Depends(get_current_user)):
    """获取单条更新日志详情"""
    sql = "SELECT * FROM system_update_logs WHERE id = ?"
    rows = execute_query(sql, (log_id,))
    
    if not rows:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    row = rows[0]
    return {
        "id": row["id"],
        "version": row["version"],
        "title": row["title"],
        "description": row["description"],
        "content": row["content"],
        "category": row["category"],
        "operator": row["operator"],
        "files_changed": json.loads(row["files_changed"]) if row["files_changed"] else [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


@router.post("")
async def create_update_log(log_data: dict, current_user: dict = Depends(get_current_user)):
    """创建更新日志"""
    required = ["version", "title", "content", "category"]
    for field in required:
        if field not in log_data:
            raise HTTPException(status_code=400, detail=f"缺少必填字段：{field}")
    
    files_changed = json.dumps(log_data.get("files_changed", []), ensure_ascii=False)
    operator = current_user.get("user_id", "system")
    
    sql = """INSERT INTO system_update_logs 
        (version, title, description, content, category, operator, files_changed)
        VALUES (?, ?, ?, ?, ?, ?, ?)"""
    
    execute_update(sql, (
        log_data["version"], log_data["title"], log_data.get("description", ""),
        log_data["content"], log_data["category"], operator, files_changed
    ))
    
    return {"success": True, "message": "创建成功"}


@router.delete("/{log_id}")
async def delete_update_log(log_id: int, current_user: dict = Depends(get_current_user)):
    """删除更新日志"""
    sql = "DELETE FROM system_update_logs WHERE id = ?"
    execute_update(sql, (log_id,))
    return {"success": True, "message": "删除成功"}


@router.get("/stats/category")
async def get_category_stats(current_user: dict = Depends(get_current_user)):
    """获取分类统计"""
    sql = "SELECT category, COUNT(*) as count FROM system_update_logs GROUP BY category"
    rows = execute_query(sql)
    
    return {
        "total": sum(row["count"] for row in rows),
        "by_category": {row["category"]: row["count"] for row in rows}
    }
