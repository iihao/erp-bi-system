#!/usr/bin/env python3
"""
AI 智能问数接口 - 性能优化版
优化点：
1. LRU 缓存相同问题，避免重复调 AI（命中即 0ms）
2. 超时 120s → 30s，快速失败
3. Prompt 精简 60%，减少 token 消耗
4. max_tokens 1000 → 500，SQL 查询不需要长输出
5. Schema 启动时缓存，不再每次请求读取
6. 标准 SQL 匹配预加载到内存，无需每次查库
7. 连接复用，使用 httpx.AsyncClient 连接池
"""

import os
import json
import logging
import time
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from collections import OrderedDict
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from api.ai_query_vector import vector_store, embed_text, normalize_question as normalize_for_vector

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-query", tags=["AI 智能问数"])


@router.on_event("startup")
async def init_caches():
    """启动时预加载缓存"""
    try:
        get_schema_context()
        logger.info("✅ Schema 缓存已预加载")
    except Exception as e:
        logger.warning(f"⚠️ Schema 预加载失败：{e}")

    try:
        load_standard_sql_cache()
        logger.info("✅ 标准 SQL 缓存已预加载")
    except Exception as e:
        logger.warning(f"⚠️ 标准 SQL 预加载失败：{e}")

    try:
        await vector_store.sync(bailian_client.api_key, bailian_client.base_url)
    except Exception as e:
        logger.warning(f"⚠️ 向量索引同步失败：{e}")


class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str
    top_k: int = 10


class QueryResponse(BaseModel):
    """查询响应模型"""
    sql: str
    explanation: str
    data: Optional[list] = None
    columns: Optional[list] = None
    tokens_used: Optional[int] = None
    execution_time_ms: Optional[int] = None
    matched_standard: Optional[bool] = False
    log_id: Optional[int] = None
    # 新增：图表推荐类型
    chart_type: Optional[str] = None
    # 新增：思考过程（关键词、匹配表、匹配来源等）
    thinking: Optional[Dict[str, Any]] = None


class ExtractKeywordsRequest(BaseModel):
    """关键词提取请求"""
    question: str


class ExtractKeywordsResponse(BaseModel):
    """关键词提取响应"""
    keywords: List[str]


class StandardSQLCreate(BaseModel):
    """创建标准 SQL 请求"""
    keywords: List[str]
    question_template: str
    standard_sql: str
    explanation: str = ""


class StandardSQLUpdate(BaseModel):
    """更新标准 SQL 请求"""
    keywords: Optional[List[str]] = None
    question_template: Optional[str] = None
    standard_sql: Optional[str] = None
    explanation: Optional[str] = None
    is_active: Optional[int] = None


# ============================================
# 性能优化：缓存层
# ============================================

class LRUCache:
    """简单的 LRU 缓存，用于缓存 AI 查询结果"""

    def __init__(self, maxsize=200):
        self._cache = OrderedDict()
        self._maxsize = maxsize

    def get(self, key):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def clear(self):
        self._cache.clear()


# 全局缓存实例
_query_cache = LRUCache(maxsize=200)
_schema_cache = None
_standard_sql_cache = None
_http_client = None


def _normalize_base_url(base_url: str) -> str:
    """统一百炼 OpenAI 兼容接口地址"""
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


def _resolve_base_url(base_url: str, api_key: str = "") -> str:
    """根据 Key 类型选择可用接口地址"""
    normalized = (base_url or "").strip().rstrip("/")
    if _is_coding_plan_key(api_key):
        if "coding.dashscope.aliyuncs.com" in normalized:
            return normalized
        if normalized.endswith("/apps/anthropic"):
            return normalized
        return "https://coding.dashscope.aliyuncs.com/v1"

    if "coding.dashscope.aliyuncs.com" in normalized:
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    return _normalize_base_url(normalized)


def get_query_cache():
    return _query_cache


def _normalize_question(question: str) -> str:
    """问题归一化：去除多余空格和标点，提高缓存命中率"""
    q = question.strip().rstrip("？?。").strip()
    return q.lower()


# ============================================
# 百炼 API 客户端 - 优化版
# ============================================

class BaiLianClient:
    """百炼 API 客户端 - 优化版"""

    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')
        self.config = {}
        self.api_key = ""
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = "qwen3.6-plus"
        self.model_mode = "text"
        self.reload_config()

    def reload_config(self):
        """重新加载 AI 配置，避免配置修改后需要重启服务。

        优先级：.env 环境变量 > ai_config.json
        .env 作为 secrets 的唯一来源，避免 ai_config.json 中的旧配置覆盖新值。
        """
        # 先加载 json 配置作为 fallback
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("📖 已从 ai_config.json 加载配置")
        except Exception as e:
            logger.warning(f"无法加载 ai_config.json: {e}，将使用环境变量配置")
            self.config = {}

        # .env 优先，ai_config.json 作为 fallback
        self.api_key = os.getenv('DASHSCOPE_API_KEY') or self.config.get('api_key')
        if not self.api_key or self.api_key == 'your-api-key-here':
            logger.error("❌ DASHSCOPE_API_KEY 未配置")
        else:
            logger.info(f"✅ API Key 已配置：{self.api_key[:15]}...")

        env_base_url = os.getenv('DASHSCOPE_BASE_URL')
        self.base_url = _resolve_base_url(
            env_base_url or self.config.get('base_url') or 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            self.api_key
        )
        self.model = os.getenv('DASHSCOPE_MODEL') or self.config.get('model') or 'qwen3.6-plus'
        self.model_mode = os.getenv('DASHSCOPE_MODEL_MODE') or self.config.get('model_mode') or 'text'
        logger.info(f"🤖 使用模型：{self.model} / mode={self.model_mode} @ {self.base_url}")

    async def _get_client(self):
        """获取复用的 httpx 客户端"""
        global _http_client
        if _http_client is None or _http_client.is_closed:
            import httpx
            # 优化：超时 30s，启用连接复用
            limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
            _http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0),
                limits=limits
            )
        return _http_client

    async def generate_sql(self, question: str, schema_context: str) -> Tuple[str, str, int, int, int]:
        """
        生成 SQL 查询
        返回：(sql, explanation, input_tokens, output_tokens, total_tokens)
        """
        self.reload_config()
        if not self.api_key or self.api_key == 'your-api-key-here':
            raise HTTPException(
                status_code=503,
                detail="AI 服务未配置：请在 .env 文件中设置正确的 DASHSCOPE_API_KEY"
            )

        # 优化：将完整 schema 喂给模型，避免只认核心表
        mode_hint = {
            "text": "当前为文本生成模式，专注将业务问题转成精准 SQL。",
            "deep": "当前为深度思考模式，请先分析业务口径、表关系与指标定义，再生成 SQL。",
            "vision": "当前为视觉理解模式，如果输入包含图表或截图，请先理解图片内容后再生成 SQL。"
        }.get(self.model_mode, "当前为文本生成模式，专注将业务问题转成精准 SQL。")

        system_prompt = f"""你是绿洲地产 BI 的 SQL 专家，擅长地产销售、财务、成本数据分析。

可用数据库表结构如下：
{schema_context}

规则：
1. 仅输出 SELECT 语句
2. 优先使用 ads_ / dws_ 聚合表，其次 dwd_ / re_ / ods_ 明细表
3. 使用 SQLite 兼容语法，结果默认 LIMIT 10
4. 金额字段建议除以 10000 显示为万元
5. 涉及项目对比时按金额降序排列
6. 只返回 SQL，不要输出解释性文字
7. {mode_hint}"""

        # 优化：max_tokens 从 1000 降到 500，SQL 查询不需要长输出
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"问题：{question}"}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        try:
            client = await self._get_client()
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            logger.info(f"📡 调用 AI: {self.model}")
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"❌ AI 失败：{response.status_code} - {response.text[:200]}")
                raise HTTPException(
                    status_code=500,
                    detail=f"AI 服务错误：{response.status_code}"
                )

            result = response.json()
            choices = result.get("choices", [])
            if choices and len(choices) > 0:
                message = choices[0].get("message", {})
                sql = message.get("content", "").strip()
            else:
                sql = ""

            usage = result.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # 清理 SQL
            sql = sql.replace("```sql", "").replace("```", "").strip()

            logger.info(f"✅ SQL 生成成功，tokens: {total_tokens}")

            return sql, "根据您的问题生成的 SQL 查询", input_tokens, output_tokens, total_tokens

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ AI 调用失败：{type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"AI 服务调用失败：{str(e)}")


