"""
AI 配置管理 API
提供 AI 模型配置、Prompt 模板、表结构映射、权限配置等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/ai-config", tags=["后台管理 - AI 配置"])

security = HTTPBearer()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
REAL_ESTATE_SCHEMA_FILE = os.path.join(BASE_DIR, "db", "init_real_estate_tables.sql")
WAREHOUSE_SCHEMA_FILE = os.path.join(BASE_DIR, "db", "init_warehouse_tables.sql")


def _default_available_models() -> Dict[str, Any]:
    return {
        "qwen3.6-plus": {
            "name": "Qwen3.6 Plus",
            "input": ["text", "image"],
            "modes": ["text", "deep", "vision"],
            "context": 1000000,
            "description": "通用文本生成、深度思考和视觉理解，适合 AI 问数与图表解读"
        },
        "qwen3.5-plus": {
            "name": "Qwen3.5 Plus",
            "input": ["text", "image"],
            "modes": ["text", "vision"],
            "context": 1000000,
            "description": "兼容性强，适合常规问数和图像理解"
        },
        "qwen3-max-2026-01-23": {
            "name": "Qwen3 Max 2026-01-23",
            "input": ["text"],
            "modes": ["text", "deep"],
            "context": 262144,
            "description": "长上下文与复杂推理"
        }
    }


def _normalize_base_url(base_url: str) -> str:
    """将百炼接口地址统一成 OpenAI 兼容模式"""
    value = (base_url or "").strip().rstrip("/")
    if not value:
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if value.endswith("/chat/completions"):
        value = value[: -len("/chat/completions")].rstrip("/")
    if value.endswith("/api/v1"):
        return value[: -len("/api/v1")] + "/compatible-mode/v1"
    if value.endswith("/v1") and "compatible-mode" not in value:
        return value[: -len("/v1")] + "/compatible-mode/v1"
    return value


def _is_coding_plan_key(api_key: str) -> bool:
    """判断是否为 Coding Plan 专属 Key"""
    return str(api_key or "").strip().startswith("sk-sp-")


def _detect_key_type(api_key: str) -> str:
    """检测 API Key 类型"""
    key = str(api_key or "").strip()
    if not key:
        return "empty"
    if key.startswith("sk-sp-"):
        return "coding_plan"
    if key.startswith("sk-"):
        return "common"
    return "unknown"


def _key_type_label(api_key: str) -> str:
    """返回 API Key 类型标签"""
    return {
        "empty": "未配置",
        "coding_plan": "Coding Plan 专属 Key",
        "common": "通用百炼 Key",
        "unknown": "未知类型 Key"
    }.get(_detect_key_type(api_key), "未知类型 Key")


def _suggest_base_url(api_key: str) -> str:
    """返回推荐 Base URL"""
    key_type = _detect_key_type(api_key)
    if key_type == "coding_plan":
        return "https://coding.dashscope.aliyuncs.com/v1"
    return "https://dashscope.aliyuncs.com/compatible-mode/v1"


def _resolve_base_url(base_url: str, api_key: str = "") -> str:
    """根据 Key 类型和当前配置，返回可用的请求地址"""
    normalized = (base_url or "").strip().rstrip("/")
    if _is_coding_plan_key(api_key):
        if "coding.dashscope.aliyuncs.com" in normalized:
            return normalized
        if normalized.endswith("/apps/anthropic"):
            return normalized
        return _suggest_base_url(api_key)

    # 通用 Key：优先使用 OpenAI 兼容模式
    if "coding.dashscope.aliyuncs.com" in normalized:
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    return _normalize_base_url(normalized)


def _table_alias_meta(table_name: str) -> Dict[str, str]:
    alias_map = {
        "re_projects": {"alias": "项目表", "description": "地产项目基础信息"},
        "re_buildings": {"alias": "楼栋表", "description": "项目楼栋与楼座信息"},
        "re_units": {"alias": "房源表", "description": "房源、面积、价格与状态"},
        "re_customers": {"alias": "客户表", "description": "客户基础信息与来源"},
        "re_customer_followups": {"alias": "客户跟进表", "description": "客户跟进和回访记录"},
        "re_subscriptions": {"alias": "认购表", "description": "认购单与定金信息"},
        "re_contracts": {"alias": "合同表", "description": "销售合同与签约信息"},
        "re_payments": {"alias": "回款表", "description": "回款与收款记录"},
        "re_receivables": {"alias": "应收表", "description": "应收款与逾期信息"},
        "re_refunds": {"alias": "退款表", "description": "退款与退房信息"},
        "ods_room": {"alias": "ODS 房源表", "description": "房源原始明细数据"},
        "ods_trade": {"alias": "ODS 交易表", "description": "销售交易原始数据"},
        "ods_payment": {"alias": "ODS 回款表", "description": "回款原始数据"},
        "ods_pay": {"alias": "ODS 付款表", "description": "付款登记原始数据"},
        "ods_contract": {"alias": "ODS 合同表", "description": "合同原始数据"},
        "ods_account": {"alias": "ODS 科目表", "description": "科目原始数据"},
        "ods_bseg": {"alias": "ODS 凭证表", "description": "SAP 凭证明细"},
        "ods_gl_actual": {"alias": "ODS 总账实际表", "description": "总账实际业务明细"},
        "ods_other": {"alias": "ODS 其他表", "description": "Excel 填报等补充数据"},
        "dwd_room_detail": {"alias": "DWD 房源明细", "description": "标准化房源明细"},
        "dwd_trade_detail": {"alias": "DWD 交易明细", "description": "标准化销售交易明细"},
        "dwd_payment_detail": {"alias": "DWD 回款明细", "description": "标准化回款明细"},
        "dwd_contract_detail": {"alias": "DWD 合同明细", "description": "标准化合同明细"},
        "dwd_pay_detail": {"alias": "DWD 付款明细", "description": "标准化付款明细"},
        "dwd_gl_actual_detail": {"alias": "DWD 总账实际明细", "description": "标准化总账实际明细"},
        "dwd_gl_budget_detail": {"alias": "DWD 总账预算明细", "description": "标准化总账预算明细"},
        "dws_sales_payment_fact": {"alias": "DWS 销售回款事实", "description": "销售回款聚合事实表"},
        "dws_sales_cost_fact": {"alias": "DWS 销售成本事实", "description": "销售成本聚合事实表"},
        "dim_project": {"alias": "项目维度", "description": "项目主数据维表"},
        "dim_date": {"alias": "日期维度", "description": "日期、季度、周等维表"},
        "dim_account": {"alias": "科目维度", "description": "科目基础维表"},
        "dim_permission": {"alias": "权限维度", "description": "权限与菜单维表"},
        "dim_indicator": {"alias": "指标维度", "description": "指标定义与口径维表"},
        "ads_group_sales_report": {"alias": "集团销售报表", "description": "集团销售分析报表"},
        "ads_group_salesdate_report": {"alias": "集团销售日表", "description": "集团销售日粒度报表"},
        "ads_group_pay_report": {"alias": "集团付款报表", "description": "集团付款分析报表"},
        "ads_project_cost_report": {"alias": "项目成本报表", "description": "项目成本与预算分析"},
        "ads_sales_dashboard": {"alias": "销售驾驶舱", "description": "项目去化、销售、回款总览"},
        "ads_finance_dashboard": {"alias": "财务驾驶舱", "description": "财务总收入、成本、利润总览"},
        "ads_szl_dashboard": {"alias": "损益驾驶舱", "description": "损益与投资回报分析"},
    }
    return alias_map.get(table_name, {
        "alias": table_name.replace("_", " ").title(),
        "description": "自动生成的表配置"
    })


def _parse_schema_file(path: str) -> List[Dict[str, Any]]:
    import re
    schemas: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for idx, match in enumerate(re.finditer(r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)\s*\((.*?)\);", content, re.S), start=1):
            table_name = match.group(1)
            body = match.group(2)
            fields: List[Dict[str, str]] = []
            for raw_line in body.splitlines():
                line = raw_line.strip().rstrip(",")
                if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT", "INDEX ")):
                    continue
                field_match = re.match(r"([a-zA-Z0-9_]+)\s+([A-Z0-9()_,\s]+)", line, re.I)
                if field_match:
                    fields.append({
                        "name": field_match.group(1),
                        "type": field_match.group(2).split()[0].replace(",", "")
                    })
            meta = _table_alias_meta(table_name)
            schemas.append({
                "table_name": table_name,
                "table_alias": meta["alias"],
                "description": meta["description"],
                "layer": table_name.split("_", 1)[0].upper() if "_" in table_name else "CUSTOM",
                "enabled": True,
                "priority": idx * 10,
                "sample_question": "",
                "fields": fields[:12]
            })
    except Exception:
        return []
    return schemas


def build_default_table_schemas() -> List[Dict[str, Any]]:
    """构建地产相关默认表配置"""
    schemas = _parse_schema_file(REAL_ESTATE_SCHEMA_FILE) + _parse_schema_file(WAREHOUSE_SCHEMA_FILE)
    seen = set()
    unique = []
    for row in schemas:
        if row["table_name"] in seen:
            continue
        seen.add(row["table_name"])
        unique.append(row)
    return unique


def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员权限"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


# ===========================================
# 请求/响应模型
# ===========================================

class APIConfigRequest(BaseModel):
    """API 配置请求"""
    api_key: str
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-plus"
    model_mode: str = "text"


class PromptConfigRequest(BaseModel):
    """Prompt 配置请求"""
    system_prompt: str
    user_prompt: str


class PermissionConfigRequest(BaseModel):
    """权限配置请求"""
    allowed_types: List[str] = ["SELECT"]
    daily_quota: int = 100
    sensitive_words: str = ""
    sensitive_tables: List[str] = []


class TableSchemaRequest(BaseModel):
    """表结构配置请求"""
    table_name: str
    table_alias: str = ""
    description: str = ""
    layer: str = "CUSTOM"
    enabled: bool = True
    priority: int = 100
    sample_question: str = ""
    fields: List[Dict[str, str]] = []


# ===========================================
# 配置存储（实际应该存储在数据库中）
# ===========================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "ai_config.json")

def load_ai_config() -> Dict[str, Any]:
    """加载 AI 配置"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen3.6-plus",
            "model_mode": "text",
            "system_prompt": """你是一个专业的 SQL 生成助手。根据数据库表结构，将用户的自然语言问题转换为 SQL 查询。

要求：
1. 只输出 SQL 语句，不要解释
2. 使用 SQLite 兼容语法
3. 如果问题不明确，生成最合理的查询
4. 限制结果数量（使用 LIMIT）
5. 只允许 SELECT 查询""",
            "user_prompt": "请将以下问题转换为 SQL 查询：{question}",
            "daily_quota": 100,
            "sensitive_words": "DROP, DELETE, TRUNCATE, GRANT, REVOKE",
            "sensitive_tables": ["users", "roles", "permissions", "system_logs"],
            "table_schemas": build_default_table_schemas(),
            "available_models": _default_available_models()
        }


