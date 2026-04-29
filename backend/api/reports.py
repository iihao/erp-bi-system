from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/reports", tags=["报表管理"])

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """简单的 token 验证（实际项目应使用数据库验证）"""
    token = credentials.credentials
    if not token or len(token) < 10:
        raise HTTPException(status_code=401, detail="无效的 token")
    return {"user_id": "admin"}


# 响应模型
class SalesTrendResponse(BaseModel):
    """销售趋势响应"""
    month: str
    sales_amount: float
    order_count: int
    quantity: int


class ProductRankingResponse(BaseModel):
    """产品排行榜响应"""
    product_id: int
    product_name: str
    category: str
    total_amount: float
    total_quantity: int
    order_count: int
    sales_rank: int


class CategoryAnalysisResponse(BaseModel):
    """品类分析响应"""
    category: str
    product_count: int
    total_sales: float
    total_quantity: int
    avg_unit_price: float
    sales_ratio: float


class KpiSummaryResponse(BaseModel):
    """KPI 汇总响应"""
    kpi_name: str
    kpi_value: float
    unit: str


class CustomerAnalysisResponse(BaseModel):
    """客户分析响应"""
    customer_type: str
    industry: str
    customer_count: int
    total_orders: int
    total_amount: float
    avg_order_value: float


# 模拟数据生成器
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


@router.get("/sales/trend", response_model=List[SalesTrendResponse])
async def get_sales_trend(
    months: int = Query(default=12, ge=1, le=24, description="查询月数"),
    current_user: dict = Depends(get_current_user)
):
    """获取销售趋势数据"""
    data = generate_sales_trend_data(months)
    return data


@router.get("/sales/product-ranking", response_model=List[ProductRankingResponse])
async def get_product_ranking(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    current_user: dict = Depends(get_current_user)
):
    """获取产品销售排行榜"""
    data = generate_product_ranking_data(limit)
    return data


@router.get("/sales/category-analysis", response_model=List[CategoryAnalysisResponse])
async def get_category_analysis(
    current_user: dict = Depends(get_current_user)
):
    """获取品类分析数据"""
    data = generate_category_analysis_data()
    return data


@router.get("/sales/kpi-summary", response_model=List[KpiSummaryResponse])
async def get_kpi_summary(
    current_user: dict = Depends(get_current_user)
):
    """获取 KPI 汇总指标"""
    data = generate_kpi_summary_data()
    return data


@router.get("/customer/analysis", response_model=List[CustomerAnalysisResponse])
async def get_customer_analysis(
    current_user: dict = Depends(get_current_user)
):
    """获取客户分析数据"""
    data = generate_customer_analysis_data()
    return data


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_user)
):
    """获取仪表板概览数据（综合所有指标）"""
    return {
        "kpi_summary": generate_kpi_summary_data(),
        "sales_trend": generate_sales_trend_data(6),
        "product_ranking": generate_product_ranking_data(5),
        "category_distribution": generate_category_analysis_data()
    }