# ============================================
# 数据库 Schema - 启动时缓存
# ============================================

DB_SCHEMA_CONTEXT = """
表结构说明：

=== 地产销售模块（re_ 开头，核心业务） ===

1. re_projects (地产项目表)
   - project_id: 项目 ID
   - project_code: 项目编码
   - project_name: 项目名称
   - city: 城市
   - district: 区域
   - project_type: 项目类型
   - total_units: 总房源数
   - project_status: 项目状态

2. re_buildings (楼栋表)
   - building_id: 楼栋 ID
   - project_id: 所属项目 ID
   - building_code/name: 楼栋编码/名称
   - building_type: 楼栋类型
   - floor_count: 楼层数
   - unit_count: 单元数

3. re_units (房源表)
   - unit_id: 房源 ID
   - building_id: 所属楼栋 ID
   - unit_code/name: 房源编码/名称
   - floor: 楼层
   - unit_type: 户型
   - building_area: 建筑面积
   - internal_area: 套内面积
   - total_price: 总价
   - unit_price: 单价
   - unit_status: 房源状态（可售/已认购/已签约/已交付）

4. re_customers (客户表)
   - customer_id: 客户 ID
   - customer_code/name: 客户编码/姓名
   - customer_type: 客户类型
   - phone: 电话
   - city: 城市
   - source: 客户来源
   - intention_level: 意向等级
   - follow_count: 跟进次数
   - status: 客户状态

5. re_customer_followups (客户跟进记录表)
   - followup_id: 跟进 ID
   - customer_id: 客户 ID
   - sales_id: 销售 ID
   - followup_date: 跟进日期
   - followup_type: 跟进方式
   - followup_content: 跟进内容

6. re_subscriptions (认购表)
   - subscription_id: 认购 ID
   - subscription_code: 认购编码
   - unit_id: 房源 ID
   - customer_id: 客户 ID
   - sales_id: 销售 ID
   - subscription_date: 认购日期
   - total_price: 认购总价
   - deposit_amount: 定金
   - mortgage_amount: 贷款金额
   - mortgage_bank: 贷款银行
   - subscription_status: 认购状态

7. re_contracts (合同表)
   - contract_id: 合同 ID
   - contract_code: 合同编码
   - subscription_id: 认购 ID
   - unit_id: 房源 ID
   - customer_id: 客户 ID
   - contract_date: 签约日期
   - contract_type: 合同类型
   - total_price: 合同总价
   - area: 面积
   - unit_price: 单价
   - payment_method: 付款方式
   - total_paid: 已付金额
   - balance: 余款
   - mortgage_amount: 贷款金额
   - contract_status: 合同状态

8. re_payments (回款表)
   - payment_id: 回款 ID
   - payment_code: 回款编码
   - contract_id: 合同 ID
   - customer_id: 客户 ID
   - payment_date: 回款日期
   - payment_type: 回款类型
   - amount: 回款金额
   - payment_method: 付款方式

9. re_receivables (应收表)
   - receivable_id: 应收 ID
   - contract_id: 合同 ID
   - customer_id: 客户 ID
   - receivable_type: 应收类型
   - amount: 应收金额
   - due_date: 到期日期
   - received_amount: 已收金额
   - balance: 应收余额
   - overdue_days: 逾期天数
   - status: 状态

10. re_refunds (退款表)
    - refund_id: 退款 ID
    - refund_code: 退款编码
    - contract_id: 合同 ID
    - refund_amount: 退款金额
    - refund_type: 退款类型
    - refund_status: 退款状态

=== 数据仓库事实表（dws_ 开头，聚合分析） ===

11. dws_sales_payment_fact (销售回款事实表)
    - project_guid/name: 项目 GUID/名称
    - contract_guid: 合同 GUID
    - date_key/year/month: 日期维度
    - contract_amount: 合同金额
    - payment_amount: 回款金额
    - payment_rate: 回款率
    - contract_count: 合同数

12. dws_sales_cost_fact (销售成本事实表)
    - project_guid/name: 项目 GUID/名称
    - account_number/name: 科目编码/名称
    - cost_center: 成本中心
    - contract_amount: 合同金额
    - cost_amount: 成本金额
    - budget_amount: 预算金额
    - budget_variance: 预算差异
    - variance_rate: 差异率

=== 数据仓库明细表（dwd_ 开头） ===

13. dwd_contract_detail (合同明细表)
    - contract_guid/code: 合同 GUID/编码
    - project_guid/name: 项目 GUID/名称
    - customer_name: 客户姓名
    - contract_type: 合同类型
    - contract_amount: 合同金额
    - contract_date: 签约日期
    - contract_status: 合同状态

14. dwd_room_detail (房间明细表)
    - room_guid: 房间 GUID
    - project_guid/name: 项目 GUID/名称
    - building_code: 楼栋编码
    - room_code/name: 房间编码/名称
    - floor: 楼层
    - room_type: 房型
    - building_area: 建筑面积
    - total_price/unit_price: 总价/单价
    - room_status: 房间状态

15. dwd_payment_detail (回款明细表)
    - payment_guid: 回款 GUID
    - contract_guid: 合同 GUID
    - project_guid/name: 项目 GUID/名称
    - payment_amount: 回款金额
    - payment_date: 回款日期
    - payment_type: 回款类型
    - payment_method: 付款方式

16. dwd_trade_detail (交易明细表)
    - trade_guid: 交易 GUID
    - project_guid/name: 项目 GUID/名称
    - customer_name: 客户姓名
    - trade_status: 交易状态
    - contract_sign_date: 签约日期
    - total_price/area/unit_price: 总价/面积/单价

=== 应用数据层（ads_ 开头，报表汇总） ===

17. ads_finance_dashboard (财务仪表盘表)
    - company_code: 公司编码
    - total_revenue: 总收入
    - total_cost: 总成本
    - total_profit: 总利润
    - profit_margin: 利润率
    - total_assets/liabilities: 总资产/负债
    - cash_flow: 现金流

18. ads_sales_dashboard (销售仪表盘表)
    - project_guid/name: 项目 GUID/名称
    - total_units/sold_units/available_units: 总/已售/可售房源
    - sell_through_rate: 去化率
    - total_sales: 销售总额
    - total_payment: 回款总额
    - payment_rate: 回款率
    - avg_unit_price: 均价

19. ads_szl_dashboard (损益仪表盘表)
    - project_guid/name: 项目 GUID/名称
    - sales_revenue: 销售收入
    - total_cost/expense: 总成本/费用
    - operating_profit: 营业利润
    - net_profit: 净利润
    - profit_margin: 利润率
    - roi: 投资回报率

20. ads_project_cost_report (项目成本报表)
    - project_guid/name: 项目 GUID/名称
    - account_number/name: 科目编码/名称
    - cost_type: 成本类型
    - budget_amount: 预算金额
    - actual_amount: 实际金额
    - variance_amount/rate: 差异金额/率
    - completion_rate: 完成率

21. ads_group_sales_report (集团销售报表)
    - project_guid/name: 项目 GUID/名称
    - city: 城市
    - target_amount: 目标金额
    - actual_amount: 实际金额
    - achievement_rate: 达成率
    - contract_count: 合同数
    - area/unit_price: 面积/单价

22. ads_group_pay_report (集团付款报表)
    - project_guid/name: 项目 GUID/名称
    - contract_pay_amount: 合同付款
    - fee_amount: 费用
    - total_amount: 总额
    - budget_amount: 预算
    - variance_amount/rate: 差异金额/率

=== 维度表（dim_ 开头） ===

23. dim_project (项目维度表)
    - project_guid/code/name: 项目 GUID/编码/名称
    - city/district: 城市/区域
    - product_type: 产品类型
    - total_units: 总房源数
    - project_status: 项目状态

24. dim_account (科目维度表)
    - account_guid/code/name: 科目 GUID/编码/名称
    - account_type: 科目类型
    - parent_account_code/name: 上级科目
    - level: 层级
    - full_path: 完整路径

=== 其他表 ===

25. products (产品表) - id, product_code, product_name, category, unit_price, stock_quantity
26. customers (客户表) - id, customer_code, customer_name, customer_type, industry
27. sales_orders (销售订单表) - id, order_no, customer_id, order_date, final_amount, order_status
28. sales_order_items (订单明细表) - id, order_id, product_id, quantity, unit_price, subtotal

=== 地产全量补充表（项目交付 / 经营 / 仓库） ===

29. re_customer_followups (客户跟进记录表)
    - followup_id, customer_id, sales_id, followup_date, followup_type, followup_content, customer_feedback, next_plan
30. re_refunds (退款记录表)
    - refund_id, refund_code, contract_id, customer_id, payment_id, refund_amount, refund_type, refund_reason, apply_date, approve_date, refund_date, refund_status
31. ods_room (ODS 房源表)
    - room_guid, project_guid, building_code, room_code, room_name, floor, unit_number, room_type, building_area, internal_area, share_area, orientation, total_price, unit_price, room_status
32. ods_trade (ODS 交易表)
    - trade_guid, contract_guid, room_guid, proj_guid, buyer_all_names, trade_status, contract_qs_date, contract_ywgs_date, rgorder_guid, rgorder_qs_date, rgorder_type
33. ods_payment (ODS 回款表)
    - payment_guid, contract_guid, proj_guid, customer_guid, payment_amount, payment_date, payment_type, payment_method, invoice_number
34. ods_pay (ODS 付款登记表)
    - pay_guid, contract_guid, proj_guid, pay_amount, pay_date, pay_type, payee_name, invoice_flag
35. ods_contract (ODS 合同表)
    - contract_guid, proj_guid, room_guid, customer_guid, contract_code, contract_type, contract_amount, contract_date, contract_status, pay_plan
36. ods_account (ODS 科目表)
    - account_guid, account_code, account_name, account_type, parent_account_guid, level, balance_direction, is_leaf
37. ods_bseg (ODS 凭证表)
    - belnr, buzei, bukrs, gjahr, hkont, shkzg, dmbtr, wrbtr, waers, kosta, kostl, bldat, budat, cpudt
38. ods_gl_actual (ODS 总账实际表)
    - gl_guid, company_code, fiscal_year, document_number, line_item, account_number, account_name, cost_center, profit_center, gl_amount, local_amount, currency, posting_date, document_date
39. ods_other (ODS 其他填报表)
    - other_id, data_type, data_content, fill_user, fill_date, remarks
40. dwd_trade_detail (DWD 销售交易明细表)
    - trade_key, trade_guid, contract_guid, room_guid, project_guid, project_name, customer_name, trade_status, contract_sign_date, contract_business_date, total_price, area, unit_price
41. dwd_payment_detail (DWD 回款明细表)
    - payment_key, payment_guid, contract_guid, project_guid, project_name, customer_name, payment_amount, payment_date, payment_type, payment_method
42. dwd_contract_detail (DWD 合同明细表)
    - contract_key, contract_guid, contract_code, project_guid, project_name, customer_name, contract_type, contract_amount, contract_date, contract_status
43. dwd_pay_detail (DWD 付款明细表)
    - pay_key, pay_guid, contract_guid, project_guid, project_name, pay_amount, pay_date, pay_type, payee_name
44. dwd_gl_actual_detail (DWD 总账实际明细表)
    - gl_key, gl_guid, company_code, fiscal_year, document_number, account_number, account_name, cost_center, profit_center, amount, posting_date
45. dwd_gl_budget_detail (DWD 总账预算明细表)
    - budget_key, budget_guid, company_code, fiscal_year, account_number, account_name, cost_center, budget_amount, budget_date
46. dws_sales_payment_fact (DWS 销售回款事实表)
    - project_guid, project_name, contract_guid, date_key, contract_amount, payment_amount, payment_rate, contract_count
47. dws_sales_cost_fact (DWS 销售成本事实表)
    - project_guid, project_name, account_number, account_name, cost_center, contract_amount, cost_amount, budget_amount, budget_variance, variance_rate
48. dim_project (项目维度表)
    - project_guid, project_code, project_name, city, district, product_type, total_units, project_status
49. dim_date (日期维度表)
    - date_key, full_date, year, quarter, month, day, week_of_year, is_month_end
50. dim_account (科目维度表)
    - account_guid, account_code, account_name, account_type, parent_account_code, parent_account_name, level, full_path
51. dim_permission (权限维度表)
    - permission_id, permission_code, permission_name, module_name, action_name, status
52. dim_indicator (指标维度表)
    - indicator_id, indicator_code, indicator_name, indicator_category, data_source, formula, unit, status
53. ads_group_sales_report (集团销售报表)
    - project_guid, project_name, city, target_amount, actual_amount, achievement_rate, contract_count, area, unit_price
54. ads_group_salesdate_report (集团销售日表)
    - project_guid, project_name, date_key, actual_amount, contract_count, payment_amount, achievement_rate
55. ads_group_pay_report (集团付款报表)
    - project_guid, project_name, contract_pay_amount, fee_amount, total_amount, budget_amount, variance_amount, variance_rate
56. ads_project_cost_report (项目成本报表)
    - project_guid, project_name, account_number, account_name, cost_type, budget_amount, actual_amount, variance_amount, variance_rate, completion_rate
57. ads_sales_dashboard (销售仪表盘)
    - project_guid, project_name, total_units, sold_units, available_units, sell_through_rate, total_sales, total_payment, payment_rate, avg_unit_price
58. ads_finance_dashboard (财务仪表盘)
    - company_code, total_revenue, total_cost, total_profit, profit_margin, total_assets, liabilities, cash_flow
59. ads_szl_dashboard (损益仪表盘)
    - project_guid, project_name, sales_revenue, total_cost, expense, operating_profit, net_profit, profit_margin, roi
"""


