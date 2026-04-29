"""
ADS 层报表加载器
从 DWS 层聚合生成面向应用的报表数据
基于黄强论文 4.3.4 节：DWS 层→ADS 层报表生成策略
"""
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging

from ..config import etl_config, get_config, layer_config
from ..utils import (
    mysql_connection, batch_insert, ETLMetrics, 
    retry_on_failure
)

logger = logging.getLogger(__name__)


class ADSLoader:
    """ADS 层报表加载器"""
    
    def __init__(self):
        self.config = get_config()
        self.dt = self.config.get_dt_str()
        self.metrics = ETLMetrics('ADS 报表生成')
    
    def load_all(self) -> bool:
        """
        执行完整的 ADS 层报表生成
        
        Returns:
            bool: 是否成功
        """
        self.metrics.start()
        
        try:
            # 生成各 ADS 层报表
            self.load_group_sales_report()
            self.load_group_salesdate_report()
            self.load_group_pay_report()
            self.load_project_cost_report()
            self.load_sales_dashboard()
            self.load_finance_dashboard()
            self.load_szl_dashboard()
            
            self.metrics.stop()
            return True
            
        except Exception as e:
            logger.error(f"❌ ADS 报表生成失败：{e}")
            self.metrics.add_error(str(e))
            self.metrics.stop()
            return False
    
    @retry_on_failure()
    def load_group_sales_report(self) -> int:
        """
        生成集团销售目标达成报表
        对应论文：ads_group_sales_report
        """
        logger.info("📈 开始生成集团销售目标达成报表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO ads_group_sales_report (
                    report_date, year, month,
                    project_guid, project_name, city,
                    target_amount, actual_amount, achievement_rate,
                    contract_count, area, unit_price,
                    data_version, dt
                )
                SELECT 
                    CURDATE() as report_date,
                    YEAR(CURDATE()) as year,
                    MONTH(CURDATE()) as month,
                    f.project_guid,
                    f.project_name,
                    '未知城市' as city,
                    0 as target_amount,  # 目标值需要另外配置
                    SUM(COALESCE(f.contract_amount, 0)) as actual_amount,
                    CASE 
                        WHEN 0 > 0 
                        THEN ROUND(SUM(COALESCE(f.contract_amount, 0)) * 100.0 / 0, 2)
                        ELSE 100.00
                    END as achievement_rate,
                    SUM(COALESCE(f.contract_count, 0)) as contract_count,
                    0 as area,
                    0 as unit_price,
                    CURDATE() as data_version,
                    %s as dt
                FROM dws_sales_payment_fact f
                WHERE f.dt = %s
                GROUP BY f.project_guid, f.project_name
                ON DUPLICATE KEY UPDATE
                    actual_amount = VALUES(actual_amount),
                    achievement_rate = VALUES(achievement_rate),
                    contract_count = VALUES(contract_count),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条集团销售目标达成记录")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def load_group_salesdate_report(self) -> int:
        """
        生成集团签约回款周月年报
        对应论文：ads_group_salesdate_report
        """
        logger.info("📈 开始生成集团签约回款周月年报...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            # 生成日报
            sql_daily = f"""
                INSERT INTO ads_group_salesdate_report (
                    report_type, report_year, report_week, report_month,
                    project_guid, project_name,
                    contract_amount, payment_amount, payment_rate,
                    contract_count, payment_count,
                    data_version, dt
                )
                SELECT 
                    'daily' as report_type,
                    YEAR(f.date_key) as report_year,
                    WEEK(f.date_key) as report_week,
                    MONTH(f.date_key) as report_month,
                    f.project_guid,
                    f.project_name,
                    SUM(COALESCE(f.contract_amount, 0)) as contract_amount,
                    SUM(COALESCE(f.payment_amount, 0)) as payment_amount,
                    COALESCE(AVG(f.payment_rate), 0) as payment_rate,
                    SUM(COALESCE(f.contract_count, 0)) as contract_count,
                    SUM(COALESCE(f.payment_count, 0)) as payment_count,
                    CURDATE() as data_version,
                    %s as dt
                FROM dws_sales_payment_fact f
                WHERE f.dt = %s
                AND f.date_key = CURDATE()
                GROUP BY 
                    YEAR(f.date_key), WEEK(f.date_key), MONTH(f.date_key),
                    f.project_guid, f.project_name
                ON DUPLICATE KEY UPDATE
                    contract_amount = VALUES(contract_amount),
                    payment_amount = VALUES(payment_amount),
                    payment_rate = VALUES(payment_rate),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql_daily, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条签约回款日报记录")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def load_group_pay_report(self) -> int:
        """
        生成集团费用支出汇总报表
        对应论文：ads_group_pay_report
        """
        logger.info("📈 开始生成集团费用支出汇总报表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO ads_group_pay_report (
                    report_date, year, month,
                    project_guid, project_name,
                    contract_pay_amount, fee_amount, total_amount,
                    budget_amount, variance_amount, variance_rate,
                    data_version, dt
                )
                SELECT 
                    CURDATE() as report_date,
                    YEAR(CURDATE()) as year,
                    MONTH(CURDATE()) as month,
                    f.project_guid,
                    f.project_name,
                    SUM(COALESCE(f.cost_amount, 0)) as contract_pay_amount,
                    SUM(COALESCE(f.fee_amount, 0)) as fee_amount,
                    SUM(COALESCE(f.cost_amount, 0)) + SUM(COALESCE(f.fee_amount, 0)) as total_amount,
                    SUM(COALESCE(f.budget_amount, 0)) as budget_amount,
                    SUM(COALESCE(f.budget_variance, 0)) as variance_amount,
                    COALESCE(AVG(f.variance_rate), 0) as variance_rate,
                    CURDATE() as data_version,
                    %s as dt
                FROM dws_sales_cost_fact f
                WHERE f.dt = %s
                GROUP BY f.project_guid, f.project_name
                ON DUPLICATE KEY UPDATE
                    total_amount = VALUES(total_amount),
                    variance_amount = VALUES(variance_amount),
                    variance_rate = VALUES(variance_rate),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条集团费用支出汇总记录")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def load_project_cost_report(self) -> int:
        """
        生成项目成本费用报表
        对应论文：ads_project_cost_report
        """
        logger.info("📈 开始生成项目成本费用报表...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO ads_project_cost_report (
                    report_date, year, month,
                    project_guid, project_name,
                    account_number, account_name, cost_type,
                    budget_amount, actual_amount, variance_amount,
                    variance_rate, completion_rate,
                    data_version, dt
                )
                SELECT 
                    CURDATE() as report_date,
                    YEAR(CURDATE()) as year,
                    MONTH(CURDATE()) as month,
                    f.project_guid,
                    f.project_name,
                    f.account_number,
                    f.account_name,
                    CASE 
                        WHEN f.account_number LIKE '5%%' THEN '成本'
                        WHEN f.account_number LIKE '6%%' THEN '费用'
                        ELSE '其他'
                    END as cost_type,
                    SUM(COALESCE(f.budget_amount, 0)) as budget_amount,
                    SUM(COALESCE(f.cost_amount, 0)) + SUM(COALESCE(f.fee_amount, 0)) as actual_amount,
                    SUM(COALESCE(f.budget_variance, 0)) as variance_amount,
                    COALESCE(AVG(f.variance_rate), 0) as variance_rate,
                    CASE 
                        WHEN SUM(COALESCE(f.budget_amount, 0)) > 0 
                        THEN ROUND((SUM(COALESCE(f.cost_amount, 0)) + SUM(COALESCE(f.fee_amount, 0))) 
                             * 100.0 / SUM(f.budget_amount), 2)
                        ELSE 0 
                    END as completion_rate,
                    CURDATE() as data_version,
                    %s as dt
                FROM dws_sales_cost_fact f
                WHERE f.dt = %s
                GROUP BY 
                    f.project_guid, f.project_name,
                    f.account_number, f.account_name
                ON DUPLICATE KEY UPDATE
                    actual_amount = VALUES(actual_amount),
                    variance_amount = VALUES(variance_amount),
                    variance_rate = VALUES(variance_rate),
                    completion_rate = VALUES(completion_rate),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条项目成本费用记录")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def load_sales_dashboard(self) -> int:
        """
        生成营销驾驶舱大屏数据
        对应论文：ads_sales_dashboard
        """
        logger.info("📈 开始生成营销驾驶舱大屏数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO ads_sales_dashboard (
                    dashboard_date, project_guid, project_name,
                    total_units, sold_units, available_units, sell_through_rate,
                    total_sales, total_payment, payment_rate, avg_unit_price,
                    data_version, dt
                )
                SELECT 
                    CURDATE() as dashboard_date,
                    d.project_guid,
                    d.project_name,
                    COUNT(DISTINCT d.room_key) as total_units,
                    SUM(CASE 
                        WHEN d.room_status IN ('signed', 'delivered', '已售') 
                        THEN 1 ELSE 0 
                    END) as sold_units,
                    SUM(CASE 
                        WHEN d.room_status IN ('available', '可售') 
                        THEN 1 ELSE 0 
                    END) as available_units,
                    ROUND(
                        SUM(CASE 
                            WHEN d.room_status IN ('signed', 'delivered', '已售') 
                            THEN 1 ELSE 0 
                        END) * 100.0 / NULLIF(COUNT(DISTINCT d.room_key), 0), 2
                    ) as sell_through_rate,
                    SUM(COALESCE(d.total_price, 0)) as total_sales,
                    COALESCE((
                        SELECT SUM(p.payment_amount) 
                        FROM dwd_payment_detail p 
                        WHERE p.project_guid = d.project_guid AND p.dt = %s
                    ), 0) as total_payment,
                    CASE 
                        WHEN SUM(COALESCE(d.total_price, 0)) > 0 
                        THEN ROUND(COALESCE((
                            SELECT SUM(p.payment_amount) 
                            FROM dwd_payment_detail p 
                            WHERE p.project_guid = d.project_guid AND p.dt = %s
                        ), 0) * 100.0 / SUM(d.total_price), 2)
                        ELSE 0 
                    END as payment_rate,
                    AVG(COALESCE(d.unit_price, 0)) as avg_unit_price,
                    CURDATE() as data_version,
                    %s as dt
                FROM dwd_room_detail d
                WHERE d.dt = %s
                GROUP BY d.project_guid, d.project_name
                ON DUPLICATE KEY UPDATE
                    sold_units = VALUES(sold_units),
                    available_units = VALUES(available_units),
                    sell_through_rate = VALUES(sell_through_rate),
                    total_sales = VALUES(total_sales),
                    total_payment = VALUES(total_payment),
                    payment_rate = VALUES(payment_rate),
                    avg_unit_price = VALUES(avg_unit_price),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt, self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条营销驾驶舱数据")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def load_finance_dashboard(self) -> int:
        """
        生成财务驾驶舱大屏数据
        对应论文：ads_finance_dashboard
        """
        logger.info("📈 开始生成财务驾驶舱大屏数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO ads_finance_dashboard (
                    dashboard_date, company_code,
                    total_revenue, total_cost, total_profit, profit_margin,
                    total_assets, total_liabilities, cash_flow,
                    budget_execution_rate,
                    data_version, dt
                )
                SELECT 
                    CURDATE() as dashboard_date,
                    COALESCE(g.company_code, 'UNKNOWN') as company_code,
                    SUM(CASE 
                        WHEN g.account_number LIKE '4%%' THEN COALESCE(g.local_amount, 0)
                        ELSE 0 
                    END) as total_revenue,
                    SUM(CASE 
                        WHEN g.account_number LIKE '5%%' THEN COALESCE(g.local_amount, 0)
                        ELSE 0 
                    END) as total_cost,
                    SUM(CASE 
                        WHEN g.account_number LIKE '4%%' THEN COALESCE(g.local_amount, 0)
                        WHEN g.account_number LIKE '5%%' THEN -COALESCE(g.local_amount, 0)
                        ELSE 0 
                    END) as total_profit,
                    CASE 
                        WHEN SUM(CASE WHEN g.account_number LIKE '4%%' THEN g.local_amount ELSE 0 END) > 0 
                        THEN ROUND(SUM(CASE 
                                WHEN g.account_number LIKE '4%%' THEN g.local_amount
                                WHEN g.account_number LIKE '5%%' THEN -g.local_amount
                                ELSE 0 
                            END) * 100.0 / 
                            SUM(CASE WHEN g.account_number LIKE '4%%' THEN g.local_amount ELSE 0 END), 2)
                        ELSE 0 
                    END as profit_margin,
                    0 as total_assets,
                    0 as total_liabilities,
                    0 as cash_flow,
                    COALESCE(AVG(f.budget_execution_rate), 0) as budget_execution_rate,
                    CURDATE() as data_version,
                    %s as dt
                FROM dwd_gl_actual_detail g
                LEFT JOIN dws_sales_cost_fact f ON g.cost_center = f.cost_center
                WHERE g.dt = %s
                GROUP BY g.company_code
                ON DUPLICATE KEY UPDATE
                    total_revenue = VALUES(total_revenue),
                    total_cost = VALUES(total_cost),
                    total_profit = VALUES(total_profit),
                    profit_margin = VALUES(profit_margin),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条财务驾驶舱数据")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def load_szl_dashboard(self) -> int:
        """
        生成收支利大屏数据
        对应论文：ads_szl_dashboard
        """
        logger.info("📈 开始生成收支利大屏数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO ads_szl_dashboard (
                    dashboard_date, project_guid, project_name,
                    sales_revenue, total_cost, total_expense,
                    operating_profit, net_profit, profit_margin,
                    roi,
                    data_version, dt
                )
                SELECT 
                    CURDATE() as dashboard_date,
                    f.project_guid,
                    f.project_name,
                    SUM(COALESCE(f.contract_amount, 0)) as sales_revenue,
                    SUM(COALESCE(f.cost_amount, 0)) as total_cost,
                    SUM(COALESCE(f.fee_amount, 0)) as total_expense,
                    SUM(COALESCE(f.contract_amount, 0)) - 
                        SUM(COALESCE(f.cost_amount, 0)) - 
                        SUM(COALESCE(f.fee_amount, 0)) as operating_profit,
                    SUM(COALESCE(f.contract_amount, 0)) - 
                        SUM(COALESCE(f.cost_amount, 0)) - 
                        SUM(COALESCE(f.fee_amount, 0)) as net_profit,  # 简化处理
                    CASE 
                        WHEN SUM(COALESCE(f.contract_amount, 0)) > 0 
                        THEN ROUND((SUM(COALESCE(f.contract_amount, 0)) - 
                                SUM(COALESCE(f.cost_amount, 0)) - 
                                SUM(COALESCE(f.fee_amount, 0))) * 100.0 / 
                                SUM(f.contract_amount), 2)
                        ELSE 0 
                    END as profit_margin,
                    CASE 
                        WHEN SUM(COALESCE(f.cost_amount, 0)) > 0 
                        THEN ROUND((SUM(COALESCE(f.contract_amount, 0)) - 
                                SUM(COALESCE(f.cost_amount, 0)) - 
                                SUM(COALESCE(f.fee_amount, 0))) * 100.0 / 
                                SUM(f.cost_amount), 2)
                        ELSE 0 
                    END as roi,
                    CURDATE() as data_version,
                    %s as dt
                FROM dws_sales_cost_fact f
                WHERE f.dt = %s
                GROUP BY f.project_guid, f.project_name
                ON DUPLICATE KEY UPDATE
                    sales_revenue = VALUES(sales_revenue),
                    total_cost = VALUES(total_cost),
                    total_expense = VALUES(total_expense),
                    operating_profit = VALUES(operating_profit),
                    net_profit = VALUES(net_profit),
                    profit_margin = VALUES(profit_margin),
                    roi = VALUES(roi),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条收支利大屏数据")
            self.metrics.add_records(affected)
            return affected
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取执行指标"""
        return self.metrics.get_summary()


def run_ads_loading() -> bool:
    """运行 ADS 层报表生成"""
    loader = ADSLoader()
    success = loader.load_all()
    
    if success:
        logger.info("✅ ADS 层报表生成完成")
    else:
        logger.error("❌ ADS 层报表生成失败")
    
    return success


if __name__ == '__main__':
    run_ads_loading()
