"""
调度器配置模块
提供 APScheduler 调度器的统一配置管理
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import logging

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """调度器配置"""
    # 调度器类型
    SCHEDULER_TYPE: str = field(default_factory=lambda: os.getenv('SCHEDULER_TYPE', 'background'))
    
    # 时区
    TIMEZONE: str = field(default_factory=lambda: os.getenv('SCHEDULER_TIMEZONE', 'Asia/Shanghai'))
    
    # 是否持久化作业
    JOB_STORE_PERSISTENT: bool = field(default_factory=lambda: os.getenv('SCHEDULER_PERSISTENT', 'false').lower() == 'true')
    
    # 数据库连接（用于持久化）
    DATABASE_URL: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///logs/scheduler.db'))
    
    # 线程池配置
    THREAD_POOL_SIZE: int = field(default_factory=lambda: int(os.getenv('SCHEDULER_THREADS', '10')))
    PROCESS_POOL_SIZE: int = field(default_factory=lambda: int(os.getenv('SCHEDULER_PROCESSES', '2')))
    
    # 日志配置
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv('SCHEDULER_LOG_LEVEL', 'INFO'))
    
    # 默认调度配置
    DEFAULT_CRON: Dict[str, Any] = field(default_factory=lambda: {
        'hour': 2,
        'minute': 0,
        'day_of_week': 'mon-fri'
    })


# 全局配置实例
scheduler_config = SchedulerConfig()


def get_scheduler_config() -> SchedulerConfig:
    """获取调度器配置"""
    return scheduler_config


def create_scheduler() -> BackgroundScheduler:
    """
    创建调度器实例
    
    Returns:
        BackgroundScheduler: 调度器实例
    """
    config = get_scheduler_config()
    
    # 配置作业存储
    jobstores = {
        'default': MemoryJobStore()
    }
    
    if config.JOB_STORE_PERSISTENT:
        try:
            jobstores['persistent'] = SQLAlchemyJobStore(url=config.DATABASE_URL)
            logger.info("✅ 启用持久化作业存储")
        except Exception as e:
            logger.warning(f"⚠️  持久化作业存储初始化失败：{e}，使用内存存储")
    
    # 配置执行器
    executors = {
        'default': ThreadPoolExecutor(config.THREAD_POOL_SIZE),
        'processpool': ProcessPoolExecutor(config.PROCESS_POOL_SIZE)
    }
    
    # 配置作业默认值
    job_defaults = {
        'coalesce': False,
        'max_instances': 1,
        'misfire_grace_time': 3600,
        'timezone': config.TIMEZONE
    }
    
    # 创建调度器
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=config.TIMEZONE
    )
    
    logger.info(f"✅ 调度器创建成功，时区：{config.TIMEZONE}，线程池大小：{config.THREAD_POOL_SIZE}")
    
    return scheduler


# 预定义的调度配置
PREDEFINED_SCHEDULES = {
    # ODS 层抽取：每天凌晨 2 点
    'ods_extraction': {
        'hour': 2,
        'minute': 0,
        'description': 'ODS 层数据抽取'
    },
    
    # DWD 层清洗：每天凌晨 3 点
    'dwd_cleaning': {
        'hour': 3,
        'minute': 0,
        'description': 'DWD 层数据清洗'
    },
    
    # DWS 层聚合：每天凌晨 4 点
    'dws_aggregation': {
        'hour': 4,
        'minute': 0,
        'description': 'DWS 层数据聚合'
    },
    
    # ADS 层报表：每天凌晨 5 点
    'ads_loading': {
        'hour': 5,
        'minute': 0,
        'description': 'ADS 层报表生成'
    },
    
    # 完整 ETL 流程：每周一凌晨 1 点
    'full_etl': {
        'hour': 1,
        'minute': 0,
        'day_of_week': 'mon',
        'description': '完整 ETL 流程'
    },
    
    # 维度表刷新：每周日凌晨 3 点
    'dim_refresh': {
        'hour': 3,
        'minute': 0,
        'day_of_week': 'sun',
        'description': '维度表刷新'
    },
    
    # 小时级增量：每小时整点
    'hourly_incremental': {
        'minute': 0,
        'description': '小时级增量更新'
    }
}


def get_predefined_schedule(task_name: str) -> Optional[Dict[str, Any]]:
    """
    获取预定义的调度配置
    
    Args:
        task_name: 任务名称
        
    Returns:
        调度配置字典
    """
    return PREDEFINED_SCHEDULES.get(task_name)


def cron_expression_to_trigger(cron_expr: str) -> Dict[str, Any]:
    """
    将 Cron 表达式转换为 APScheduler 触发器参数
    
    Args:
        cron_expr: Cron 表达式（支持 5 位和 6 位格式）
        
    Returns:
        触发器参数字典
    """
    parts = cron_expr.strip().split()
    
    if len(parts) == 5:
        # 标准 5 位 Cron: minute hour day month day_of_week
        return {
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'day_of_week': parts[4]
        }
    elif len(parts) == 6:
        # 扩展 6 位 Cron: second minute hour day month day_of_week
        return {
            'second': parts[0],
            'minute': parts[1],
            'hour': parts[2],
            'day': parts[3],
            'month': parts[4],
            'day_of_week': parts[5]
        }
    else:
        raise ValueError(f"无效的 Cron 表达式：{cron_expr}")
