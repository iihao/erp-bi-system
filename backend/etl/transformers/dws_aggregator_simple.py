"""
DWS 层数据聚合器 - 修复版本
基于当前数仓表结构
"""
import mysql.connector
from typing import List, Dict
from datetime import date
import logging

from ..config import get_config
from ..utils import mysql_connection, batch_insert

logger = logging.getLogger(__name__)


class DWSAggregator:
    """DWS 层数据聚合器"""
    
    def __init__(self):
        self.config = get_config()
        self.dt = self.config.get_dt_str()
    
    def aggregate_all(self) -> bool:
        """执行完整的 DWS 层聚合"""
        try:
            self.aggregate_sales_payment_fact()
            return True
        except Exception as e:
            logger.error(f"❌ DWS 聚合失败：{e}")
            return False
    
    def aggregate_sales_payment_fact(self) -> int:
        """聚合销售 - 回款事实表"""
        logger.info("📈 开始生成销售 - 回款事实表...")
        
        with mysql_connection() as mysql_conn:
            cursor = mysql_conn.cursor()
            
            # 先清空当日数据
            truncate_sql = "DELETE FROM dws_sales_payment_fact WHERE dt = %s"
            cursor.execute(truncate_sql, (self.dt,))
            
            # 从 DWD 层聚合
            insert_sql = """
                INSERT INTO dws_sales_payment_fact (
                    project_guid, project_name, contract_guid, customer_guid,
                    date_key, year, month, day,
                    contract_amount, payment_amount, payment_rate,
                    contract_count, payment_count,
                    data_version, dt
                )
                SELECT 
                    t.room_guid as project_guid,
                    '项目' as project_name,
                    t.contract_guid,
                    t.buyer_all_names as customer_guid,
                    t.contract_qs_date as date_key,
                    YEAR(t.contract_qs_date) as year,
                    MONTH(t.contract_qs_date) as month,
                    DAY(t.contract_qs_date) as day,
                    COUNT(DISTINCT t.trade_guid) as contract_count,
                    COUNT(DISTINCT p.payment_guid) as payment_count,
                    0 as contract_amount,
                    0 as payment_amount,
                    0 as payment_rate,
                    %s as data_version,
                    %s as dt
                FROM ods_trade t
                LEFT JOIN ods_payment p ON t.contract_guid = p.contract_guid
                WHERE t.dt = %s
                GROUP BY t.room_guid, t.contract_guid, t.buyer_all_names, t.contract_qs_date
            """
            
            cursor.execute(insert_sql, (self.dt, self.dt, self.dt))
            mysql_conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条销售 - 回款事实数据")
            return affected


def run_dws_aggregation() -> bool:
    """DWS 聚合入口函数"""
    aggregator = DWSAggregator()
    return aggregator.aggregate_all()
