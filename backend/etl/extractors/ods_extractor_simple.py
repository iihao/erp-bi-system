"""
ODS 层数据抽取器 - 简化版本
适配当前 SQLite 数据库表结构
"""
import sqlite3
import mysql.connector
from typing import List, Dict, Any
from datetime import date
import logging

from ..config import get_config
from ..utils import sqlite_connection, mysql_connection, batch_insert

logger = logging.getLogger(__name__)


class ODSExtractor:
    """ODS 层数据抽取器"""
    
    def __init__(self):
        self.config = get_config()
        self.dt = self.config.get_dt_str()
    
    def extract_all(self) -> bool:
        """执行完整的 ODS 层抽取"""
        try:
            self.extract_rooms()
            self.extract_trades()
            self.extract_payments()
            return True
        except Exception as e:
            logger.error(f"❌ ODS 抽取失败：{e}")
            return False
    
    def extract_rooms(self) -> int:
        """抽取房源数据到 ods_room"""
        logger.info("📤 开始抽取房源数据...")
        
        with sqlite_connection() as sqlite_conn, mysql_connection() as mysql_conn:
            sqlite_cursor = sqlite_conn.cursor()
            mysql_cursor = mysql_conn.cursor()
            
            query = """
                SELECT 
                    unit_id as room_guid,
                    building_id as building_code,
                    unit_code as room_code,
                    unit_name as room_name,
                    floor,
                    unit_number,
                    unit_type as room_type,
                    building_area,
                    internal_area,
                    share_area,
                    orientation,
                    total_price,
                    unit_price,
                    unit_status as room_status,
                    created_at as created_time,
                    updated_at as modified_time
                FROM re_units
                WHERE unit_status IS NOT NULL
            """
            
            sqlite_cursor.execute(query)
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.warning("⚠️  未找到房源数据")
                return 0
            
            columns = [
                'room_guid', 'building_code', 'room_code', 'room_name',
                'floor', 'unit_number', 'room_type', 'building_area', 'internal_area',
                'share_area', 'orientation', 'total_price', 'unit_price', 'room_status',
                'created_time', 'modified_time', 'dt'
            ]
            
            placeholders = ', '.join(['%s'] * len(columns))
            cols_str = ', '.join(columns)
            
            insert_sql = f"""
                INSERT INTO ods_room ({cols_str})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE room_status = VALUES(room_status), modified_time = VALUES(modified_time)
            """
            
            values = []
            for row in rows:
                row_dict = dict(row)
                value_tuple = tuple([row_dict.get(col) for col in columns[:-1]] + [self.dt])
                values.append(value_tuple)
            
            total_inserted = batch_insert(mysql_cursor, insert_sql, values)
            mysql_conn.commit()
            
            logger.info(f"✅ 抽取 {total_inserted} 条房源数据到 ods_room")
            return total_inserted
    
    def extract_trades(self) -> int:
        """抽取销售数据到 ods_trade"""
        logger.info("📤 开始抽取销售数据...")
        
        with sqlite_connection() as sqlite_conn, mysql_connection() as mysql_conn:
            sqlite_cursor = sqlite_conn.cursor()
            mysql_cursor = mysql_conn.cursor()
            
            query = """
                SELECT 
                    contract_id as trade_guid,
                    contract_code as contract_guid,
                    unit_id as room_guid,
                    customer_id as buyer_all_names,
                    contract_date as contract_qs_date,
                    contract_type as trade_status,
                    contract_status as room_status,
                    created_at as created_time,
                    updated_at as modified_time
                FROM re_contracts
                WHERE contract_status IS NOT NULL
            """
            
            sqlite_cursor.execute(query)
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.warning("⚠️  未找到销售数据")
                return 0
            
            columns = [
                'trade_guid', 'contract_guid', 'room_guid',
                'buyer_all_names', 'trade_status', 'contract_qs_date',
                'room_status', 'created_time', 'modified_time', 'dt'
            ]
            
            placeholders = ', '.join(['%s'] * len(columns))
            cols_str = ', '.join(columns)
            
            insert_sql = f"""
                INSERT INTO ods_trade ({cols_str})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE trade_status = VALUES(trade_status), modified_time = VALUES(modified_time)
            """
            
            values = []
            for row in rows:
                row_dict = dict(row)
                value_tuple = tuple([row_dict.get(col) for col in columns[:-1]] + [self.dt])
                values.append(value_tuple)
            
            total_inserted = batch_insert(mysql_cursor, insert_sql, values)
            mysql_conn.commit()
            
            logger.info(f"✅ 抽取 {total_inserted} 条销售数据到 ods_trade")
            return total_inserted
    
    def extract_payments(self) -> int:
        """抽取回款数据到 ods_payment"""
        logger.info("📤 开始抽取回款数据...")
        
        with sqlite_connection() as sqlite_conn, mysql_connection() as mysql_conn:
            sqlite_cursor = sqlite_conn.cursor()
            mysql_cursor = mysql_conn.cursor()
            
            query = """
                SELECT 
                    payment_id as payment_guid,
                    contract_id as contract_guid,
                    payment_date,
                    amount as payment_amount,
                    payment_type,
                    payment_method,
                    remarks,
                    created_at
                FROM re_payments
                WHERE amount IS NOT NULL
            """
            
            sqlite_cursor.execute(query)
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.warning("⚠️  未找到回款数据")
                return 0
            
            columns = [
                'payment_guid', 'contract_guid', 'payment_date', 'payment_amount',
                'payment_type', 'payment_method', 'remarks',
                'created_at', 'dt'
            ]
            
            placeholders = ', '.join(['%s'] * len(columns))
            cols_str = ', '.join(columns)
            
            insert_sql = f"""
                INSERT INTO ods_payment ({cols_str})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE payment_amount = VALUES(payment_amount), payment_date = VALUES(payment_date)
            """
            
            values = []
            for row in rows:
                row_dict = dict(row)
                value_tuple = tuple([row_dict.get(col) for col in columns[:-1]] + [self.dt])
                values.append(value_tuple)
            
            total_inserted = batch_insert(mysql_cursor, insert_sql, values)
            mysql_conn.commit()
            
            logger.info(f"✅ 抽取 {total_inserted} 条回款数据到 ods_payment")
            return total_inserted


def run_ods_extraction() -> bool:
    """ODS 抽取入口函数"""
    extractor = ODSExtractor()
    return extractor.extract_all()