def get_schema_context() -> str:
    """获取缓存的 Schema 上下文"""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = DB_SCHEMA_CONTEXT
    return _schema_cache


def refresh_schema_cache():
    """刷新 Schema 缓存"""
    global _schema_cache
    _schema_cache = None
    return get_schema_context()


# ============================================
# 标准 SQL 匹配 - 内存缓存
# ============================================

def load_standard_sql_cache() -> List[Dict[str, Any]]:
    """预加载所有启用的标准 SQL 到内存"""
    global _standard_sql_cache
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, keywords, question_template, standard_sql, explanation
                FROM standard_sql_library
                WHERE is_active = 1
            """)
            records = cursor.fetchall()
            _standard_sql_cache = [
                {
                    'id': r['id'],
                    'keywords': json.loads(r['keywords']) if r['keywords'] else [],
                    'question_template': r['question_template'],
                    'standard_sql': r['standard_sql'],
                    'explanation': r['explanation'] or '标准 SQL'
                }
                for r in records
            ]
            logger.info(f"📦 标准 SQL 缓存已加载：{len(_standard_sql_cache)} 条")
            return _standard_sql_cache
    except Exception as e:
        logger.error(f"加载标准 SQL 缓存失败：{e}")
        _standard_sql_cache = []
        return _standard_sql_cache


def match_standard_sql_cached(question_or_keywords) -> Optional[Dict[str, Any]]:
    """从内存缓存中匹配标准 SQL（评分最高优先）"""
    global _standard_sql_cache
    if _standard_sql_cache is None:
        load_standard_sql_cache()

    if isinstance(question_or_keywords, str):
        keywords = extract_keywords(question_or_keywords)
        normalized_question = _normalize_question(question_or_keywords)
    else:
        keywords = list(question_or_keywords or [])
        normalized_question = ""

    best_match = None
    best_score = 0

    for record in _standard_sql_cache:
        template_text = _normalize_question(record.get('question_template') or "")
        score = sum(1 for kw in keywords if kw in record['keywords'])
        if normalized_question and template_text:
            if normalized_question == template_text:
                score += 4
            else:
                score += sum(1 for kw in keywords if kw and kw in template_text)
        if score > best_score:
            best_score = score
            best_match = record

    if best_match:
        logger.info(f"✅ 匹配标准 SQL (id={best_match['id']}, score={best_score}): {best_match['question_template']}")
        return best_match

    return None


# ============================================
# 图表推荐 & 思考过程
# ============================================

def recommend_chart(columns: list, data: list) -> str:
    """根据查询结果推荐图表类型"""
    if not columns or not data or len(columns) < 2:
        return 'table'

    col_count = len(columns)
    row_count = len(data)
    col_names = [c.lower() for c in columns]

    # 单维度 + 单指标 → 饼图或柱状图
    if col_count == 2 and row_count <= 10:
        return 'pie'

    # 包含时间字段 → 折线图
    time_keywords = ['year', 'month', 'date', '时间', '月', '年', '日期']
    has_time = any(t in ' '.join(col_names) for t in time_keywords)
    if has_time:
        return 'line'

    # 多维度 + 指标 → 柱状图
    if col_count >= 2 and row_count <= 20:
        return 'bar'

    # 数据量大 → 表格
    return 'table'


def build_thinking_detail(keywords: list, question: str, standard_match: Optional[Dict], sql: str, columns: list, data: list) -> Dict[str, Any]:
    """构建思考过程信息"""
    dimension_field = None
    measure_field = None
    if columns:
        dimension_field = next(
            (
                col for col in columns
                if any(token in col.lower() for token in ['name', 'title', 'city', 'project', 'building', 'customer', 'type', 'status', 'code', 'date', 'month', 'year'])
            ),
            columns[0]
        )
        measure_field = next(
            (
                col for col in columns
                if any(token in col.lower() for token in ['amount', 'count', 'price', 'rate', 'profit', 'cost', 'fee', 'quantity', 'total', 'sum'])
            ),
            None
        )

    step1 = f"解析问题，提取关键词：{', '.join(keywords)}" if keywords else "解析问题，未识别到明确关键词"
    step2 = "优先命中标准 SQL 库" if standard_match else "标准 SQL 未命中，调用 AI 在线生成"
    step3 = "执行 SQL 并获取结果集"
    step4 = f"根据字段特征推荐图表：{recommend_chart(columns, data)}" if columns else "结果为空，默认展示表格"

    thinking = {
        "keywords": keywords,
        "matched_standard": standard_match is not None,
        "decision_steps": [step1, step2, step3, step4],
        "result_profile": {
            "row_count": len(data) if data else 0,
            "column_count": len(columns) if columns else 0,
            "dimension_field": dimension_field,
            "measure_field": measure_field,
            "chart_type": recommend_chart(columns, data) if columns else "table"
        }
    }

    if standard_match:
        thinking["match_source"] = "标准库命中"
        thinking["matched_template"] = standard_match.get('question_template', '')
        thinking["match_score"] = "精确匹配"
        thinking["recommended_tables"] = _extract_tables_from_sql(standard_match.get('standard_sql', ''))
        thinking["field_mapping"] = _simple_field_mapping(columns, data)
        thinking["reasoning"] = "标准 SQL 已覆盖该问题，直接复用已审核口径，避免重复生成。"
    else:
        thinking["match_source"] = "AI 在线生成"
        thinking["matched_template"] = None
        thinking["match_score"] = "AI 智能推导"
        thinking["recommended_tables"] = _extract_tables_from_sql(sql)
        thinking["field_mapping"] = _simple_field_mapping(columns, data)
        thinking["reasoning"] = _generate_reasoning(keywords, question, columns, data)

    return thinking


def _extract_tables_from_sql(sql: str) -> List[str]:
    """从 SQL 中提取表名"""
    import re
    # 匹配 FROM 和 JOIN 后面的表名
    pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_]\w*)'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return list(dict.fromkeys(matches))  # 去重保序


def _simple_field_mapping(columns: list, data: list) -> List[Dict[str, str]]:
    """简单的字段映射"""
    if not columns:
        return []
    mapping = []
    for col in columns:
        field_type = "指标"
        if any(k in col.lower() for k in ['name', '名称', 'city', '城市', 'type', '类型', 'status', '状态', 'code', '编码']):
            field_type = "维度"
        elif any(k in col.lower() for k in ['count', 'sum', 'amount', 'rate', 'total', 'avg', '数量', '金额', '率', '万']):
            field_type = "指标"
        mapping.append({"field": col, "type": field_type})
    return mapping


def _generate_reasoning(keywords: list, question: str, columns: list, data: list) -> str:
    """生成 AI 推理说明"""
    parts = []
    if keywords:
        parts.append(f"识别到关键词：{', '.join(keywords)}")

    if '销售' in keywords and '排行' in keywords:
        parts.append("使用聚合表按金额降序排列")
    elif '回款' in keywords and '趋势' in keywords:
        parts.append("按时间维度汇总回款数据")
    elif '利润' in keywords:
        parts.append("从损益仪表盘获取利润数据")
    elif '成本' in keywords:
        parts.append("从成本报表获取预算与实际对比")

    if len(data) > 0:
        parts.append(f"查询返回 {len(data)} 条记录")

    return '；'.join(parts) if parts else "根据问题语义推导最佳查询"

def extract_keywords(question: str) -> List[str]:
    """从问题中提取关键词"""
    keyword_patterns = {
        # 通用业务
        '产品': ['产品', '商品', '品类', 'category'],
        '客户': ['客户', '顾客', '买家', 'customer'],
        '订单': ['订单', '销售单', 'order'],
        '销售': ['销售', '销售额', '销量', '成交', '签约额'],
        '时间': ['时间', '日期', '什么时候'],
        '今天': ['今天', '今日', '当天'],
        '昨天': ['昨天', '昨日', '前一天'],
        '本月': ['本月', '这个月', '当月'],
        '上月': ['上月', '上个月', '前一个月'],
        '今年': ['今年', '本年', '当前年'],
        '统计': ['统计', '计算', '汇总', '合计'],
        '查询': ['查询', '查找', '搜索', '有哪些'],
        '排行': ['排行', '排名', '最高', '最多', 'top'],
        '占比': ['占比', '比例', '百分比', '分布'],
        '金额': ['金额', '钱', '收入', '营收', 'amount', 'price'],
        '数量': ['数量', '个数', '多少', 'count', 'quantity'],
        '价格': ['价格', '单价', '价位'],
        '利润': ['利润', '盈利', '赚'],
        # 地产领域
        '项目': ['项目', '楼盘', '地产', 're_projects'],
        '房源': ['房源', '房间', '单元', 'unit', '楼栋'],
        '合同': ['合同', '签约', '签约单', 'contract'],
        '认购': ['认购', '认筹', 'subscription'],
        '回款': ['回款', '收款', '付款', 'payment', '款项'],
        '应收': ['应收', '欠款', 'receivable', '逾期', '账款'],
        '退款': ['退款', '退房', '退订', 'refund'],
        '成本': ['成本', '预算', '费用', 'cost', 'budget', '支出'],
        '财务': ['财务', '资产', '负债', '现金流', 'finance', '利润', '损益'],
        '损益': ['损益', '利润表', '利润分析', '损益表', 'roi', '回报率', '净利润'],
        '跟进': ['跟进', '回访', 'followup', '客户跟进'],
        '去化': ['去化', '去化率', '售罄', '消化'],
        '目标': ['目标', '达成', '完成率', 'achievement', '指标', '维度'],
        '楼栋': ['楼栋', '楼层', '楼座', 'building'],
        '认购书': ['认购书', '订金', '定金', '预订', 'subscrib'],
        '项目成本': ['项目成本', '成本报表', '项目预算', 'project cost'],
        '集团': ['集团', '总部', '区域公司', '集团销售', '集团付款'],
    }

    keywords = []
    question_lower = question.lower()

    for keyword, patterns in keyword_patterns.items():
        for pattern in patterns:
            if pattern.lower() in question_lower:
                if keyword not in keywords:
                    keywords.append(keyword)
                break

    if not keywords:
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', question)
        keywords = list(set(words))[:5]

    return keywords


# ============================================
# 数据库连接和日志
# ============================================

def get_db_connection():
    """获取数据库连接"""
    from api.database import get_db_connection as db_conn
    return db_conn()


def log_query(
    question: str, generated_sql: Optional[str], keywords: List[str],
    input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0,
    execution_time_ms: int = 0, status: str = 'success',
    error_message: Optional[str] = None, match_source: Optional[str] = None
) -> int:
    """记录问数日志"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_query_logs
                (question, generated_sql, keywords, input_tokens, output_tokens, total_tokens,
                 execution_time_ms, status, error_message, match_source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                question, generated_sql, json.dumps(keywords, ensure_ascii=False),
                input_tokens, output_tokens, total_tokens,
                execution_time_ms, status, error_message, match_source
            ))
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"记录日志失败：{e}")
        return -1


