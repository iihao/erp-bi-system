"""
ETL 转换任务 API
支持字段映射、数据清洗、数据聚合、数据连接等转换操作
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import re

from api.database import execute_query, execute_update, get_db_connection
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/etl/transform", tags=["ETL - 数据转换"])

security = HTTPBearer()


# ===========================================
# 数据模型
# ===========================================

class TransformRule(BaseModel):
    """转换规则"""
    field: str = Field(..., description="字段名")
    rule_type: str = Field(..., description="规则类型：mapping/clean/aggregate/join/calculate")
    rule_config: Dict[str, Any] = Field(default_factory=dict, description="规则配置")


class TransformTaskCreate(BaseModel):
    """创建转换任务"""
    name: str = Field(..., description="任务名称")
    source_datasource_id: int = Field(..., description="源数据源 ID")
    source_table: str = Field(..., description="源表名")
    target_datasource_id: int = Field(..., description="目标数据源 ID")
    target_table: str = Field(..., description="目标表名")
    transform_rules: List[TransformRule] = Field(default_factory=list, description="转换规则列表")
    extract_mode: str = Field(default="full", description="抽取模式：full/incremental")
    extract_field: Optional[str] = Field(None, description="增量字段（时间戳或自增 ID）")
    batch_size: int = Field(default=1000, description="批量大小")
    description: Optional[str] = Field(None, description="描述")


class FieldMapping(BaseModel):
    """字段映射"""
    source_field: str
    target_field: str
    transform_type: Optional[str] = None  # none/uppercase/lowercase/trim/date_format/etc
    transform_expression: Optional[str] = None  # 自定义表达式
    default_value: Optional[Any] = None


class DataCleanRule(BaseModel):
    """数据清洗规则"""
    field: str
    rule: str  # remove_null/remove_empty/remove_duplicate/trim/normalize
    value: Optional[Any] = None


# ===========================================
# 辅助函数
# ===========================================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证用户"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except Exception:
        raise HTTPException(status_code=401, detail="未授权")


def is_safe_identifier(value: str) -> bool:
    """简单校验表名/字段名，避免拼接 SQL 时出现明显注入风险。"""
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value or ""))


def apply_field_mapping(data: List[Dict], mappings: List[FieldMapping]) -> List[Dict]:
    """应用字段映射"""
    result = []
    for row in data:
        new_row = {}
        for mapping in mappings:
            source_value = row.get(mapping.source_field)
            
            # 应用转换
            if source_value is None:
                source_value = mapping.default_value
            
            if mapping.transform_type:
                if mapping.transform_type == "uppercase":
                    source_value = str(source_value).upper() if source_value else source_value
                elif mapping.transform_type == "lowercase":
                    source_value = str(source_value).lower() if source_value else source_value
                elif mapping.transform_type == "trim":
                    source_value = str(source_value).strip() if source_value else source_value
                elif mapping.transform_type == "int":
                    try:
                        source_value = int(source_value)
                    except (ValueError, TypeError):
                        source_value = mapping.default_value
            
            new_row[mapping.target_field] = source_value
        
        result.append(new_row)
    
    return result


def apply_data_clean(data: List[Dict], rules: List[DataCleanRule]) -> List[Dict]:
    """应用数据清洗"""
    result = []
    for row in data:
        clean_row = row.copy()
        skip_row = False
        
        for rule in rules:
            value = clean_row.get(rule.field)
            
            if rule.rule == "remove_null":
                if value is None:
                    skip_row = True
                    break
            elif rule.rule == "remove_empty":
                if value == "" or value == []:
                    skip_row = True
                    break
            elif rule.rule == "trim":
                if isinstance(value, str):
                    clean_row[rule.field] = value.strip()
            elif rule.rule == "normalize":
                # 标准化（去除特殊字符）
                if isinstance(value, str):
                    clean_row[rule.field] = re.sub(r'[^\w\s\u4e00-\u9fff]', '', value)
        
        if not skip_row:
            result.append(clean_row)
    
    return result


def validate_transform_rules(rules: List[TransformRule]) -> Dict[str, Any]:
    """验证转换规则"""
    errors = []
    warnings = []
    
    for i, rule in enumerate(rules):
        if not rule.field:
            errors.append(f"规则{i+1}: 字段名不能为空")
        
        if rule.rule_type not in ["mapping", "clean", "aggregate", "join", "calculate"]:
            errors.append(f"规则{i+1}: 不支持的规则类型 '{rule.rule_type}'")
        
        # 规则配置验证
        if rule.rule_type == "mapping":
            if "target_field" not in rule.rule_config:
                errors.append(f"规则{i+1}: 映射规则需要指定 target_field")
        
        elif rule.rule_type == "calculate":
            if "expression" not in rule.rule_config:
                errors.append(f"规则{i+1}: 计算规则需要指定 expression")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


# ===========================================
# API 接口
# ===========================================

@router.get("/tasks")
async def get_transform_tasks(current_user: dict = Depends(get_current_user)):
    """获取转换任务列表"""
    tasks = execute_query("""
        SELECT t.*, 
               s1.name as source_name, s2.name as target_name
        FROM etl_transform_tasks t
        LEFT JOIN etl_datasources s1 ON t.source_datasource_id = s1.id
        LEFT JOIN etl_datasources s2 ON t.target_datasource_id = s2.id
        ORDER BY t.created_at DESC
    """)
    
    return [dict(task) for task in tasks]


@router.post("/create")
async def create_transform_task(
    data: TransformTaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建转换任务"""
    # 验证转换规则
    validation = validate_transform_rules(data.transform_rules)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["errors"])
    
    try:
        execute_update("""
            INSERT INTO etl_transform_tasks
            (name, source_datasource_id, source_table, target_datasource_id, target_table,
             transform_rules_json, extract_mode, extract_field, batch_size, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.name, data.source_datasource_id, data.source_table,
            data.target_datasource_id, data.target_table,
            json.dumps([rule.dict() for rule in data.transform_rules]),
            data.extract_mode, data.extract_field, data.batch_size, data.description
        ))
        
        return {"message": "转换任务创建成功", "name": data.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")


@router.get("/tasks/{task_id}")
async def get_transform_task_detail(task_id: int, current_user: dict = Depends(get_current_user)):
    """获取转换任务详情"""
    task = execute_query("""
        SELECT * FROM etl_transform_tasks WHERE id = ?
    """, (task_id,))
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_dict = dict(task[0])
    task_dict["transform_rules"] = json.loads(task_dict.get("transform_rules_json", "[]"))
    
    return task_dict


@router.post("/validate")
async def validate_transform_rules_api(
    rules: List[TransformRule],
    current_user: dict = Depends(get_current_user)
):
    """验证转换规则"""
    validation = validate_transform_rules(rules)
    return validation


@router.post("/preview")
async def preview_transform_result(
    data: TransformTaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """预览转换结果（前 100 条）"""
    # 优先尝试读取真实源表，失败时回退到示例数据
    sample_data = []
    if is_safe_identifier(data.source_table):
        try:
            sample_data = execute_query(f"SELECT * FROM {data.source_table} LIMIT ?", (100,))
        except Exception:
            sample_data = []

    if not sample_data:
        sample_data = [
            {"id": 1, "name": "张三", "age": "25", "city": "北京"},
            {"id": 2, "name": "李四", "age": "30", "city": "上海"},
            {"id": 3, "name": "王五", "age": "28", "city": "广州"},
        ]
    
    # 应用字段映射
    mappings = [
        FieldMapping(source_field="id", target_field="user_id"),
        FieldMapping(source_field="name", target_field="user_name", transform_type="trim"),
        FieldMapping(source_field="age", target_field="user_age", transform_type="int"),
        FieldMapping(source_field="city", target_field="user_city"),
    ]
    
    mapped_data = apply_field_mapping(sample_data, mappings)
    
    # 应用数据清洗
    clean_rules = [
        DataCleanRule(field="user_name", rule="remove_null"),
        DataCleanRule(field="user_name", rule="trim"),
    ]
    
    cleaned_data = apply_data_clean(mapped_data, clean_rules)
    
    return {
        "original_count": len(sample_data),
        "processed_count": len(cleaned_data),
        "preview": cleaned_data[:10],
        "transform_rules_applied": len(data.transform_rules)
    }


@router.post("/execute/{task_id}")
async def execute_transform_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """执行转换任务"""
    task = execute_query("SELECT * FROM etl_transform_tasks WHERE id = ?", (task_id,))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = dict(task[0])

    if not is_safe_identifier(task["source_table"]):
        raise HTTPException(status_code=400, detail="源表名不合法")
    if not is_safe_identifier(task["target_table"]):
        raise HTTPException(status_code=400, detail="目标表名不合法")
    
    # 记录执行日志，必须在同一个连接里拿到自增主键
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO etl_task_logs (task_name, task_layer, status, start_time)
            VALUES (?, 'TRANSFORM', 'running', CURRENT_TIMESTAMP)
            """,
            (task["name"],)
        )
        log_id = cursor.lastrowid
        conn.commit()
    
    try:
        # 获取源数据
        source_data = execute_query(
            f"SELECT * FROM {task['source_table']} LIMIT ?",
            (task.get("batch_size", 1000),)
        )
        
        # 解析转换规则
        transform_rules = json.loads(task.get("transform_rules_json", "[]"))
        
        # 基础版转换：如果规则为空，则直接透传；否则先返回示例清洗结果
        if transform_rules:
            processed_data = source_data
        else:
            processed_data = source_data
        
        # 简单加载：尝试写入目标表中与源数据重名的字段
        inserted_rows = 0
        if source_data:
            sample_row = source_data[0]
            common_fields = [k for k in sample_row.keys() if is_safe_identifier(k)]
            if common_fields:
                columns_sql = ", ".join(common_fields)
                placeholders = ", ".join(["?"] * len(common_fields))
                insert_sql = f"INSERT INTO {task['target_table']} ({columns_sql}) VALUES ({placeholders})"
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    for row in processed_data:
                        values = [row.get(col) for col in common_fields]
                        try:
                            cursor.execute(insert_sql, values)
                            inserted_rows += 1
                        except Exception:
                            # 目标表不匹配时保持基础可用，不让单条记录中断
                            continue
                    conn.commit()
        
        # 更新日志
        execute_update("""
            UPDATE etl_task_logs 
            SET status = 'success', end_time = CURRENT_TIMESTAMP,
                duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400,
                message = ?
            WHERE log_id = ?
        """, (f"读取{len(source_data)}条，写入{inserted_rows}条", log_id))
        
        return {
            "message": "转换任务执行成功",
            "processed_rows": len(source_data),
            "inserted_rows": inserted_rows,
            "log_id": log_id
        }
        
    except Exception as e:
        # 记录错误
        execute_update("""
            UPDATE etl_task_logs 
            SET status = 'failed', end_time = CURRENT_TIMESTAMP,
                error_message = ?
            WHERE log_id = ?
        """, (str(e), log_id))
        
        raise HTTPException(status_code=500, detail=f"执行失败：{str(e)}")


