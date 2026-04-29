"""
DWS 层数据聚合器
从 DWD 层轻度聚合生成主题宽表和维度表
基于黄强论文 4.3.3 节：DWD 层→DWS 层聚合策略
"""
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging

from ..config import etl_config, get_config, layer_config
from ..utils import (
    mysql_connection, batch_insert, ETLMetrics, 
    retry_on_failure, get_date_range
)

logger = logging.getLogger(__name__)


class DWSAggregator:
    """DWS 层数据聚合器"""
    
    def __init__(self):
        self.config = get_config()
        self.dt = self.config.get_dt_str()
        self.metrics = ETLMetrics('DWS 数据聚合')
    
    def aggregate_all(self) -> bool:
        """
        执行完整的 DWS 层聚合
        
        Returns:
            bool: 是否成功
        """
        self.metrics.start()
        
        try:
            # 聚合各 DWS 层表和维度表
            self.aggregate_sales_payment_fact()
            self.aggregate_sales_cost_fact()
            self.build_dim_project()
            self.build_dim_date()
            self.build_dim_account()
            
            self.metrics.stop()
            return True
            
        except Exception as e:
            logger.error(f"❌ DWS 聚合失败：{e}")
            self.metrics.add_error(str(e))
            self.metrics.stop()
            return False
    
    @retry_on_failure()
    def aggregate_sales_payment_fact(self) -> int:
        """
        聚合销售 - 回款事实表
        基于黄强论文 4.3.3 节：销售与回款主题
        """
        logger.info("📊 开始聚合销售 - 回款事实表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            # 聚合逻辑：
            # 1. 以销售合同为主线
            # 2. LEFT JOIN 回款记录
            # 3. 按项目、合同、日期维度聚合
            # 4. 计算回款率等核心指标
            
            sql = f"""
                INSERT INTO dws_sales_payment_fact (
                    project_guid, project_name, contract_guid, customer_guid,
                    date_key, year, month, day,
                    contract_amount, payment_amount, payment_rate,
                    contract_count, payment_count,
                    data_version, dt
                )
                SELECT 
                    d.project_guid,
                    d.project_name,
                    d.contract_guid,
                    d.customer_guid,
                    DATE(d.contract_sign_date) as date_key,
                    YEAR(d.contract_sign_date) as year,
                    MONTH(d.contract_sign_date) as month,
                    DAY(d.contract_sign_date) as day,
                    SUM(COALESCE(d.total_price, 0)) as contract_amount,
                    COALESCE(SUM(p.payment_amount), 0) as payment_amount,
                    CASE 
                        WHEN SUM(COALESCE(d.total_price, 0)) > 0 
                        THEN ROUND(COALESCE(SUM(p.payment_amount), 0) * 100.0 / 
                             SUM(COALESCE(d.total_price, 0)), 2)
                        ELSE 0 
                    END as payment_rate,
                    COUNT(DISTINCT d.contract_guid) as contract_count,
                    COUNT(DISTINCT p.payment_guid) as payment_count,
                    CURDATE() as data_version,
                    %s as dt
                FROM dwd_trade_detail d
                LEFT JOIN dwd_payment_detail p 
                    ON d.contract_guid = p.contract_guid 
                    AND p.dt = %s
                WHERE d.dt = %s
                AND d.contract_guid IS NOT NULL
                GROUP BY 
                    d.project_guid, d.project_name, d.contract_guid, d.customer_guid,
                    DATE(d.contract_sign_date),
                    YEAR(d.contract_sign_date),
                    MONTH(d.contract_sign_date),
                    DAY(d.contract_sign_date)
                ON DUPLICATE KEY UPDATE
                    payment_amount = VALUES(payment_amount),
                    payment_rate = VALUES(payment_rate),
                    payment_count = VALUES(payment_count),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 聚合 {affected} 条销售 - 回款事实记录到 dws_sales_payment_fact")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def aggregate_sales_cost_fact(self) -> int:
        """
        聚合成本 - 费用事实表
        基于黄强论文 4.3.3 节：成本与费用主题
        """
        logger.info("📊 开始聚合成本 - 费用事实表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO dws_sales_cost_fact (
                    project_guid, project_name, contract_guid,
                    account_number, account_name, cost_center,
                    date_key, year, month, day,
                    contract_amount, cost_amount, fee_amount,
                    budget_amount, budget_variance, variance_rate,
                    data_version, dt
                )
                SELECT 
                    d.project_guid,
                    d.project_name,
                    d.contract_guid,
                    COALESCE(g.account_number, 'UNKNOWN') as account_number,
                    COALESCE(g.account_name, '未知科目') as account_name,
                    COALESCE(g.cost_center, 'UNKNOWN') as cost_center,
                    COALESCE(g.posting_date, CURDATE()) as date_key,
                    YEAR(COALESCE(g.posting_date, CURDATE())) as year,
                    MONTH(COALESCE(g.posting_date, CURDATE())) as month,
                    DAY(COALESCE(g.posting_date, CURDATE())) as day,
                    COALESCE(SUM(d.total_price), 0) as contract_amount,
                    COALESCE(SUM(CASE 
                        WHEN g.account_number LIKE '5%%' THEN g.local_amount 
                        ELSE 0 
                    END), 0) as cost_amount,
                    COALESCE(SUM(CASE 
                        WHEN g.account_number LIKE '6%%' THEN g.local_amount 
                        ELSE 0 
                    END), 0) as fee_amount,
                    COALESCE(SUM(b.budget_amount), 0) as budget_amount,
                    COALESCE(SUM(g.local_amount), 0) - COALESCE(SUM(b.budget_amount), 0) as budget_variance,
                    CASE 
                        WHEN COALESCE(SUM(b.budget_amount), 0) > 0 
                        THEN ROUND((COALESCE(SUM(g.local_amount), 0) - COALESCE(SUM(b.budget_amount), 0)) 
                             * 100.0 / SUM(b.budget_amount), 2)
                        ELSE 0 
                    END as variance_rate,
                    CURDATE() as data_version,
                    %s as dt
                FROM dwd_trade_detail d
                LEFT JOIN dwd_gl_actual_detail g 
                    ON d.project_guid = g.cost_center
                    AND g.dt = %s
                LEFT JOIN dwd_gl_budget_detail b 
                    ON g.account_number = b.account_number
                    AND g.fiscal_year = b.fiscal_year
                    AND b.dt = %s
                WHERE d.dt = %s
                GROUP BY 
                    d.project_guid, d.project_name, d.contract_guid,
                    g.account_number, g.account_name, g.cost_center,
                    COALESCE(g.posting_date, CURDATE()),
                    YEAR(COALESCE(g.posting_date, CURDATE())),
                    MONTH(COALESCE(g.posting_date, CURDATE())),
                    DAY(COALESCE(g.posting_date, CURDATE()))
                ON DUPLICATE KEY UPDATE
                    cost_amount = VALUES(cost_amount),
                    fee_amount = VALUES(fee_amount),
                    budget_variance = VALUES(budget_variance),
                    variance_rate = VALUES(variance_rate),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt, self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 聚合 {affected} 条成本 - 费用事实记录到 dws_sales_cost_fact")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def build_dim_project(self) -> int:
        """
        构建项目维度表
        """
        logger.info("📊 开始构建项目维度表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            # 从 ODS 层或业务表抽取项目维度
            sql = f"""
                INSERT INTO dim_project (
                    project_guid, project_code, project_name,
                    city, district, product_type, building_type,
                    total_area, total_units, developer,
                    property_management, start_date, expected_completion,
                    actual_completion, project_status, is_active, dt
                )
                SELECT DISTINCT
                    r.project_guid,
                    CONCAT('PRJ_', r.project_guid) as project_code,
                    COALESCE(r.project_name, '未知项目') as project_name,
                    '未知城市' as city,
                    '未知区域' as district,
                    '住宅' as product_type,
                    '高层' as building_type,
                    0 as total_area,
                    0 as total_units,
                    '未知开发商' as developer,
                    '未知物业' as property_management,
                    NULL as start_date,
                    NULL as expected_completion,
                    NULL as actual_completion,
                    COALESCE(r.room_status, 'unknown') as project_status,
                    1 as is_active,
                    %s as dt
                FROM ods_room r
                WHERE r.project_guid IS NOT NULL
                AND r.dt = %s
                ON DUPLICATE KEY UPDATE
                    project_name = VALUES(project_name),
                    project_status = VALUES(project_status),
                    dt = VALUES(dt)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 构建 {affected} 条项目维度记录")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def build_dim_date(self) -> int:
        """
        构建时间维度表
        预生成 10 年的日期维度数据
        """
        logger.info("📊 开始构建时间维度表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在数据
            cursor.execute("SELECT COUNT(*) as cnt FROM dim_date")
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            if count > 100:
                logger.info("⏭️  时间维度表已有数据，跳过生成")
                return 0
            
            # 生成 2020-2030 年的日期维度
            start_year = 2020
            end_year = 2030
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            
            values = []
            current_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            
            while current_date <= end_date:
                weekday = current_date.weekday()
                is_weekend = 1 if weekday >= 5 else 0
                
                # 简化节假日判断（实际应该查询节假日表）
                is_holiday = 0
                holiday_name = ''
                if current_date.month == 1 and current_date.day == 1:
                    is_holiday = 1
                    holiday_name = '元旦'
                elif current_date.month == 10 and current_date.day == 1:
                    is_holiday = 1
                    holiday_name = '国庆节'
                
                values.append((
                    current_date,  # date_key
                    current_date.year,
                    (current_date.month - 1) // 3 + 1,  # quarter
                    current_date.month,
                    current_date.day,
                    current_date.isocalendar()[1],  # week_of_year
                    weekday + 1,  # day_of_week (1=Monday)
                    day_names[weekday],
                    month_names[current_date.month - 1],
                    is_weekend,
                    is_holiday,
                    holiday_name,
                    current_date.year,  # fiscal_year (简化处理)
                    (current_date.month - 1) // 3 + 1,  # fiscal_quarter
                    current_date.month,  # fiscal_month
                    self.dt
                ))
                
                current_date += timedelta(days=1)
            
            # 批量插入
            insert_sql = """
                INSERT INTO dim_date (
                    date_key, year, quarter, month, day, week_of_year,
                    day_of_week, day_name, month_name, is_weekend, is_holiday,
                    holiday_name, fiscal_year, fiscal_quarter, fiscal_month, dt
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE dt = VALUES(dt)
            """
            
            cursor.executemany(insert_sql, values)
            conn.commit()
            
            logger.info(f"✅ 构建 {len(values)} 条时间维度记录（{start_year}-{end_year}）")
            self.metrics.add_records(len(values))
            return len(values)
    
    @retry_on_failure()
    def build_dim_account(self) -> int:
        """
        构建科目维度表
        """
        logger.info("📊 开始构建科目维度表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO dim_account (
                    account_guid, account_code, account_name, account_type,
                    parent_account_guid, parent_account_code, parent_account_name,
                    level, balance_direction, is_leaf, full_path, is_active, dt
                )
                SELECT 
                    a.account_guid,
                    a.account_code,
                    a.account_name,
                    COALESCE(a.account_type, '未知类型') as account_type,
                    a.parent_account_guid,
                    '' as parent_account_code,
                    '' as parent_account_name,
                    COALESCE(a.level, 1) as level,
                    COALESCE(a.balance_direction, '借') as balance_direction,
                    COALESCE(a.is_leaf, 1) as is_leaf,
                    a.account_name as full_path,
                    1 as is_active,
                    %s as dt
                FROM ods_account a
                WHERE a.account_guid IS NOT NULL
                AND a.dt = %s
                ON DUPLICATE KEY UPDATE
                    account_name = VALUES(account_name),
                    account_type = VALUES(account_type),
                    dt = VALUES(dt)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 构建 {affected} 条科目维度记录")
            self.metrics.add_records(affected)
            return affected
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取执行指标"""
        return self.metrics.get_summary()


def run_dws_aggregation() -> bool:
    """运行 DWS 层聚合"""
    aggregator = DWSAggregator()
    success = aggregator.aggregate_all()
    
    if success:
        logger.info("✅ DWS 层聚合完成")
    else:
        logger.error("❌ DWS 层聚合失败")
    
    return success


if __name__ == '__main__':
    run_dws_aggregation()
