"""
DWD 层数据清洗器
从 ODS 层清洗和标准化数据到 DWD 层
基于黄强论文 4.3.2 节：ODS 层→DWD 层清洗策略
"""
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

from ..config import etl_config, get_config, layer_config
from ..utils import (
    mysql_connection, batch_insert, ETLMetrics, 
    retry_on_failure, DataQualityChecker
)

logger = logging.getLogger(__name__)


class DWDCleaner:
    """DWD 层数据清洗器"""
    
    def __init__(self):
        self.config = get_config()
        self.dt = self.config.get_dt_str()
        self.metrics = ETLMetrics('DWD 数据清洗')
        self.quality_checker = DataQualityChecker()
    
    def clean_all(self) -> bool:
        """
        执行完整的 DWD 层清洗
        
        Returns:
            bool: 是否成功
        """
        self.metrics.start()
        
        try:
            # 清洗各 DWD 层表
            self.clean_room_detail()
            self.clean_trade_detail()
            self.clean_payment_detail()
            self.clean_contract_detail()
            self.clean_pay_detail()
            self.clean_gl_actual_detail()
            self.clean_gl_budget_detail()
            
            self.metrics.stop()
            return True
            
        except Exception as e:
            logger.error(f"❌ DWD 清洗失败：{e}")
            self.metrics.add_error(str(e))
            self.metrics.stop()
            return False
    
    @retry_on_failure()
    def clean_room_detail(self) -> int:
        """
        清洗房源明细数据
        ODS: ods_room → DWD: dwd_room_detail
        """
        logger.info("🧹 开始清洗房源明细数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            # DWD 层清洗 SQL（基于论文 4.3.2 节）
            # 1. 生成房源主键（room_key）
            # 2. 关联项目维度，补充项目名称
            # 3. 数据标准化：空值处理、格式统一
            # 4. 添加数据版本和分区日期
            
            sql = f"""
                INSERT INTO dwd_room_detail (
                    room_key, room_guid, project_guid, project_name,
                    building_code, room_code, room_name, floor, unit_number,
                    room_type, building_area, internal_area, share_area,
                    orientation, total_price, unit_price, room_status,
                    data_version, dt
                )
                SELECT 
                    CONCAT('RK_', COALESCE(r.room_guid, 'UNKNOWN')) as room_key,
                    r.room_guid,
                    r.project_guid,
                    COALESCE(p.project_name, '未知项目') as project_name,
                    r.building_code,
                    r.room_code,
                    COALESCE(r.room_name, '未知房间') as room_name,
                    COALESCE(r.floor, 0) as floor,
                    COALESCE(r.unit_number, 0) as unit_number,
                    COALESCE(r.room_type, '未知类型') as room_type,
                    COALESCE(r.building_area, 0) as building_area,
                    COALESCE(r.internal_area, 0) as internal_area,
                    COALESCE(r.share_area, 0) as share_area,
                    COALESCE(r.orientation, '未知') as orientation,
                    COALESCE(r.total_price, 0) as total_price,
                    COALESCE(r.unit_price, 0) as unit_price,
                    COALESCE(r.room_status, 'unknown') as room_status,
                    CURDATE() as data_version,
                    %s as dt
                FROM ods_room r
                LEFT JOIN dim_project p ON r.project_guid = p.project_guid
                WHERE r.dt = %s
                AND r.room_guid IS NOT NULL
                ON DUPLICATE KEY UPDATE
                    room_name = VALUES(room_name),
                    room_status = VALUES(room_status),
                    total_price = VALUES(total_price),
                    unit_price = VALUES(unit_price),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 清洗 {affected} 条房源明细数据到 dwd_room_detail")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def clean_trade_detail(self) -> int:
        """
        清洗销售明细数据
        ODS: ods_trade → DWD: dwd_trade_detail
        """
        logger.info("🧹 开始清洗销售明细数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO dwd_trade_detail (
                    trade_key, trade_guid, contract_guid, room_guid,
                    project_guid, project_name, customer_name, customer_id_type,
                    customer_id_number, trade_status, contract_sign_date,
                    contract_business_date, subscription_guid, subscription_date,
                    subscription_type, total_price, area, unit_price,
                    is_delay_pay, last_follow_date, data_version, dt
                )
                SELECT 
                    CONCAT('TD_', COALESCE(t.trade_guid, 'UNKNOWN')) as trade_key,
                    t.trade_guid,
                    t.contract_guid,
                    t.room_guid,
                    t.proj_guid as project_guid,
                    COALESCE(p.project_name, '未知项目') as project_name,
                    COALESCE(t.buyer_all_names, '未知客户') as customer_name,
                    '身份证' as customer_id_type,
                    COALESCE(t.buyer_all_card_ids, '未知') as customer_id_number,
                    COALESCE(t.trade_status, 'unknown') as trade_status,
                    t.contract_qs_date as contract_sign_date,
                    t.contract_ywgs_date as contract_business_date,
                    t.rgorder_guid as subscription_guid,
                    t.rgorder_qs_date as subscription_date,
                    COALESCE(t.rgorder_type, '正常认购') as subscription_type,
                    COALESCE(r.total_price, 0) as total_price,
                    COALESCE(r.building_area, 0) as area,
                    COALESCE(r.unit_price, 0) as unit_price,
                    COALESCE(t.is_exist_delay_pay, 0) as is_delay_pay,
                    t.last_gj_date as last_follow_date,
                    CURDATE() as data_version,
                    %s as dt
                FROM ods_trade t
                LEFT JOIN ods_room r ON t.room_guid = r.room_guid
                LEFT JOIN dim_project p ON t.proj_guid = p.project_guid
                WHERE t.dt = %s
                AND t.trade_guid IS NOT NULL
                ON DUPLICATE KEY UPDATE
                    trade_status = VALUES(trade_status),
                    total_price = VALUES(total_price),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 清洗 {affected} 条销售明细数据到 dwd_trade_detail")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def clean_payment_detail(self) -> int:
        """
        清洗回款明细数据
        ODS: ods_payment → DWD: dwd_payment_detail
        """
        logger.info("🧹 开始清洗回款明细数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO dwd_payment_detail (
                    payment_key, payment_guid, contract_guid, project_guid,
                    project_name, customer_guid, customer_name,
                    payment_amount, payment_date, payment_type, payment_method,
                    bank_account, invoice_number, invoice_date,
                    data_version, dt
                )
                SELECT 
                    CONCAT('PAY_', COALESCE(p.payment_guid, 'UNKNOWN')) as payment_key,
                    p.payment_guid,
                    p.contract_guid,
                    p.proj_guid as project_guid,
                    COALESCE(prj.project_name, '未知项目') as project_name,
                    p.customer_guid,
                    '未知客户' as customer_name,
                    COALESCE(p.payment_amount, 0) as payment_amount,
                    p.payment_date,
                    COALESCE(p.payment_type, '未知类型') as payment_type,
                    COALESCE(p.payment_method, '未知方式') as payment_method,
                    COALESCE(p.bank_account, '') as bank_account,
                    COALESCE(p.invoice_number, '') as invoice_number,
                    p.invoice_date,
                    CURDATE() as data_version,
                    %s as dt
                FROM ods_payment p
                LEFT JOIN dim_project prj ON p.proj_guid = prj.project_guid
                WHERE p.dt = %s
                AND p.payment_guid IS NOT NULL
                AND p.payment_amount > 0
                ON DUPLICATE KEY UPDATE
                    payment_amount = VALUES(payment_amount),
                    payment_type = VALUES(payment_type),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 清洗 {affected} 条回款明细数据到 dwd_payment_detail")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def clean_contract_detail(self) -> int:
        """
        清洗合同明细数据
        ODS: ods_contract → DWD: dwd_contract_detail
        """
        logger.info("🧹 开始清洗合同明细数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO dwd_contract_detail (
                    contract_key, contract_guid, proj_guid, project_name,
                    room_guid, customer_guid, customer_name, contract_code,
                    contract_type, contract_amount, contract_date, contract_status,
                    start_date, end_date, pay_plan, data_version, dt
                )
                SELECT 
                    CONCAT('CT_', COALESCE(c.contract_guid, 'UNKNOWN')) as contract_key,
                    c.contract_guid,
                    c.proj_guid,
                    COALESCE(p.project_name, '未知项目') as project_name,
                    c.room_guid,
                    c.customer_guid,
                    '未知客户' as customer_name,
                    COALESCE(c.contract_code, '') as contract_code,
                    COALESCE(c.contract_type, '未知类型') as contract_type,
                    COALESCE(c.contract_amount, 0) as contract_amount,
                    c.contract_date,
                    COALESCE(c.contract_status, 'unknown') as contract_status,
                    c.start_date,
                    c.end_date,
                    c.pay_plan,
                    CURDATE() as data_version,
                    %s as dt
                FROM ods_contract c
                LEFT JOIN dim_project p ON c.proj_guid = p.project_guid
                WHERE c.dt = %s
                AND c.contract_guid IS NOT NULL
                ON DUPLICATE KEY UPDATE
                    contract_amount = VALUES(contract_amount),
                    contract_status = VALUES(contract_status),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 清洗 {affected} 条合同明细数据到 dwd_contract_detail")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def clean_pay_detail(self) -> int:
        """
        清洗付款明细数据
        ODS: ods_pay → DWD: dwd_pay_detail
        """
        logger.info("🧹 开始清洗付款明细数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO dwd_pay_detail (
                    pay_key, pay_guid, contract_guid, proj_guid, project_name,
                    pay_amount, pay_date, pay_type, payee_name, payee_account,
                    invoice_flag, invoice_number, data_version, dt
                )
                SELECT 
                    CONCAT('PAYOUT_', COALESCE(p.pay_guid, 'UNKNOWN')) as pay_key,
                    p.pay_guid,
                    p.contract_guid,
                    p.proj_guid,
                    COALESCE(prj.project_name, '未知项目') as project_name,
                    COALESCE(p.pay_amount, 0) as pay_amount,
                    p.pay_date,
                    COALESCE(p.pay_type, '未知类型') as pay_type,
                    COALESCE(p.payee_name, '未知收款方') as payee_name,
                    COALESCE(p.payee_account, '') as payee_account,
                    COALESCE(p.invoice_flag, 0) as invoice_flag,
                    COALESCE(p.invoice_number, '') as invoice_number,
                    CURDATE() as data_version,
                    %s as dt
                FROM ods_pay p
                LEFT JOIN dim_project prj ON p.proj_guid = prj.project_guid
                WHERE p.dt = %s
                AND p.pay_guid IS NOT NULL
                AND p.pay_amount > 0
                ON DUPLICATE KEY UPDATE
                    pay_amount = VALUES(pay_amount),
                    pay_type = VALUES(pay_type),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 清洗 {affected} 条付款明细数据到 dwd_pay_detail")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def clean_gl_actual_detail(self) -> int:
        """
        清洗总账实际明细数据
        ODS: ods_gl_actual → DWD: dwd_gl_actual_detail
        """
        logger.info("🧹 开始清洗总账实际明细数据...")
        
        with mysql_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                INSERT INTO dwd_gl_actual_detail (
                    gl_key, gl_guid, company_code, fiscal_year,
                    document_number, line_item, account_number, account_name,
                    cost_center, cost_center_name, profit_center,
                    gl_amount, local_amount, currency, posting_date,
                    document_date, text_field, data_version, dt
                )
                SELECT 
                    CONCAT('GL_', COALESCE(g.gl_guid, 'UNKNOWN')) as gl_key,
                    g.gl_guid,
                    COALESCE(g.company_code, 'UNKNOWN') as company_code,
                    COALESCE(g.fiscal_year, YEAR(CURDATE())) as fiscal_year,
                    COALESCE(g.document_number, '') as document_number,
                    COALESCE(g.line_item, 0) as line_item,
                    COALESCE(g.account_number, '') as account_number,
                    COALESCE(g.account_name, '未知科目') as account_name,
                    COALESCE(g.cost_center, '') as cost_center,
                    '未知成本中心' as cost_center_name,
                    COALESCE(g.profit_center, '') as profit_center,
                    COALESCE(g.gl_amount, 0) as gl_amount,
                    COALESCE(g.local_amount, 0) as local_amount,
                    COALESCE(g.currency, 'CNY') as currency,
                    g.posting_date,
                    g.document_date,
                    COALESCE(g.text_field, '') as text_field,
                    CURDATE() as data_version,
                    %s as dt
                FROM ods_gl_actual g
                WHERE g.dt = %s
                AND g.gl_guid IS NOT NULL
                ON DUPLICATE KEY UPDATE
                    gl_amount = VALUES(gl_amount),
                    local_amount = VALUES(local_amount),
                    data_version = VALUES(data_version)
            """
            
            cursor.execute(sql, (self.dt, self.dt))
            conn.commit()
            
            affected = cursor.rowcount
            logger.info(f"✅ 清洗 {affected} 条总账实际明细数据到 dwd_gl_actual_detail")
            self.metrics.add_records(affected)
            return affected
    
    @retry_on_failure()
    def clean_gl_budget_detail(self) -> int:
        """
        清洗总账预算明细数据
        数据来源：可能需要从其他系统导入或 Excel 填报
        """
        logger.info("🧹 开始清洗总账预算明细数据...")
        # 预算数据通常来自其他系统，这里预留接口
        logger.warning("⚠️  预算数据源未配置，跳过 dwd_gl_budget_detail 清洗")
        return 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取执行指标"""
        return self.metrics.get_summary()


def run_dwd_cleaning() -> bool:
    """运行 DWD 层清洗"""
    cleaner = DWDCleaner()
    success = cleaner.clean_all()
    
    if success:
        logger.info("✅ DWD 层清洗完成")
    else:
        logger.error("❌ DWD 层清洗失败")
    
    return success


if __name__ == '__main__':
    run_dwd_cleaning()
