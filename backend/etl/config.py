"""
ETL 配置管理模块
基于黄强论文的数仓分层设计，提供统一的配置管理
"""
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # SQLite 业务库配置
    SQLITE_DB_PATH: str = field(
        default_factory=lambda: os.getenv('SQLITE_DB_PATH', 'db/erp_bi.db')
    )
    
    # MySQL 数仓配置
    MYSQL_HOST: str = field(default_factory=lambda: os.getenv('MYSQL_HOST', 'localhost'))
    MYSQL_PORT: int = field(default_factory=lambda: int(os.getenv('MYSQL_PORT', '3306')))
    MYSQL_USER: str = field(default_factory=lambda: os.getenv('MYSQL_USER', 'root'))
    MYSQL_PASSWORD: str = field(default_factory=lambda: os.getenv('MYSQL_PASSWORD', 'root123'))
    MYSQL_DATABASE: str = field(default_factory=lambda: os.getenv('MYSQL_DATABASE', 'erp_bi_warehouse'))
    
    # 连接池配置
    POOL_SIZE: int = field(default_factory=lambda: int(os.getenv('DB_POOL_SIZE', '5')))
    POOL_TIMEOUT: int = field(default_factory=lambda: int(os.getenv('DB_TIMEOUT', '30')))


@dataclass
class ETLConfig:
    """ETL 全局配置"""
    # 当前数据分区日期（T+1）
    DT: date = field(default_factory=lambda: date.today() - timedelta(days=1))
    
    # ETL 模式：full（全量）或 incremental（增量）
    MODE: str = field(default_factory=lambda: os.getenv('ETL_MODE', 'incremental'))
    
    # 重试配置
    MAX_RETRIES: int = field(default_factory=lambda: int(os.getenv('ETL_MAX_RETRIES', '3')))
    RETRY_DELAY: int = field(default_factory=lambda: int(os.getenv('ETL_RETRY_DELAY', '5')))
    
    # 批量处理配置
    BATCH_SIZE: int = field(default_factory=lambda: int(os.getenv('ETL_BATCH_SIZE', '1000')))
    
    # 日志配置
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv('ETL_LOG_LEVEL', 'INFO'))
    LOG_DIR: str = field(default_factory=lambda: os.getenv('ETL_LOG_DIR', 'logs/etl'))
    
    # 数据库配置
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    def get_dt_str(self) -> str:
        """获取分区日期字符串"""
        return self.DT.isoformat()
    
    def get_dt_range(self, days: int = 7) -> List[date]:
        """获取最近 N 天的日期范围（用于增量加载）"""
        return [(self.DT - timedelta(days=i)) for i in range(days)]
    
    def is_incremental(self) -> bool:
        """判断是否为增量模式"""
        return self.MODE.lower() == 'incremental'


@dataclass
class LayerConfig:
    """数仓分层配置"""
    # ODS 层表
    ODS_TABLES: List[str] = field(default_factory=lambda: [
        'ods_room', 'ods_trade', 'ods_payment', 'ods_pay',
        'ods_account', 'ods_contract', 'ods_bseg',
        'ods_gl_actual', 'ods_other'
    ])
    
    # DWD 层表
    DWD_TABLES: List[str] = field(default_factory=lambda: [
        'dwd_room_detail', 'dwd_trade_detail', 'dwd_payment_detail',
        'dwd_contract_detail', 'dwd_pay_detail',
        'dwd_gl_actual_detail', 'dwd_gl_budget_detail'
    ])
    
    # DWS 层表
    DWS_TABLES: List[str] = field(default_factory=lambda: [
        'dws_sales_payment_fact', 'dws_sales_cost_fact',
        'dim_project', 'dim_date', 'dim_account'
    ])
    
    # ADS 层表
    ADS_TABLES: List[str] = field(default_factory=lambda: [
        'ads_group_sales_report', 'ads_group_salesdate_report',
        'ads_group_pay_report', 'ads_project_cost_report',
        'ads_sales_dashboard', 'ads_finance_dashboard',
        'ads_szl_dashboard'
    ])
    
    def get_table_layer(self, table_name: str) -> Optional[str]:
        """获取表所属的数仓层"""
        if table_name in self.ODS_TABLES:
            return 'ODS'
        elif table_name in self.DWD_TABLES:
            return 'DWD'
        elif table_name in self.DWS_TABLES:
            return 'DWS'
        elif table_name in self.ADS_TABLES:
            return 'ADS'
        return None


# 全局配置实例
etl_config = ETLConfig()
layer_config = LayerConfig()


def get_config() -> ETLConfig:
    """获取 ETL 配置"""
    return etl_config


def get_layer_config() -> LayerConfig:
    """获取分层配置"""
    return layer_config


def setup_logging(log_file: Optional[str] = None):
    """配置日志"""
    log_dir = etl_config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    
    if not log_file:
        log_file = os.path.join(log_dir, f"etl_{etl_config.get_dt_str()}.log")
    
    logging.basicConfig(
        level=getattr(logging, etl_config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"📝 日志文件：{log_file}")
    logger.info(f"📅 ETL 日期：{etl_config.get_dt_str()}")
    logger.info(f"🔄 ETL 模式：{etl_config.MODE}")
    
    return logging.getLogger(__name__)
