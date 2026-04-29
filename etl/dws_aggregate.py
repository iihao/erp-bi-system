#!/usr/bin/env python3
"""
DWS 层数据聚合脚本
从 DWD 层读取明细数据，进行轻度聚合，生成汇总数据
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


class DWSAggregator:
    """DWS 层聚合器"""
    
    def __init__(self):
        self.db_url = os.getenv('DWD_DB_URL', 'mysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi_dwd')
        self.ods_db_url = os.getenv('ODS_DB_URL', 'mysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi_ods')
        self.engine = None
        self.ods_engine = None
    
    def create_engines(self):
        """创建数据库连接"""
        self.engine = create_engine(self.db_url)
        self.ods_engine = create_engine(self.ods_db_url)
        logger.info("数据库连接创建成功")
    
    def close_engines(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
        if self.ods_engine:
            self.ods_engine.dispose()
        logger.info("数据库连接已关闭")
    
    def aggregate_sales_daily(self):
        """按天聚合销售数据"""
        logger.info("开始执行销售日报聚合...")
        
        sql = """
        SELECT 
            DATE(order_date) as stat_date,
            customer_id,
            COUNT(DISTINCT order_id) as order_count,
            SUM(quantity) as total_quantity,
            SUM(subtotal) as total_amount,
            AVG(subtotal) as avg_order_value
        FROM dwd_sales_order_items
        GROUP BY DATE(order_date), customer_id
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('dws_sales_daily', self.engine, if_exists='replace', index=False)
        logger.info(f"销售日报聚合完成，共 {len(df)} 条记录")
        return df
    
    def aggregate_sales_monthly(self):
        """按月聚合销售数据"""
        logger.info("开始执行销售月报聚合...")
        
        sql = """
        SELECT 
            DATE_FORMAT(order_date, '%Y-%m') as stat_month,
            customer_id,
            COUNT(DISTINCT order_id) as order_count,
            SUM(quantity) as total_quantity,
            SUM(subtotal) as total_amount,
            AVG(subtotal) as avg_order_value
        FROM dwd_sales_order_items
        GROUP BY DATE_FORMAT(order_date, '%Y-%m'), customer_id
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('dws_sales_monthly', self.engine, if_exists='replace', index=False)
        logger.info(f"销售月报聚合完成，共 {len(df)} 条记录")
        return df
    
    def aggregate_product_sales(self):
        """按产品聚合销售数据"""
        logger.info("开始执行产品销售聚合...")
        
        sql = """
        SELECT 
            product_id,
            product_name,
            category,
            COUNT(DISTINCT order_id) as order_count,
            SUM(quantity) as total_quantity,
            SUM(subtotal) as total_amount,
            AVG(unit_price) as avg_price
        FROM dwd_sales_order_items
        GROUP BY product_id, product_name, category
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('dws_product_sales', self.engine, if_exists='replace', index=False)
        logger.info(f"产品销售聚合完成，共 {len(df)} 条记录")
        return df
    
    def aggregate_customer_stats(self):
        """按客户聚合统计数据"""
        logger.info("开始执行客户统计聚合...")
        
        sql = """
        SELECT 
            c.customer_id,
            c.customer_name,
            c.customer_type,
            c.industry,
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(o.final_amount) as total_amount,
            AVG(o.final_amount) as avg_order_value,
            MIN(o.order_date) as first_order_date,
            MAX(o.order_date) as last_order_date
        FROM dwd_sales_orders o
        JOIN dwd_customers c ON o.customer_id = c.customer_id
        GROUP BY c.customer_id, c.customer_name, c.customer_type, c.industry
        """
        
        df = pd.read_sql(sql, self.engine)
        df.to_sql('dws_customer_stats', self.engine, if_exists='replace', index=False)
        logger.info(f"客户统计聚合完成，共 {len(df)} 条记录")
        return df
    
    def run_all_aggregations(self):
        """执行所有聚合任务"""
        logger.info("=" * 50)
        logger.info("开始执行 DWS 层聚合任务")
        logger.info("=" * 50)
        
        try:
            self.create_engines()
            
            self.aggregate_sales_daily()
            self.aggregate_sales_monthly()
            self.aggregate_product_sales()
            self.aggregate_customer_stats()
            
            logger.info("=" * 50)
            logger.info("DWS 层聚合任务全部完成")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"DWS 聚合任务失败：{e}")
            raise
        finally:
            self.close_engines()


def run_dws_aggregate():
    """DWS 聚合入口函数"""
    aggregator = DWSAggregator()
    aggregator.run_all_aggregations()


if __name__ == '__main__':
    run_dws_aggregate()
