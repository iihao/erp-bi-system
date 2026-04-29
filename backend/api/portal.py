"""
前台报表 API
为普通用户提供只读报表数据，基于角色权限控制
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/portal", tags=["前台报表"])

security = HTTPBearer()

# 角色 ID 定义
ROLE_SUPER_ADMIN = 1      # 超级管理员 - 所有报表
ROLE_DATA_ANALYST = 2     # 数据分析师 - 分析类报表
ROLE_NORMAL_USER = 3      # 普通用户 - 基础报表

# 报表权限配置
REPORT_PERMISSIONS = {
    "sales-overview": [ROLE_SUPER_ADMIN, ROLE_DATA_ANALYST, ROLE_NORMAL_USER],      # 销售概览
    "sales-trend": [ROLE_SUPER_ADMIN, ROLE_DATA_ANALYST, ROLE_NORMAL_USER],         # 销售趋势
    "product-ranking": [ROLE_SUPER_ADMIN, ROLE_DATA_ANALYST, ROLE_NORMAL_USER],     # 产品排行
    "category-analysis": [ROLE_SUPER_ADMIN, ROLE_DATA_ANALYST, ROLE_NORMAL_USER],   # 品类分析
    "customer-analysis": [ROLE_SUPER_ADMIN, ROLE_DATA_ANALYST],                     # 客户分析
    "profit-analysis": [ROLE_SUPER_ADMIN, ROLE_DATA_ANALYST],                       # 利润分析
    "inventory-report": [ROLE_SUPER_ADMIN, ROLE_DATA_ANALYST],                      # 库存报表
    "forecast-report": [ROLE_SUPER_ADMIN],                                          # 预测报表
}

# 报表分类
REPORT_CATEGORIES = {
    "basic": ["sales-overview", "sales-trend", "product-ranking", "category-analysis"],  # 基础报表
    "analysis": ["customer-analysis", "profit-analysis", "inventory-report"],             # 分析报表
    "advanced": ["forecast-report"],                                                       # 高级报表
}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 token 并获取用户信息"""
    from api.auth import decode_token
    token = credentials.credentials
    if not token or len(token) < 10:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        return {"user_id": user_id, "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


def get_user_role(user_id: str) -> int:
    """获取用户角色 ID"""
    from api.database import execute_query
    sql = "SELECT role_id FROM users WHERE user_id = ?"
    result = execute_query(sql, (user_id,))
    if result:
        return result[0].get("role_id", ROLE_NORMAL_USER)
    return ROLE_NORMAL_USER


def check_report_permission(user_role: int, report_id: str) -> bool:
    """检查用户是否有报表访问权限"""
    allowed_roles = REPORT_PERMISSIONS.get(report_id, [])
    return user_role in allowed_roles


def get_accessible_reports(user_role: int) -> List[Dict[str, Any]]:
    """获取用户可访问的报表列表"""
    reports = []
    for report_id, allowed_roles in REPORT_PERMISSIONS.items():
        if user_role in allowed_roles:
            # 确定报表分类
            category = "basic"
            for cat, report_ids in REPORT_CATEGORIES.items():
                if report_id in report_ids:
                    category = cat
                    break

            reports.append({
                "report_id": report_id,
                "report_name": get_report_name(report_id),
                "category": category,
                "description": get_report_description(report_id),
            })
    return reports


def get_report_name(report_id: str) -> str:
    """获取报表名称"""
    names = {
        "sales-overview": "销售概览",
        "sales-trend": "销售趋势",
        "product-ranking": "产品排行",
        "category-analysis": "品类分析",
        "customer-analysis": "客户分析",
        "profit-analysis": "利润分析",
        "inventory-report": "库存报表",
        "forecast-report": "预测报表",
    }
    return names.get(report_id, report_id)


def get_report_description(report_id: str) -> str:
    """获取报表描述"""
    descriptions = {
        "sales-overview": "核心销售指标概览，包括销售额、订单数、销售量等关键指标",
        "sales-trend": "销售趋势分析，展示近 12 个月的销售变化情况",
        "product-ranking": "产品销量排行榜，Top 50 产品销售额排名",
        "category-analysis": "品类销售分析，各品类销售占比和趋势",
        "customer-analysis": "客户分析报表，客户类型、行业分布及价值分析",
        "profit-analysis": "利润分析报表，毛利率、净利率等利润指标",
        "inventory-report": "库存报表，库存周转率、滞销商品分析",
        "forecast-report": "销售预测报表，基于历史数据的智能预测",
    }
    return descriptions.get(report_id, "")


# ===========================================
# 响应模型
# ===========================================

class ReportInfo(BaseModel):
    """报表信息"""
    report_id: str
    report_name: str
    category: str
    description: str


class KpiItem(BaseModel):
    """KPI 指标项"""
    kpi_name: str
    kpi_value: float
    unit: str


class SalesTrendItem(BaseModel):
    """销售趋势项"""
    month: str
    sales_amount: float
    order_count: int
    quantity: int


class ProductRankingItem(BaseModel):
    """产品排行项"""
    product_id: int
    product_name: str
    category: str
    total_amount: float
    total_quantity: int
    order_count: int
    sales_rank: int


class CategoryAnalysisItem(BaseModel):
    """品类分析项"""
    category: str
    product_count: int
    total_sales: float
    total_quantity: int
    avg_unit_price: float
    sales_ratio: float


class ReportDataResponse(BaseModel):
    """报表数据响应"""
    report_id: str
    report_name: str
    data: Dict[str, Any]
    updated_at: str


# ===========================================
# 模拟数据生成器
# ===========================================

def generate_sales_trend_data(months: int = 12) -> List[Dict[str, Any]]:
    """生成销售趋势模拟数据"""
    now = datetime.now()
    data = []
    for i in range(months, 0, -1):
        date = now - timedelta(days=i*30)
        month_str = date.strftime("%Y-%m")
        data.append({
            "month": month_str,
            "sales_amount": round(random.uniform(500000, 1500000), 2),
            "order_count": random.randint(1500, 3000),
            "quantity": random.randint(5000, 15000)
        })
    return data


def generate_product_ranking_data(limit: int = 10) -> List[Dict[str, Any]]:
    """生成产品排行榜模拟数据"""
    products = [
        ("iPhone 15 Pro", "手机"),
        ("MacBook Pro 14", "笔记本"),
        ("iPad Air", "平板"),
        ("AirPods Pro", "耳机"),
        ("Apple Watch", "手表"),
        ("iMac 24", "台式机"),
        ("Mac mini", "台式机"),
        ("HomePod", "音响"),
        ("Magic Keyboard", "配件"),
        ("Magic Mouse", "配件"),
    ]
    data = []
    for i, (name, category) in enumerate(products[:limit], 1):
        data.append({
            "product_id": i,
            "product_name": name,
            "category": category,
            "total_amount": round(random.uniform(100000, 800000), 2),
            "total_quantity": random.randint(500, 5000),
            "order_count": random.randint(200, 2000),
            "sales_rank": i
        })
    return data


def generate_category_analysis_data() -> List[Dict[str, Any]]:
    """生成品类分析模拟数据"""
    categories = [
        ("手机", 15, 0.35),
        ("笔记本", 8, 0.25),
        ("平板", 10, 0.15),
        ("耳机", 20, 0.10),
        ("手表", 12, 0.08),
        ("台式机", 5, 0.05),
        ("配件", 30, 0.02),
    ]
    total_sales = 5000000
    data = []
    for name, count, ratio in categories:
        sales = total_sales * ratio
        data.append({
            "category": name,
            "product_count": count,
            "total_sales": round(sales, 2),
            "total_quantity": random.randint(1000, 10000),
            "avg_unit_price": round(sales / random.randint(1000, 10000), 2),
            "sales_ratio": round(ratio * 100, 2)
        })
    return data


def generate_kpi_summary_data() -> List[Dict[str, Any]]:
    """生成 KPI 汇总模拟数据"""
    return [
        {"kpi_name": "总销售额", "kpi_value": 5234567.89, "unit": "元"},
        {"kpi_name": "总订单数", "kpi_value": 23456, "unit": "单"},
        {"kpi_name": "总销售量", "kpi_value": 89012, "unit": "件"},
        {"kpi_name": "产品种类数", "kpi_value": 156, "unit": "种"},
        {"kpi_name": "客户总数", "kpi_value": 3456, "unit": "个"},
        {"kpi_name": "平均客单价", "kpi_value": 2231.45, "unit": "元"},
    ]


def generate_real_estate_summary_data() -> Dict[str, Any]:
    """生成地产经营汇总数据"""
    from api.database import execute_query

    def first_value(sql: str, default: float = 0.0) -> float:
        result = execute_query(sql)
        if not result:
            return default
        value = result[0].get("total")
        return float(value or default)

    total_projects = int(first_value("SELECT COUNT(*) as total FROM re_projects", 0))
    total_units = int(first_value("SELECT COUNT(*) as total FROM re_units", 0))
    total_subscriptions = int(first_value("SELECT COUNT(*) as total FROM re_subscriptions", 0))
    total_contracts = int(first_value("SELECT COUNT(*) as total FROM re_contracts WHERE contract_status != 'cancelled'", 0))
    total_sales = first_value("SELECT COALESCE(SUM(total_price), 0) as total FROM re_contracts WHERE contract_status != 'cancelled'")
    total_received = first_value("SELECT COALESCE(SUM(amount), 0) as total FROM re_payments")
    total_receivables = first_value("SELECT COALESCE(SUM(balance), 0) as total FROM re_receivables")

    total_cost = first_value("SELECT COALESCE(SUM(actual_amount), 0) as total FROM ads_project_cost_report")
    if total_cost == 0:
        total_cost = first_value("SELECT COALESCE(SUM(cost_amount), 0) as total FROM dws_sales_cost_fact")

    total_expense = first_value("SELECT COALESCE(SUM(total_cost), 0) as total FROM ads_finance_dashboard")
    if total_expense == 0:
        total_expense = first_value("SELECT COALESCE(SUM(fee_amount), 0) as total FROM dws_sales_cost_fact")

    total_profit = first_value("SELECT COALESCE(SUM(total_profit), 0) as total FROM ads_finance_dashboard")
    if total_profit == 0 and total_sales:
        total_profit = total_sales - total_cost - total_expense

    return {
        "total_projects": total_projects,
        "total_units": total_units,
        "total_subscriptions": total_subscriptions,
        "total_contracts": total_contracts,
        "total_sales": round(total_sales, 2),
        "total_received": round(total_received, 2),
        "total_receivables": round(total_receivables, 2),
        "total_cost": round(total_cost, 2),
        "total_expense": round(total_expense, 2),
        "total_profit": round(total_profit, 2),
        "subscription_rate": round(total_contracts * 100.0 / total_subscriptions, 2) if total_subscriptions else 0,
        "collection_rate": round(total_received * 100.0 / total_sales, 2) if total_sales else 0,
        "cost_ratio": round(total_cost * 100.0 / total_sales, 2) if total_sales else 0,
        "expense_ratio": round(total_expense * 100.0 / total_sales, 2) if total_sales else 0,
        "profit_margin": round(total_profit * 100.0 / total_sales, 2) if total_sales else 0,
    }


def generate_real_estate_trend_data(months: int = 6) -> List[Dict[str, Any]]:
    """生成地产经营趋势数据"""
    from api.database import execute_query

    sql = """
        WITH monthly_data AS (
            SELECT
                strftime('%Y-%m', c.contract_date) as month,
                COALESCE(SUM(c.total_price), 0) as sales_amount,
                COUNT(DISTINCT c.contract_id) as contract_count,
                COALESCE(SUM(COALESCE(pay.total_paid, 0)), 0) as received_amount
            FROM re_contracts c
            LEFT JOIN (
                SELECT contract_id, SUM(amount) as total_paid
                FROM re_payments
                GROUP BY contract_id
            ) pay ON c.contract_id = pay.contract_id
            WHERE c.contract_status != 'cancelled'
              AND c.contract_date IS NOT NULL
            GROUP BY strftime('%Y-%m', c.contract_date)
            ORDER BY month DESC
            LIMIT ?
        )
        SELECT * FROM monthly_data
        ORDER BY month ASC
    """
    result = execute_query(sql, (months,))
    return [dict(row) for row in result]


def generate_real_estate_ranking_data(limit: int = 5) -> List[Dict[str, Any]]:
    """生成地产项目销售排行"""
    from api.database import execute_query

    sql = """
        SELECT
            p.project_name,
            p.city,
            COUNT(DISTINCT c.contract_id) as contract_count,
            COUNT(DISTINCT u.unit_id) as total_units,
            COALESCE(SUM(c.total_price), 0) as total_sales,
            ROUND(
                COUNT(DISTINCT c.contract_id) * 100.0 / NULLIF(COUNT(DISTINCT u.unit_id), 0), 2
            ) as sell_through_rate
        FROM re_projects p
        LEFT JOIN re_buildings b ON p.project_id = b.project_id
        LEFT JOIN re_units u ON b.building_id = u.building_id
        LEFT JOIN re_contracts c ON u.unit_id = c.unit_id AND c.contract_status != 'cancelled'
        GROUP BY p.project_id, p.project_name, p.city
        ORDER BY total_sales DESC
        LIMIT ?
    """
    result = execute_query(sql, (limit,))
    return [dict(row) for row in result]


def generate_real_estate_payment_structure_data(limit: int = 6) -> List[Dict[str, Any]]:
    """生成地产回款结构数据"""
    from api.database import execute_query

    sql = """
        SELECT
            COALESCE(payment_method, '未分类') as name,
            COALESCE(SUM(amount), 0) as value
        FROM re_payments
        GROUP BY COALESCE(payment_method, '未分类')
        ORDER BY value DESC
        LIMIT ?
    """
    result = execute_query(sql, (limit,))
    return [dict(row) for row in result]


def generate_customer_analysis_data() -> List[Dict[str, Any]]:
    """生成客户分析模拟数据"""
    customer_types = ["企业客户", "个人客户", "政府客户"]
    industries = ["科技", "金融", "教育", "医疗", "制造"]
    data = []
    for ctype in customer_types:
        for industry in industries:
            data.append({
                "customer_type": ctype,
                "industry": industry,
                "customer_count": random.randint(50, 500),
                "total_orders": random.randint(100, 2000),
                "total_amount": round(random.uniform(100000, 2000000), 2),
                "avg_order_value": round(random.uniform(1000, 5000), 2)
            })
    return sorted(data, key=lambda x: x["total_amount"], reverse=True)


def generate_profit_analysis_data() -> List[Dict[str, Any]]:
    """生成利润分析模拟数据"""
    return [
        {"month": "2025-01", "gross_profit": 1250000, "net_profit": 520000, "gross_margin": 25.5, "net_margin": 10.6},
        {"month": "2025-02", "gross_profit": 1380000, "net_profit": 580000, "gross_margin": 26.2, "net_margin": 11.0},
        {"month": "2025-03", "gross_profit": 1420000, "net_profit": 610000, "gross_margin": 25.8, "net_margin": 11.1},
        {"month": "2025-04", "gross_profit": 1510000, "net_profit": 650000, "gross_margin": 26.5, "net_margin": 11.4},
        {"month": "2025-05", "gross_profit": 1620000, "net_profit": 720000, "gross_margin": 27.1, "net_margin": 12.1},
        {"month": "2025-06", "gross_profit": 1580000, "net_profit": 680000, "gross_margin": 26.3, "net_margin": 11.3},
    ]


def generate_inventory_report_data() -> List[Dict[str, Any]]:
    """生成库存报表模拟数据"""
    return [
        {"category": "手机", "stock_quantity": 5000, "stock_value": 25000000, "turnover_rate": 8.5, "slow_items": 12},
        {"category": "笔记本", "stock_quantity": 1200, "stock_value": 15000000, "turnover_rate": 6.2, "slow_items": 8},
        {"category": "平板", "stock_quantity": 2500, "stock_value": 8000000, "turnover_rate": 7.1, "slow_items": 5},
        {"category": "配件", "stock_quantity": 15000, "stock_value": 3000000, "turnover_rate": 4.8, "slow_items": 25},
    ]


def generate_forecast_data() -> List[Dict[str, Any]]:
    """生成预测报表模拟数据"""
    now = datetime.now()
    data = []
    for i in range(1, 7):
        date = now + timedelta(days=i*30)
        month_str = date.strftime("%Y-%m")
        data.append({
            "month": month_str,
            "predicted_sales": round(random.uniform(1200000, 1800000), 2),
            "confidence_interval_low": round(random.uniform(1000000, 1400000), 2),
            "confidence_interval_high": round(random.uniform(1600000, 2000000), 2),
        })
    return data


# ===========================================
# API 接口
# ===========================================

@router.get("/reports", response_model=List[ReportInfo])
async def get_reports_list(
    current_user: dict = Depends(get_current_user)
):
    """获取用户可访问的报表列表"""
    from api.database import execute_query
    user_id = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    user_role = get_user_role(user_id)

    reports = get_accessible_reports(user_role)
    return reports


@router.get("/report/{report_id}")
async def get_report_data(
    report_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="返回数量"),
    months: int = Query(default=12, ge=1, le=24, description="查询月数"),
    current_user: dict = Depends(get_current_user)
):
    """获取单个报表数据"""
    user_id = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    user_role = get_user_role(user_id)

    # 检查权限
    if not check_report_permission(user_role, report_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您没有权限访问该报表"
        )

    # 根据报表 ID 生成对应数据
    data = {}
    if report_id == "sales-overview":
        data["kpi"] = generate_kpi_summary_data()
        data["summary"] = {
            "total_sales": 5234567.89,
            "total_orders": 23456,
            "total_quantity": 89012,
            "avg_order_value": 223.15
        }
    elif report_id == "sales-trend":
        data["trend"] = generate_sales_trend_data(months)
    elif report_id == "product-ranking":
        data["ranking"] = generate_product_ranking_data(limit)
    elif report_id == "category-analysis":
        data["categories"] = generate_category_analysis_data()
    elif report_id == "customer-analysis":
        data["customers"] = generate_customer_analysis_data()
    elif report_id == "profit-analysis":
        data["profit"] = generate_profit_analysis_data()
    elif report_id == "inventory-report":
        data["inventory"] = generate_inventory_report_data()
    elif report_id == "forecast-report":
        data["forecast"] = generate_forecast_data()
    else:
        raise HTTPException(status_code=404, detail="报表不存在")

    return {
        "report_id": report_id,
        "report_name": get_report_name(report_id),
        "data": data,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@router.get("/kpi", response_model=List[KpiItem])
async def get_kpi(
    current_user: dict = Depends(get_current_user)
):
    """获取 KPI 指标"""
    return generate_kpi_summary_data()


@router.get("/sales-trend", response_model=List[SalesTrendItem])
async def get_sales_trend(
    months: int = Query(default=12, ge=1, le=24, description="查询月数"),
    current_user: dict = Depends(get_current_user)
):
    """获取销售趋势数据"""
    user_id = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    user_role = get_user_role(user_id)

    if not check_report_permission(user_role, "sales-trend"):
        raise HTTPException(status_code=403, detail="您没有权限访问该报表")

    return generate_sales_trend_data(months)


@router.get("/product-ranking", response_model=List[ProductRankingItem])
async def get_product_ranking(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    current_user: dict = Depends(get_current_user)
):
    """获取产品销量排行榜"""
    user_id = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    user_role = get_user_role(user_id)

    if not check_report_permission(user_role, "product-ranking"):
        raise HTTPException(status_code=403, detail="您没有权限访问该报表")

    return generate_product_ranking_data(limit)


@router.get("/category-analysis", response_model=List[CategoryAnalysisItem])
async def get_category_analysis(
    current_user: dict = Depends(get_current_user)
):
    """获取品类分析数据"""
    user_id = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    user_role = get_user_role(user_id)

    if not check_report_permission(user_role, "category-analysis"):
        raise HTTPException(status_code=403, detail="您没有权限访问该报表")

    return generate_category_analysis_data()


@router.get("/overview")
async def get_portal_overview(
    current_user: dict = Depends(get_current_user)
):
    """获取前台概览数据（用于 Dashboard）"""
    user_id = current_user.get("user_id") or current_user.get("payload", {}).get("sub")
    user_role = get_user_role(user_id)

    overview = {
        "real_estate_summary": generate_real_estate_summary_data(),
        "real_estate_trend": generate_real_estate_trend_data(6),
        "real_estate_ranking": generate_real_estate_ranking_data(5),
        "real_estate_payment_structure": generate_real_estate_payment_structure_data(),
        "user_role": user_role,
        "accessible_reports": get_accessible_reports(user_role)
    }

    # 根据角色添加额外数据
    if check_report_permission(user_role, "customer-analysis"):
        overview["customer_summary"] = generate_customer_analysis_data()[:3]

    if check_report_permission(user_role, "profit-analysis"):
        overview["profit_summary"] = generate_profit_analysis_data()[-3:]

    if check_report_permission(user_role, "forecast-report"):
        overview["forecast_summary"] = generate_forecast_data()[:3]

    return overview
