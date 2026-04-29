#!/usr/bin/env python3
"""
ADS 层报表指标计算脚本
从 DWS 层读取聚合数据，生成面向应用的报表指标
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ADSReportGenerator:
    """ADS 层报表生成器"""
    
    def __init__(self):
        self.dws_db_url = os.getenv('DWS_DB_URL', 'mysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi_dws')
        self.ads_db_url = os.getenv('ADS_DB_URL', 'mysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi_ads')
        self.engine = None
        self.ads_engine = None
    
    def create_engines(self):
        """创建数据库连接"""
        self.engine = create_engine(self.dws_db_url)
        self.ads_engine = create_engine(self.ads_db_url)
        logger.info("数据库连接创建成功")
    
    def close_engines(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
        if self.ads_engine:
            self.ads_engine.dispose()
        logger.info("数据库连接已关闭")
    
    def generate_sales_dashboard(self):
        """生成销售大屏指标"""
        logger.info("开始生成销售大屏指标...")
        
        sql = """
        SELECT 
            stat_month,
            SUM(total_amount) as monthly_sales,
            SUM(order_count) as monthly_orders,
            SUM(total_quantity) as monthly_quantity,
            AVG(avg_order_value) as avg_order_value
        FROM dws_sales_monthly
        GROUP BY stat_month
        ORDER BY stat_month DESC
        LIMIT 12
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('ads_sales_dashboard', self.ads_engine, if_exists='replace', index=False)
        logger.info(f"销售大屏指标生成完成，共 {len(df)} 条记录")
        return df
    
    def generate_product_ranking(self):
        """生成产品排行榜"""
        logger.info("开始生成产品排行榜...")
        
        sql = """
        SELECT 
            product_id,
            product_name,
            category,
            total_amount,
            total_quantity,
            order_count,
            avg_price,
            RANK() OVER (ORDER BY total_amount DESC) as sales_rank
        FROM dws_product_sales
        ORDER BY total_amount DESC
        LIMIT 50
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('ads_product_ranking', self.ads_engine, if_exists='replace', index=False)
        logger.info(f"产品排行榜生成完成，共 {len(df)} 条记录")
        return df
    
    def generate_customer_analysis(self):
        """生成客户分析报表"""
        logger.info("开始生成客户分析报表...")
        
        sql = """
        SELECT 
            customer_type,
            industry,
            COUNT(*) as customer_count,
            SUM(total_orders) as total_orders,
            SUM(total_amount) as total_amount,
            AVG(avg_order_value) as avg_order_value
        FROM dws_customer_stats
        GROUP BY customer_type, industry
        ORDER BY total_amount DESC
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('ads_customer_analysis', self.ads_engine, if_exists='replace', index=False)
        logger.info(f"客户分析报表生成完成，共 {len(df)} 条记录")
        return df
    
    def generate_kpi_summary(self):
        """生成 KPI 汇总指标"""
        logger.info("开始生成 KPI 汇总指标...")
        
        sql = """
        SELECT 
            '总销售额' as kpi_name, SUM(total_amount) as kpi_value, '元' as unit FROM dws_product_sales
        UNION ALL
        SELECT 
            '总订单数', SUM(order_count), '单' FROM dws_product_sales
        UNION ALL
        SELECT 
            '总销售量', SUM(total_quantity), '件' FROM dws_product_sales
        UNION ALL
        SELECT 
            '产品种类数', COUNT(*), '种' FROM dws_product_sales
        UNION ALL
        SELECT 
            '客户总数', COUNT(DISTINCT customer_id), '个' FROM dws_customer_stats
        UNION ALL
        SELECT 
            '平均客单价', AVG(total_amount), '元' FROM dws_customer_stats
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('ads_kpi_summary', self.ads_engine, if_exists='replace', index=False)
        logger.info(f"KPI 汇总指标生成完成，共 {len(df)} 条记录")
        return df
    
    def generate_category_analysis(self):
        """生成品类分析报表"""
        logger.info("开始生成品类分析报表...")
        
        sql = """
        SELECT 
            category,
            COUNT(*) as product_count,
            SUM(total_amount) as total_sales,
            SUM(total_quantity) as total_quantity,
            SUM(total_amount) / SUM(total_quantity) as avg_unit_price,
            ROUND(SUM(total_amount) * 100.0 / (SELECT SUM(total_amount) FROM dws_product_sales), 2) as sales_ratio
        FROM dws_product_sales
        GROUP BY category
        ORDER BY total_sales DESC
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('ads_category_analysis', self.ads_engine, if_exists='replace', index=False)
        logger.info(f"品类分析报表生成完成，共 {len(df)} 条记录")
        return df
    
    def run_all_reports(self):
        """执行所有报表生成任务"""
        logger.info("=" * 50)
        logger.info("开始执行 ADS 层报表生成任务")
        logger.info("=" * 50)
        
        try:
            self.create_engines()
            
            self.generate_sales_dashboard()
            self.generate_product_ranking()
            self.generate_customer_analysis()
            self.generate_kpi_summary()
            self.generate_category_analysis()
            
            logger.info("=" * 50)
            logger.info("ADS 层报表生成任务全部完成")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"ADS 报表生成任务失败：{e}")
            raise
        finally:
            self.close_engines()


def run_ads_report():
    """ADS 报表入口函数"""
    generator = ADSReportGenerator()
    generator.run_all_reports()


if __name__ == '__main__':
    run_ads_report()
