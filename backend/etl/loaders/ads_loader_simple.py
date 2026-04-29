"""
ADS 层报表生成器 - 修复版本
基于当前数仓表结构
"""
import mysql.connector
from typing import List, Dict
from datetime import date
import logging

from ..config import get_config
from ..utils import mysql_connection, batch_insert

logger = logging.getLogger(__name__)


class ADSLoader:
    """ADS 层报表加载器"""
    
    def __init__(self):
        self.config = get_config()
        self.dt = self.config.get_dt_str()
    
    def load_all(self) -> bool:
        """执行完整的 ADS 层报表生成"""
        try:
            self.load_sales_dashboard()
            return True
        except Exception as e:
            logger.error(f"❌ ADS 报表生成失败：{e}")
            return False
    
    def load_sales_dashboard(self) -> int:
        """生成营销驾驶舱数据"""
        logger.info("📊 开始生成营销驾驶舱数据...")
        
        with mysql_connection() as mysql_conn:
            cursor = mysql_conn.cursor()
            
            # 先清空当日数据
            truncate_sql = "DELETE FROM ads_sales_dashboard WHERE dt = %s"
            cursor.execute(truncate_sql, (self.dt,))
            
            # 从 DWD 层聚合
            insert_sql = """
                INSERT INTO ads_sales_dashboard (
                    dashboard_date, project_guid, project_name,
                    total_units, sold_units, available_units,
                    sell_through_rate, total_sales, total_payment,
                    payment_rate, avg_unit_price,
                    data_version, dt
                )
                SELECT 
                    %s as dashboard_date,
                    building_code as project_guid,
                    CONCAT('项目-', building_code) as project_name,
                    COUNT(*) as total_units,
                    SUM(CASE WHEN room_status IN ('已签约', '已交付') THEN 1 ELSE 0 END) as sold_units,
                    SUM(CASE WHEN room_status = '可售' THEN 1 ELSE 0 END) as available_units,
                    ROUND(
                        SUM(CASE WHEN room_status IN ('已签约', '已交付') THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(*), 0), 2
                    ) as sell_through_rate,
                    SUM(total_price) as total_sales,
                    0 as total_payment,
                    0 as payment_rate,
                    AVG(unit_price) as avg_unit_price,
                    %s as data_version,
                    %s as dt
                FROM dwd_room_detail
                WHERE dt = %s
                GROUP BY building_code
            """
            
            cursor.execute(insert_sql, (self.dt, self.dt, self.dt, self.dt))
            mysql_conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 生成 {affected} 条营销驾驶舱数据")
            return affected


def run_ads_loading() -> bool:
    """ADS 报表生成入口函数"""
    loader = ADSLoader()
    return loader.load_all()