def save_ai_config(config: Dict[str, Any]):
    """保存 AI 配置"""
    import os
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ===========================================
# API 接口
# ===========================================

@router.get("/config")
async def get_full_config(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取完整 AI 配置（含 API Key）"""
    config = load_ai_config()
    api_key = config.get("api_key", "")
    return {
        "api_key": config.get("api_key", ""),
        "base_url": _resolve_base_url(config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"), api_key),
        "model": config.get("model", "qwen3.6-plus"),
        "model_mode": config.get("model_mode", "text"),
        "key_type": _detect_key_type(api_key),
        "key_type_label": _key_type_label(api_key),
        "base_url_suggested": _suggest_base_url(api_key),
        "system_prompt": config.get("system_prompt", ""),
        "user_prompt": config.get("user_prompt", ""),
        "daily_quota": config.get("daily_quota", 100),
        "sensitive_words": config.get("sensitive_words", ""),
        "sensitive_tables": config.get("sensitive_tables", []),
        "table_schemas": config.get("table_schemas", []) or build_default_table_schemas(),
        "available_models": config.get("available_models", {}) or _default_available_models()
    }


@router.get("/current")
async def get_current_config(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取当前 AI 配置（不含 API Key）"""
    config = load_ai_config()
    api_key = config.get("api_key", "")
    return {
        "api_key_configured": bool(config.get("api_key", "").startswith("sk-")),
        "base_url": _resolve_base_url(config.get("base_url", ""), api_key),
        "model": config.get("model", "qwen3.6-plus"),
        "model_mode": config.get("model_mode", "text"),
        "key_type": _detect_key_type(api_key),
        "key_type_label": _key_type_label(api_key),
        "base_url_suggested": _suggest_base_url(api_key),
        "system_prompt": config.get("system_prompt", ""),
        "user_prompt": config.get("user_prompt", ""),
        "daily_quota": config.get("daily_quota", 100),
        "sensitive_words": config.get("sensitive_words", ""),
        "sensitive_tables": config.get("sensitive_tables", []),
        "table_schemas": config.get("table_schemas", []) or build_default_table_schemas(),
        "available_models": config.get("available_models", {}) or _default_available_models()
    }


@router.post("/api")
async def save_api_config(
    request: dict,
    current_user: dict = Depends(get_current_admin_user)
):
    """保存 API 配置"""
    config = load_ai_config()
    api_key = request.get("apiKey", "")
    if api_key and "****" not in api_key:
        config["api_key"] = api_key
    config["base_url"] = _resolve_base_url(
        request.get("baseUrl", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        config.get("api_key", api_key)
    )
    config["model"] = request.get("model", "qwen3.6-plus")
    config["model_mode"] = request.get("modelMode", request.get("model_mode", config.get("model_mode", "text")))
    config["available_models"] = request.get("available_models", config.get("available_models", _default_available_models()))
    save_ai_config(config)

    # 更新环境变量
    os.environ["DASHSCOPE_API_KEY"] = config["api_key"]

    return {"message": "API 配置保存成功"}


@router.post("/prompt")
async def save_prompt_config(
    request: dict,
    current_user: dict = Depends(get_current_admin_user)
):
    """保存 Prompt 模板配置"""
    config = load_ai_config()
    config["system_prompt"] = request.get("system_prompt", "")
    config["user_prompt"] = request.get("user_prompt", "")
    save_ai_config(config)

    return {"message": "Prompt 模板保存成功"}


@router.post("/permission")
async def save_permission_config(
    request: dict,
    current_user: dict = Depends(get_current_admin_user)
):
    """保存权限配置"""
    config = load_ai_config()
    config["allowed_types"] = request.get("allowed_types", ["SELECT"])
    config["daily_quota"] = request.get("daily_quota", 100)
    config["sensitive_words"] = request.get("sensitive_words", "")
    config["sensitive_tables"] = request.get("sensitive_tables", [])
    save_ai_config(config)

    return {"message": "权限配置保存成功"}


@router.post("/schema")
async def save_table_schema(
    request: TableSchemaRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """保存表结构配置"""
    config = load_ai_config()

    # 查找是否已存在
    table_schemas = config.get("table_schemas", [])
    found = False
    for table in table_schemas:
        if table.get("table_name") == request.table_name:
            table["table_alias"] = request.table_alias
            table["description"] = request.description
            table["layer"] = request.layer
            table["enabled"] = request.enabled
            table["priority"] = request.priority
            table["sample_question"] = request.sample_question
            table["fields"] = request.fields
            found = True
            break

    if not found:
        table_schemas.append({
            "table_name": request.table_name,
            "table_alias": request.table_alias,
            "description": request.description,
            "layer": request.layer,
            "enabled": request.enabled,
            "priority": request.priority,
            "sample_question": request.sample_question,
            "fields": request.fields
        })

    config["table_schemas"] = table_schemas
    save_ai_config(config)

    return {"message": "表结构配置保存成功"}


@router.delete("/schema/{table_name}")
async def delete_table_schema(
    table_name: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除表结构配置"""
    config = load_ai_config()
    table_schemas = config.get("table_schemas", [])
    config["table_schemas"] = [t for t in table_schemas if t.get("table_name") != table_name]
    save_ai_config(config)

    return {"message": "表结构配置删除成功"}


@router.get("/test")
async def test_connection(
    current_user: dict = Depends(get_current_admin_user)
):
    """测试 API 连接"""
    import httpx

    config = load_ai_config()
    api_key = config.get("api_key", "")
    base_url = _resolve_base_url(config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"), api_key)
    model = config.get("model", "qwen3.6-plus")
    model_mode = config.get("model_mode", "text")
    
    # 检查 API Key 格式
    if not api_key:
        return {
            "status": "error",
            "message": "未配置 API Key，请先保存配置",
            "model": model,
            "model_mode": model_mode
        }
    
    if not api_key.startswith("sk-"):
        return {
            "status": "error",
            "message": "API Key 格式错误，应该以 sk- 开头",
            "model": model,
            "model_mode": model_mode
        }
    
    if len(api_key) < 15:
        return {
            "status": "error",
            "message": f"API Key 长度过短（当前{len(api_key)}字符，建议 32+ 字符）",
            "model": model,
            "model_mode": model_mode
        }

    try:
        # 使用自定义端点测试
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 尝试 chat 接口
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello"}
                    ],
                    "max_tokens": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return {
                        "status": "success",
                        "message": "API 连接正常，模型可用",
                        "model": model,
                        "model_mode": model_mode,
                        "key_type": _detect_key_type(api_key),
                        "key_type_label": _key_type_label(api_key),
                        "base_url_suggested": _suggest_base_url(api_key),
                        "request_id": data.get("request_id", ""),
                        "reply": data["choices"][0]["message"]["content"][:50]
                    }
            
            # 解析错误信息
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(response.status_code))

            if response.status_code == 404 and _is_coding_plan_key(api_key):
                return {
                    "status": "error",
                    "message": "当前使用的是 Coding Plan 专属 Key（sk-sp-），请确保 Base URL 为 https://coding.dashscope.aliyuncs.com/v1",
                    "model": model,
                    "model_mode": model_mode,
                    "key_type": _detect_key_type(api_key),
                    "key_type_label": _key_type_label(api_key),
                    "base_url_suggested": _suggest_base_url(api_key),
                    "request_id": error_data.get("request_id", ""),
                    "hint": "如果你想使用通用百炼接口，请改用 sk- 开头的通用 API Key"
                }
            
            if response.status_code == 401:
                return {
                    "status": "error",
                    "message": "API Key 无效或已过期，请检查百炼控制台",
                    "model": model,
                    "model_mode": model_mode,
                    "key_type": _detect_key_type(api_key),
                    "key_type_label": _key_type_label(api_key),
                    "base_url_suggested": _suggest_base_url(api_key),
                    "help": "请访问 https://bailian.console.aliyun.com/ 获取有效 API Key"
                }
            elif "not supported" in error_msg.lower():
                return {
                    "status": "warning",
                    "message": f"模型 {model} 不支持，请更换其他模型",
                    "model": model,
                    "model_mode": model_mode,
                    "key_type": _detect_key_type(api_key),
                    "key_type_label": _key_type_label(api_key),
                    "base_url_suggested": _suggest_base_url(api_key),
                    "suggestion": "尝试：qwen2.5-coder-32b-instruct, codeqwen1.5-7b-chat"
                }
            else:
                return {
                    "status": "error",
                    "message": f"API 返回错误：{error_msg}",
                    "model": model,
                    "model_mode": model_mode,
                    "key_type": _detect_key_type(api_key),
                    "key_type_label": _key_type_label(api_key),
                    "base_url_suggested": _suggest_base_url(api_key),
                    "request_id": error_data.get("request_id", "")
                }
    except httpx.TimeoutException:
        return {
            "status": "error",
            "message": "API 请求超时，请检查网络连接",
            "model": model,
            "model_mode": model_mode,
            "key_type": _detect_key_type(api_key),
            "key_type_label": _key_type_label(api_key),
            "base_url_suggested": _suggest_base_url(api_key)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"连接测试失败：{str(e)}",
            "model": model,
            "model_mode": model_mode,
            "key_type": _detect_key_type(api_key),
            "key_type_label": _key_type_label(api_key),
            "base_url_suggested": _suggest_base_url(api_key)
        }


@router.get("/users")
async def get_user_permissions(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取用户 AI 权限列表"""
    # 从数据库获取用户列表
    users = execute_query("""
        SELECT u.user_id, u.username, u.email, r.role_name,
               u.ai_enabled, u.ai_quota, u.ai_used_today
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        ORDER BY u.user_id
    """)

    result = []
    for user in users:
        result.append({
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user.get("role_name", "普通用户"),
            "ai_enabled": bool(user.get("ai_enabled", 1)),
            "quota": user.get("ai_quota", 100),
            "used_today": user.get("ai_used_today", 0)
        })

    return result


@router.post("/user/{user_id}/toggle")
async def toggle_user_ai_permission(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """切换用户 AI 权限"""
    # 获取当前状态
    user = execute_query("SELECT ai_enabled FROM users WHERE user_id = ?", (user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_status = 0 if user[0].get("ai_enabled") else 1
    execute_update("UPDATE users SET ai_enabled = ? WHERE user_id = ?", (new_status, user_id))

    return {"message": f"用户 AI 权限已{'禁用' if new_status == 0 else '启用'}"}


@router.post("/user/{user_id}/quota")
async def update_user_quota(
    user_id: int,
    quota: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新用户每日配额"""
    user = execute_query("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    execute_update("UPDATE users SET ai_quota = ? WHERE user_id = ?", (quota, user_id))
    return {"message": "配额更新成功"}


@router.get("/stats")
async def get_ai_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 AI 使用统计"""
    from datetime import datetime, timedelta
    
    config = load_ai_config()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 从 ai_query_logs 表统计
    try:
        # 今日调用次数
        today_result = execute_query("""
            SELECT COUNT(*) FROM ai_query_logs 
            WHERE DATE(created_at) = ?
        """, (today,))
        today_count = today_result[0][0] if today_result else 0
        
        # 成功/失败次数
        success_result = execute_query("""
            SELECT COUNT(*) FROM ai_query_logs 
            WHERE DATE(created_at) = ? AND status = 'success'
        """, (today,))
        success_count = success_result[0][0] if success_result else 0
        
        failed_result = execute_query("""
            SELECT COUNT(*) FROM ai_query_logs 
            WHERE DATE(created_at) = ? AND status = 'failed'
        """, (today,))
        failed_count = failed_result[0][0] if failed_result else 0
        
        # 平均响应时间
        time_result = execute_query("""
            SELECT AVG(execution_time_ms) FROM ai_query_logs 
            WHERE DATE(created_at) = ? AND status = 'success'
        """, (today,))
        avg_time = round(time_result[0][0], 2) if time_result and time_result[0][0] else 0
        
        # 总 Token 消耗
        tokens_result = execute_query("""
            SELECT SUM(total_tokens) FROM ai_query_logs 
            WHERE DATE(created_at) = ? AND status = 'success'
        """, (today,))
        total_tokens = tokens_result[0][0] if tokens_result and tokens_result[0][0] else 0
        
        return {
            "today_count": today_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "avg_time": avg_time or 0,
            "total_tokens": total_tokens or 0,
            "daily_quota": config.get("daily_quota", 100),
            "remaining": config.get("daily_quota", 100) - today_count
        }
    except Exception as e:
        # 表不存在时返回默认值
        return {
            "today_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "avg_time": 0,
            "total_tokens": 0,
            "daily_quota": config.get("daily_quota", 100),
            "remaining": config.get("daily_quota", 100)
        }
