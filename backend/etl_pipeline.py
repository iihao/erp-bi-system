#!/usr/bin/env python3
"""
ETL 流程 - 从 SQLite 业务库到 MySQL 数仓
基于黄强论文《基于 ERP 的地产行业商业智能报表系统的设计与实现》
实现 ODS→DWD→DWS→ADS 四层数据流转

执行方式：
    python etl_pipeline.py
    
环境要求：
    pip install mysql-connector-python
"""

import sqlite3
import mysql.connector
from mysql.connector import Error
import os
import sys
from datetime import datetime, date
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ETLConfig:
    """ETL 配置"""
    # SQLite 业务库配置
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'backend/db/erp_bi.db')
    
    # MySQL 数仓配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3307'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'erp_bi')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'erp_bi123')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'erp_bi_warehouse')
    
    # 当前数据分区日期
    DT = date.today().isoformat()


class ETLConnection:
    """数据库连接管理"""
    
    def __init__(self):
        self.sqlite_conn = None
        self.mysql_conn = None
    
    def connect_sqlite(self):
        """连接 SQLite 业务库"""
        try:
            self.sqlite_conn = sqlite3.connect(ETLConfig.SQLITE_DB_PATH)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"✅ SQLite 连接成功：{ETLConfig.SQLITE_DB_PATH}")
            return True
        except Exception as e:
            logger.error(f"❌ SQLite 连接失败：{e}")
            return False
    
    def connect_mysql(self):
        """连接 MySQL 数仓"""
        try:
            self.mysql_conn = mysql.connector.connect(
                host=ETLConfig.MYSQL_HOST,
                port=ETLConfig.MYSQL_PORT,
                user=ETLConfig.MYSQL_USER,
                password=ETLConfig.MYSQL_PASSWORD,
                database=ETLConfig.MYSQL_DATABASE,
                charset='utf8mb4',
                use_unicode=True
            )
            logger.info(f"✅ MySQL 连接成功：{ETLConfig.MYSQL_HOST}:{ETLConfig.MYSQL_PORT}/{ETLConfig.MYSQL_DATABASE}")
            return True
        except Error as e:
            logger.error(f"❌ MySQL 连接失败：{e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("SQLite 连接已关闭")
        if self.mysql_conn:
            self.mysql_conn.close()
            logger.info("MySQL 连接已关闭")


class ETLExtractor:
    """数据抽取器 - 从 SQLite 抽取数据"""
    
    def __init__(self, sqlite_conn):
        self.conn = sqlite_conn
        self.cursor = self.conn.cursor()
    
    def extract_table(self, table_name: str, columns: List[str] = None, where: str = None) -> List[Dict]:
        """抽取表数据"""
        try:
            cols = '*' if not columns else ', '.join(columns)
            sql = f"SELECT {cols} FROM {table_name}"
            if where:
                sql += f" WHERE {where}"
            
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            
            result = []
            for row in rows:
                row_dict = dict(row) if hasattr(row, 'keys') else row
                result.append(row_dict)
            
            logger.info(f"📤 从 {table_name} 抽取 {len(result)} 条记录")
            return result
        except Exception as e:
            logger.error(f"❌ 抽取 {table_name} 失败：{e}")
            return []
    
    def extract_projects(self) -> List[Dict]:
        """抽取项目数据"""
        return self.extract_table('re_projects')
    
    def extract_buildings(self) -> List[Dict]:
        """抽取楼栋数据"""
        return self.extract_table('re_buildings')
    
    def extract_units(self) -> List[Dict]:
        """抽取房源数据"""
        return self.extract_table('re_units')
    
    def extract_customers(self) -> List[Dict]:
        """抽取客户数据"""
        return self.extract_table('re_customers')
    
    def extract_contracts(self) -> List[Dict]:
        """抽取合同数据"""
        return self.extract_table('re_contracts')
    
    def extract_payments(self) -> List[Dict]:
        """抽取收款数据"""
        return self.extract_table('re_payments')


class ETLLoader:
    """数据加载器 - 加载到 MySQL 数仓"""
    
    def __init__(self, mysql_conn):
        self.conn = mysql_conn
        self.cursor = self.conn.cursor()
        self.dt = ETLConfig.DT
    
    def load_to_ods(self, table_name: str, data: List[Dict], field_mapping: Dict[str, str]):
        """加载数据到 ODS 层"""
        if not data:
            logger.warning(f"⚠️  {table_name} 无数据可加载")
            return 0
        
        try:
            # 构建插入 SQL
            columns = list(field_mapping.keys())
            columns.append('dt')
            placeholders = ', '.join(['%s'] * len(columns))
            cols_str = ', '.join(columns)
            
            insert_sql = f"""
                INSERT INTO {table_name} ({cols_str})
                VALUES ({placeholders})
            """
            
            # 准备数据
            values = []
            for row in data:
                row_values = [row.get(field_mapping[col]) for col in list(field_mapping.keys())]
                row_values.append(self.dt)
                values.append(tuple(row_values))
            
            # 批量插入
            self.cursor.executemany(insert_sql, values)
            self.conn.commit()
            
            affected = self.cursor.rowcount
            logger.info(f"📥 加载 {affected} 条记录到 ODS.{table_name}")
            return affected
        except Error as e:
            logger.error(f"❌ 加载 {table_name} 失败：{e}")
            self.conn.rollback()
            return 0
    
    def execute_sql(self, sql: str, params: tuple = None):
        """执行 SQL"""
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            self.conn.commit()
            return self.cursor.rowcount
        except Error as e:
            logger.error(f"❌ SQL 执行失败：{e}\nSQL: {sql}")
            self.conn.rollback()
            return 0
    
    def truncate_table(self, table_name: str):
        """清空表"""
        return self.execute_sql(f"TRUNCATE TABLE {table_name}")


class ETLPipeline:
    """ETL 主流程"""
    
    def __init__(self):
        self.connection = ETLConnection()
        self.extractor = None
        self.loader = None
    
    def run(self):
        """执行 ETL 流程"""
        logger.info("=" * 60)
        logger.info("🚀 ETL 流程开始")
        logger.info(f"📅 数据分区日期：{ETLConfig.DT}")
        logger.info("=" * 60)
        
        try:
            # 1. 建立连接
            if not self.connection.connect_sqlite():
                return False
            if not self.connection.connect_mysql():
                return False
            
            self.extractor = ETLExtractor(self.connection.sqlite_conn)
            self.loader = ETLLoader(self.connection.mysql_conn)
            
            # 2. 执行各层 ETL
            self.etl_source_to_ods()
            self.etl_odsto_dwd()
            self.etl_dwd_to_dws()
            self.etl_dws_to_ads()
            
            logger.info("=" * 60)
            logger.info("✅ ETL 流程完成")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ ETL 流程异常：{e}")
            return False
        finally:
            self.connection.close()
    
    def etl_source_to_ods(self):
        """第一阶段：业务库 → ODS 层"""
        logger.info("\n" + "=" * 60)
        logger.info("📌 阶段 1: 业务库 → ODS 层")
        logger.info("=" * 60)
        
        # 抽取项目数据并加载到 ODS
        projects = self.extractor.extract_projects()
        if projects:
            # 将 re_projects 映射到 ods_room（简化示例）
            field_mapping = {
                'project_guid': 'project_id',
                'project_name': 'project_name',
                'city': 'city',
                'district': 'district',
                'project_type': 'room_type',
                'total_area': 'building_area',
                'total_units': 'unit_number',
                'project_status': 'room_status'
            }
            # 注意：这里需要根据实际表结构调整映射关系
            logger.info(f"✅ 项目数据已抽取：{len(projects)} 条")
        
        # TODO: 实现完整的 ODS 层加载逻辑
        # - ods_room (从 re_units + re_buildings + re_projects)
        # - ods_trade (从 re_contracts + re_subscriptions)
        # - ods_payment (从 re_payments)
        # - ods_contract (从 re_contracts)
        # - 等等...
    
    def etl_odsto_dwd(self):
        """第二阶段：ODS 层 → DWD 层（数据清洗）"""
        logger.info("\n" + "=" * 60)
        logger.info("📌 阶段 2: ODS 层 → DWD 层（数据清洗）")
        logger.info("=" * 60)
        
        # 示例：DWD 层数据清洗 SQL
        sql_dwd_room = """
            INSERT INTO dwd_room_detail 
            (room_key, room_guid, project_guid, project_name, building_code, room_code, 
             room_name, floor, unit_number, room_type, building_area, internal_area, 
             share_area, orientation, total_price, unit_price, room_status, data_version, dt)
            SELECT 
                CONCAT('RK_', room_guid) as room_key,
                room_guid,
                project_guid,
                '' as project_name,
                building_code,
                room_code,
                room_name,
                floor,
                unit_number,
                room_type,
                building_area,
                internal_area,
                share_area,
                orientation,
                total_price,
                unit_price,
                room_status,
                DATE(NOW()) as data_version,
                %s as dt
            FROM ods_room
            WHERE dt = %s
        """
        # self.loader.execute_sql(sql_dwd_room, (self.loader.dt, self.loader.dt))
    
    def etl_dwd_to_dws(self):
        """第三阶段：DWD 层 → DWS 层（主题聚合）"""
        logger.info("\n" + "=" * 60)
        logger.info("📌 阶段 3: DWD 层 → DWS 层（主题聚合）")
        logger.info("=" * 60)
        
        # 示例：DWS 层销售 - 回款事实表聚合
        sql_dws_sales = """
            INSERT INTO dws_sales_payment_fact
            (project_guid, project_name, contract_guid, customer_guid, 
             date_key, year, month, day, contract_amount, payment_amount, 
             payment_rate, contract_count, payment_count, data_version, dt)
            SELECT 
                d.project_guid,
                d.project_name,
                d.contract_guid,
                d.customer_guid,
                d.contract_sign_date as date_key,
                YEAR(d.contract_sign_date) as year,
                MONTH(d.contract_sign_date) as month,
                DAY(d.contract_sign_date) as day,
                SUM(d.total_price) as contract_amount,
                COALESCE(SUM(p.payment_amount), 0) as payment_amount,
                CASE 
                    WHEN SUM(d.total_price) > 0 
                    THEN COALESCE(SUM(p.payment_amount), 0) * 100.0 / SUM(d.total_price)
                    ELSE 0 
                END as payment_rate,
                COUNT(DISTINCT d.contract_guid) as contract_count,
                COUNT(DISTINCT p.payment_guid) as payment_count,
                DATE(NOW()) as data_version,
                %s as dt
            FROM dwd_trade_detail d
            LEFT JOIN dwd_payment_detail p ON d.contract_guid = p.contract_guid
            WHERE d.dt = %s
            GROUP BY d.project_guid, d.project_name, d.contract_guid, d.customer_guid,
                     d.contract_sign_date, YEAR(d.contract_sign_date), 
                     MONTH(d.contract_sign_date), DAY(d.contract_sign_date)
        """
        # self.loader.execute_sql(sql_dws_sales, (self.loader.dt, self.loader.dt))
    
    def etl_dws_to_ads(self):
        """第四阶段：DWS 层 → ADS 层（报表聚合）"""
        logger.info("\n" + "=" * 60)
        logger.info("📌 阶段 4: DWS 层 → ADS 层（报表聚合）")
        logger.info("=" * 60)
        
        # 示例：ADS 层营销驾驶舱聚合
        sql_ads_sales = """
            INSERT INTO ads_sales_dashboard
            (dashboard_date, project_guid, project_name, total_units, sold_units, 
             available_units, sell_through_rate, total_sales, total_payment, 
             payment_rate, avg_unit_price, data_version, dt)
            SELECT 
                DATE(NOW()) as dashboard_date,
                project_guid,
                project_name,
                COUNT(*) as total_units,
                SUM(CASE WHEN room_status IN ('signed', 'delivered') THEN 1 ELSE 0 END) as sold_units,
                SUM(CASE WHEN room_status = 'available' THEN 1 ELSE 0 END) as available_units,
                ROUND(
                    SUM(CASE WHEN room_status IN ('signed', 'delivered') THEN 1 ELSE 0 END) * 100.0 / 
                    NULLIF(COUNT(*), 0), 2
                ) as sell_through_rate,
                SUM(total_price) as total_sales,
                0 as total_payment,
                0 as payment_rate,
                AVG(unit_price) as avg_unit_price,
                DATE(NOW()) as data_version,
                %s as dt
            FROM dwd_room_detail
            WHERE dt = %s
            GROUP BY project_guid, project_name
        """
        # self.loader.execute_sql(sql_ads_sales, (self.loader.dt, self.loader.dt))


if __name__ == '__main__':
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)
    
    # 执行 ETL
    pipeline = ETLPipeline()
    success = pipeline.run()
    
    # 退出码
    sys.exit(0 if success else 1)