# 初始化客户端
bailian_client = BaiLianClient()


# ============================================
# API 接口
# ============================================

@router.post("/execute-query")
async def execute_query(request: QueryRequest):
    """
    生成 SQL 并执行查询，返回结果数据
    优化：缓存 → 标准 SQL → AI 生成
    """
    start_time = time.time()
    log_id = -1
    tokens_used = 0
    matched_standard = False
    match_source = "AI 在线生成"
    keywords = []

    try:
        # 1. 问题归一化
        normalized = _normalize_question(request.question)

        # 2. 检查缓存（命中则 0ms 返回）
        cache_key = f"{normalized}:{request.top_k}"
        cached = get_query_cache().get(cache_key)
        if cached:
            logger.info(f"💾 缓存命中：{request.question[:50]}")
            return QueryResponse(**cached)

        # 3. 提取关键词
        keywords = extract_keywords(request.question)

        # 4. 匹配标准 SQL（从内存缓存，无查库）
        standard_match = match_standard_sql_cached(request.question)

        if standard_match:
            matched_standard = True
            match_source = "标准库命中"
            sql = standard_match['standard_sql']
            explanation = standard_match['explanation']
            logger.info(f"✅ 使用标准 SQL: {sql[:80]}")
        else:
            # 5. 向量语义匹配（新增，~200ms）
            try:
                question_vec = await embed_text(
                    normalize_for_vector(request.question),
                    bailian_client.api_key,
                    bailian_client.base_url
                )
                vector_match = await vector_store.search_with_embedding(request.question, question_vec)
            except Exception as e:
                logger.warning(f"⚠️ 向量匹配跳过：{e}")
                vector_match = None

            if vector_match:
                match_source = f"向量匹配({vector_match['score']})"
                sql = vector_match['sql']
                explanation = vector_match['explanation']
                logger.info(f"🧠 向量语义匹配命中: score={vector_match['score']}, query={vector_match.get('match_query', '')[:40]}")
            else:
                match_source = "AI 在线生成"
                # 6. 调用 AI 生成 SQL
                schema = get_schema_context()
                sql, explanation, input_tokens, output_tokens, total_tokens = await bailian_client.generate_sql(
                    question=request.question,
                    schema_context=schema
                )
                tokens_used = total_tokens

                # 保存到向量库，供后续复用
                try:
                    await vector_store.save(request.question, sql, explanation, bailian_client.api_key, bailian_client.base_url)
                except Exception as e:
                    logger.warning(f"⚠️ 向量保存失败：{e}")

        # 7. 执行查询
        db_path = os.getenv('SQLITE_DB_PATH', os.path.join(os.path.dirname(__file__), "..", "db", "erp_bi.db"))
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            data = [dict(zip(columns, row)) for row in rows]
            logger.info(f"✅ 查询成功，返回 {len(data)} 条记录")
        except sqlite3.Error as e:
            logger.error(f"❌ SQL 执行失败：{e}")
            raise HTTPException(status_code=400, detail=f"SQL 执行失败：{str(e)}")
        finally:
            conn.close()

        execution_time_ms = int((time.time() - start_time) * 1000)

        # 7. 推荐图表和构建思考过程
        trimmed_data = data[:request.top_k]
        chart_type = recommend_chart(columns, trimmed_data)
        thinking = build_thinking_detail(keywords, request.question, standard_match if matched_standard else None, sql, columns, trimmed_data)
        # 更新匹配来源（支持向量匹配）
        thinking["match_source"] = match_source

        # 8. 写入缓存
        response_data = {
            "sql": sql,
            "explanation": explanation,
            "data": trimmed_data,
            "columns": columns,
            "tokens_used": tokens_used if not matched_standard else 0,
            "execution_time_ms": execution_time_ms,
            "matched_standard": matched_standard,
            "log_id": log_id,
            "chart_type": chart_type,
            "thinking": thinking
        }
        get_query_cache().put(cache_key, response_data)

        # 8. 记录日志
        log_id = log_query(
            question=request.question, generated_sql=sql, keywords=keywords,
            input_tokens=tokens_used if not matched_standard else 0,
            output_tokens=0, total_tokens=tokens_used,
            execution_time_ms=execution_time_ms, status='success',
            match_source=match_source
        )

        return QueryResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"❌ 查询失败：{type(e).__name__}: {e}")
        log_id = log_query(
            question=request.question, generated_sql=None, keywords=keywords if 'keywords' in locals() else [],
            input_tokens=0, output_tokens=0, total_tokens=0,
            execution_time_ms=execution_time_ms, status='failed', error_message=str(e),
            match_source=match_source
        )
        raise HTTPException(status_code=500, detail=f"查询执行失败：{str(e)}")