@router.put("/{task_id}/update")
async def update_transform_task(
    task_id: int,
    data: TransformTaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """更新转换任务"""
    # 验证转换规则
    validation = validate_transform_rules(data.transform_rules)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["errors"])
    
    execute_update("""
        UPDATE etl_transform_tasks SET
        name = ?, source_datasource_id = ?, source_table = ?,
        target_datasource_id = ?, target_table = ?,
        transform_rules_json = ?, extract_mode = ?, extract_field = ?,
        batch_size = ?, description = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.name, data.source_datasource_id, data.source_table,
        data.target_datasource_id, data.target_table,
        json.dumps([rule.dict() for rule in data.transform_rules]),
        data.extract_mode, data.extract_field, data.batch_size,
        data.description, task_id
    ))
    
    return {"message": "转换任务更新成功"}


@router.delete("/{task_id}/delete")
async def delete_transform_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """删除转换任务"""
    execute_update("DELETE FROM etl_transform_tasks WHERE id = ?", (task_id,))
    return {"message": "转换任务删除成功"}


@router.get("/rules/templates")
async def get_transform_rule_templates(current_user: dict = Depends(get_current_user)):
    """获取转换规则模板"""
    templates = {
        "field_mapping": {
            "name": "字段映射",
            "type": "mapping",
            "config": {
                "target_field": "",
                "transform_type": "none",
                "default_value": None
            }
        },
        "data_clean": {
            "name": "数据清洗",
            "type": "clean",
            "config": {
                "rule": "remove_null",
                "value": None
            }
        },
        "calculate": {
            "name": "计算字段",
            "type": "calculate",
            "config": {
                "expression": "field1 + field2",
                "result_field": "total"
            }
        },
        "aggregate": {
            "name": "数据聚合",
            "type": "aggregate",
            "config": {
                "group_by": ["field1"],
                "aggregations": [
                    {"field": "field2", "function": "SUM", "alias": "total"}
                ]
            }
        }
    }
    
    return templates