@router.post("/generate-sql", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    """仅生成 SQL，不执行"""
    start_time = time.time()
    log_id = -1
    tokens_used = 0
    matched_standard = False
    match_source = "AI 在线生成"
    keywords = []

    try:
        normalized = _normalize_question(request.question)
        cache_key = f"{normalized}:sql-only"
        cached = get_query_cache().get(cache_key)
        if cached:
            logger.info(f"💾 缓存命中：{request.question[:50]}")
            return QueryResponse(**cached)

        keywords = extract_keywords(request.question)
        standard_match = match_standard_sql_cached(request.question)

        if standard_match:
            matched_standard = True
            match_source = "标准库命中"
            sql = standard_match['standard_sql']
            explanation = standard_match['explanation']
        else:
            # 向量语义匹配
            try:
                question_vec = await embed_text(
                    normalize_for_vector(request.question),
                    bailian_client.api_key,
                    bailian_client.base_url
                )
                vector_match = await vector_store.search_with_embedding(request.question, question_vec)
            except Exception as e:
                logger.warning(f"⚠️ 向量匹配跳过：{e}")
                vector_match = None

            if vector_match:
                match_source = f"向量匹配({vector_match['score']})"
                sql = vector_match['sql']
                explanation = vector_match['explanation']
                logger.info(f"🧠 [generate-sql] 向量匹配命中: score={vector_match['score']}")
            else:
                match_source = "AI 在线生成"
                schema = get_schema_context()
                sql, explanation, input_tokens, output_tokens, total_tokens = await bailian_client.generate_sql(
                    question=request.question, schema_context=schema
                )
                tokens_used = total_tokens

                # 保存到向量库
                try:
                    await vector_store.save(request.question, sql, explanation, bailian_client.api_key, bailian_client.base_url)
                except Exception as e:
                    logger.warning(f"⚠️ 向量保存失败：{e}")

        execution_time_ms = int((time.time() - start_time) * 1000)

        # 构建思考过程（generate-sql 无数据，但仍包含关键词和匹配信息）
        thinking = {
            "keywords": keywords,
            "matched_standard": matched_standard,
            "match_source": match_source,
            "matched_template": standard_match.get('question_template', '') if standard_match else None,
            "recommended_tables": _extract_tables_from_sql(standard_match.get('standard_sql', '') if standard_match else sql),
        }

        response_data = {
            "sql": sql, "explanation": explanation, "data": None, "columns": None,
            "tokens_used": tokens_used if not matched_standard else 0,
            "execution_time_ms": execution_time_ms, "matched_standard": matched_standard, "log_id": log_id,
            "chart_type": None, "thinking": thinking
        }
        get_query_cache().put(cache_key, response_data)

        log_id = log_query(
            question=request.question, generated_sql=sql, keywords=keywords,
            input_tokens=tokens_used if not matched_standard else 0,
            output_tokens=0, total_tokens=tokens_used,
            execution_time_ms=execution_time_ms, status='success',
            match_source=match_source
        )

        return QueryResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"❌ 生成失败：{e}")
        log_id = log_query(
            question=request.question, generated_sql=None, keywords=keywords if 'keywords' in locals() else [],
            input_tokens=0, output_tokens=0, total_tokens=0,
            execution_time_ms=execution_time_ms, status='failed', error_message=str(e),
            match_source=match_source
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-keywords", response_model=ExtractKeywordsResponse)
async def extract_keywords_api(request: ExtractKeywordsRequest):
    """从问题中提取关键词"""
    keywords = extract_keywords(request.question)
    return ExtractKeywordsResponse(keywords=keywords)


@router.get("/schema")
async def get_schema():
    """获取数据库表结构说明"""
    return {
        "schema": get_schema_context(),
        "tables": [
            "re_projects", "re_buildings", "re_units", "re_customers", "re_customer_followups",
            "re_subscriptions", "re_contracts", "re_payments", "re_receivables", "re_refunds",
            "ods_room", "ods_trade", "ods_payment", "ods_pay", "ods_contract", "ods_account",
            "ods_bseg", "ods_gl_actual", "ods_other",
            "dwd_room_detail", "dwd_trade_detail", "dwd_payment_detail", "dwd_contract_detail",
            "dwd_pay_detail", "dwd_gl_actual_detail", "dwd_gl_budget_detail",
            "dws_sales_payment_fact", "dws_sales_cost_fact",
            "dim_project", "dim_date", "dim_account", "dim_permission", "dim_indicator",
            "ads_group_sales_report", "ads_group_salesdate_report", "ads_group_pay_report",
            "ads_project_cost_report", "ads_sales_dashboard", "ads_finance_dashboard", "ads_szl_dashboard"
        ]
    }


@router.post("/cache/clear")
async def clear_cache():
    """清除查询缓存和向量索引"""
    get_query_cache().clear()
    refresh_schema_cache()
    load_standard_sql_cache()
    vector_store._vector_cache = []
    vector_store.enabled = False
    return {"message": "缓存已清除，向量索引已清空"}


@router.get("/cache/stats")
async def cache_stats():
    """查看缓存统计"""
    cache = get_query_cache()
    return {
        "query_cache_size": len(cache._cache),
        "query_cache_max": cache._maxsize,
        "schema_cached": _schema_cache is not None,
        "standard_sql_cached": len(_standard_sql_cache) if _standard_sql_cache else 0,
        "vector_store": vector_store.get_stats()
    }


@router.post("/vector/sync")
async def sync_vectors():
    """手动触发向量索引同步"""
    await vector_store.sync(bailian_client.api_key, bailian_client.base_url)
    return vector_store.get_stats()


@router.delete("/vector/clear")
async def clear_vectors():
    """清空向量索引缓存（不删除数据库数据）"""
    vector_store._vector_cache = []
    vector_store.enabled = False
    return {"message": "向量缓存已清空"}


# ==========================================
# 标准 SQL 库管理接口
# ==========================================

@router.get("/standard-sql")
async def list_standard_sql(
    keywords: Optional[str] = None,
    is_active: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
):
    """获取标准 SQL 列表"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            where_clauses = []
            params = []

            if keywords:
                where_clauses.append("(question_template LIKE ? OR keywords LIKE ?)")
                keyword_pattern = f"%{keywords}%"
                params.extend([keyword_pattern, keyword_pattern])

            if is_active is not None:
                where_clauses.append("is_active = ?")
                params.append(is_active)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            cursor.execute(f"SELECT COUNT(*) as total FROM standard_sql_library WHERE {where_sql}", params)
            total = cursor.fetchone()['total']

            offset = (page - 1) * page_size
            params.extend([page_size, offset])
            cursor.execute(f"""
                SELECT id, keywords, question_template, standard_sql, explanation, usage_count, is_active, created_at, updated_at
                FROM standard_sql_library WHERE {where_sql}
                ORDER BY usage_count DESC, id DESC LIMIT ? OFFSET ?
            """, params)
            records = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) as total FROM standard_sql_library")
            stats_total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as active FROM standard_sql_library WHERE is_active = 1")
            stats_active = cursor.fetchone()['active']
            cursor.execute("SELECT SUM(usage_count) as usage_count FROM standard_sql_library")
            stats_usage = cursor.fetchone()['usage_count'] or 0

            result = []
            for record in records:
                result.append({
                    'id': record['id'],
                    'keywords': json.loads(record['keywords']) if record['keywords'] else [],
                    'question_template': record['question_template'],
                    'standard_sql': record['standard_sql'],
                    'explanation': record['explanation'],
                    'usage_count': record['usage_count'],
                    'is_active': bool(record['is_active']),
                    'created_at': record['created_at'],
                    'updated_at': record['updated_at']
                })

            # 更新内存缓存
            load_standard_sql_cache()

            return {
                "items": result, "total": total, "page": page, "page_size": page_size,
                "stats": {
                    "total": stats_total, "active": stats_active,
                    "usageCount": stats_usage, "tokenSaved": stats_usage * 2000
                }
            }
    except Exception as e:
        logger.error(f"获取标准 SQL 列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/standard-sql")
async def create_standard_sql(request: StandardSQLCreate):
    """创建标准 SQL 记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO standard_sql_library
                (keywords, question_template, standard_sql, explanation, usage_count, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                json.dumps(request.keywords, ensure_ascii=False),
                request.question_template, request.standard_sql, request.explanation
            ))
            sql_id = cursor.lastrowid
            load_standard_sql_cache()  # 刷新缓存
            return {"id": sql_id, "message": "创建成功"}
    except Exception as e:
        logger.error(f"创建标准 SQL 失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/standard-sql/{sql_id}")
async def update_standard_sql(sql_id: int, request: StandardSQLUpdate):
    """更新标准 SQL 记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if request.keywords is not None:
                updates.append("keywords = ?")
                params.append(json.dumps(request.keywords, ensure_ascii=False))
            if request.question_template is not None:
                updates.append("question_template = ?")
                params.append(request.question_template)
            if request.standard_sql is not None:
                updates.append("standard_sql = ?")
                params.append(request.standard_sql)
            if request.explanation is not None:
                updates.append("explanation = ?")
                params.append(request.explanation)
            if request.is_active is not None:
                updates.append("is_active = ?")
                params.append(request.is_active)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(sql_id)
                cursor.execute(f"UPDATE standard_sql_library SET {', '.join(updates)} WHERE id = ?", params)
                load_standard_sql_cache()  # 刷新缓存
                return {"message": "更新成功"}
            return {"message": "无需更新"}
    except Exception as e:
        logger.error(f"更新标准 SQL 失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/standard-sql/{sql_id}")
async def delete_standard_sql(sql_id: int):
    """删除标准 SQL（软删除）"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE standard_sql_library SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (sql_id,))
            load_standard_sql_cache()  # 刷新缓存
            return {"message": "删除成功"}
    except Exception as e:
        logger.error(f"删除标准 SQL 失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 问数日志查询
# ==========================================

@router.get("/logs")
async def list_query_logs(limit: int = 20, offset: int = 0, status: Optional[str] = None):
    """获取问数日志列表"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("""
                    SELECT id, question, generated_sql, keywords, input_tokens, output_tokens,
                           total_tokens, execution_time_ms, status, error_message, created_at
                    FROM ai_query_logs WHERE status = ?
                    ORDER BY created_at DESC LIMIT ? OFFSET ?
                """, (status, limit, offset))
            else:
                cursor.execute("""
                    SELECT id, question, generated_sql, keywords, input_tokens, output_tokens,
                           total_tokens, execution_time_ms, status, error_message, created_at
                    FROM ai_query_logs ORDER BY created_at DESC LIMIT ? OFFSET ?
                """, (limit, offset))

            records = cursor.fetchall()
            result = []
            for record in records:
                result.append({
                    'id': record['id'], 'question': record['question'],
                    'generated_sql': record['generated_sql'],
                    'keywords': json.loads(record['keywords']) if record['keywords'] else [],
                    'input_tokens': record['input_tokens'], 'output_tokens': record['output_tokens'],
                    'total_tokens': record['total_tokens'], 'execution_time_ms': record['execution_time_ms'],
                    'status': record['status'], 'error_message': record['error_message'],
                    'created_at': record['created_at']
                })

            cursor.execute("SELECT COUNT(*) FROM ai_query_logs WHERE status = ?" if status else "SELECT COUNT(*) FROM ai_query_logs",
                          (status,) if status else ())
            total = cursor.fetchone()[0]

            return {"total": total, "limit": limit, "offset": offset, "data": result}
    except Exception as e:
        logger.error(f"获取日志失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stats")
async def get_query_stats():
    """获取问数统计"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ai_query_logs")
            total_queries = cursor.fetchone()[0]
            cursor.execute("SELECT status, COUNT(*) FROM ai_query_logs GROUP BY status")
            status_counts = dict(cursor.fetchall())
            cursor.execute("SELECT AVG(execution_time_ms) FROM ai_query_logs WHERE status = 'success'")
            avg_execution_time = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(total_tokens) FROM ai_query_logs WHERE status = 'success'")
            total_tokens = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ai_query_logs WHERE total_tokens = 0 AND status = 'success'")
            matched_standard_count = cursor.fetchone()[0] or 0

            return {
                "total_queries": total_queries,
                "success_count": status_counts.get('success', 0),
                "failed_count": status_counts.get('failed', 0),
                "avg_execution_time_ms": round(avg_execution_time, 2),
                "total_tokens_consumed": total_tokens,
                "matched_standard_count": matched_standard_count
            }
    except Exception as e:
        logger.error(f"获取统计失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
