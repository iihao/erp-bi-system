"""
调度任务定义模块
定义所有可调度的 ETL 任务
"""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps

from etl.extractors.ods_extractor import run_ods_extraction
from etl.transformers.dwd_cleaner import run_dwd_cleaning
from etl.transformers.dws_aggregator import run_dws_aggregation
from etl.loaders.ads_loader import run_ads_loading
from etl.config import setup_logging

logger = logging.getLogger(__name__)


# ============================================
# 任务执行包装器
# ============================================

def etl_task(task_name: str):
    """
    ETL 任务装饰器
    
    Args:
        task_name: 任务名称
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info("=" * 60)
            logger.info(f"🚀 开始执行任务：{task_name}")
            logger.info(f"⏰ 执行时间：{datetime.now().isoformat()}")
            logger.info("=" * 60)
            
            try:
                # 设置日志
                setup_logging()
                
                # 执行任务
                result = func(*args, **kwargs)
                
                logger.info("=" * 60)
                logger.info(f"✅ 任务完成：{task_name}")
                logger.info(f"📊 执行结果：{result}")
                logger.info("=" * 60)
                
                return {
                    'success': True,
                    'task_name': task_name,
                    'executed_at': datetime.now().isoformat(),
                    'result': result
                }
                
            except Exception as e:
                logger.error("=" * 60)
                logger.error(f"❌ 任务失败：{task_name}")
                logger.error(f"💥 错误信息：{str(e)}")
                logger.error("=" * 60)
                
                return {
                    'success': False,
                    'task_name': task_name,
                    'executed_at': datetime.now().isoformat(),
                    'error': str(e)
                }
        
        return wrapper
    return decorator


# ============================================
# ETL 任务定义
# ============================================

@etl_task('ODS 数据抽取')
def job_ods_extraction(mode: str = 'incremental') -> Dict[str, Any]:
    """
    ODS 层数据抽取任务
    
    Args:
        mode: 抽取模式（full/incremental）
        
    Returns:
        执行结果
    """
    from ..etl.config import etl_config
    etl_config.MODE = mode
    
    success = run_ods_extraction()
    
    return {
        'layer': 'ODS',
        'mode': mode,
        'success': success
    }


@etl_task('DWD 数据清洗')
def job_dwd_cleaning(mode: str = 'incremental') -> Dict[str, Any]:
    """
    DWD 层数据清洗任务
    
    Args:
        mode: 清洗模式（full/incremental）
        
    Returns:
        执行结果
    """
    from ..etl.config import etl_config
    etl_config.MODE = mode
    
    success = run_dwd_cleaning()
    
    return {
        'layer': 'DWD',
        'mode': mode,
        'success': success
    }


@etl_task('DWS 数据聚合')
def job_dws_aggregation(mode: str = 'incremental') -> Dict[str, Any]:
    """
    DWS 层数据聚合任务
    
    Args:
        mode: 聚合模式（full/incremental）
        
    Returns:
        执行结果
    """
    from ..etl.config import etl_config
    etl_config.MODE = mode
    
    success = run_dws_aggregation()
    
    return {
        'layer': 'DWS',
        'mode': mode,
        'success': success
    }


@etl_task('ADS 报表生成')
def job_ads_loading(mode: str = 'incremental') -> Dict[str, Any]:
    """
    ADS 层报表生成任务
    
    Args:
        mode: 生成模式（full/incremental）
        
    Returns:
        执行结果
    """
    from ..etl.config import etl_config
    etl_config.MODE = mode
    
    success = run_ads_loading()
    
    return {
        'layer': 'ADS',
        'mode': mode,
        'success': success
    }


@etl_task('完整 ETL 流程')
def job_full_etl(mode: str = 'incremental') -> Dict[str, Any]:
    """
    完整 ETL 流程任务（按顺序执行所有层）
    
    Args:
        mode: 执行模式（full/incremental）
        
    Returns:
        执行结果
    """
    results = {
        'ODS': None,
        'DWD': None,
        'DWS': None,
        'ADS': None
    }
    
    # 顺序执行各层
    logger.info("📌 执行阶段 1: ODS 层抽取")
    results['ODS'] = job_ods_extraction(mode)
    
    if not results['ODS']['success']:
        logger.error("❌ ODS 层失败，终止后续流程")
        return {'success': False, 'failed_at': 'ODS', 'results': results}
    
    logger.info("📌 执行阶段 2: DWD 层清洗")
    results['DWD'] = job_dwd_cleaning(mode)
    
    if not results['DWD']['success']:
        logger.error("❌ DWD 层失败，终止后续流程")
        return {'success': False, 'failed_at': 'DWD', 'results': results}
    
    logger.info("📌 执行阶段 3: DWS 层聚合")
    results['DWS'] = job_dws_aggregation(mode)
    
    if not results['DWS']['success']:
        logger.error("❌ DWS 层失败，终止后续流程")
        return {'success': False, 'failed_at': 'DWS', 'results': results}
    
    logger.info("📌 执行阶段 4: ADS 层报表生成")
    results['ADS'] = job_ads_loading(mode)
    
    if not results['ADS']['success']:
        logger.error("❌ ADS 层失败")
        return {'success': False, 'failed_at': 'ADS', 'results': results}
    
    logger.info("✅ 完整 ETL 流程执行成功")
    return {'success': True, 'results': results}


@etl_task('维度表刷新')
def job_dim_refresh() -> Dict[str, Any]:
    """
    维度表刷新任务
    
    Returns:
        执行结果
    """
    from ..etl.transformers.dws_aggregator import DWSAggregator
    
    aggregator = DWSAggregator()
    
    results = {
        'dim_project': None,
        'dim_date': None,
        'dim_account': None
    }
    
    try:
        logger.info("📌 刷新项目维度表")
        results['dim_project'] = aggregator.build_dim_project()
        
        logger.info("📌 刷新时间维度表")
        results['dim_date'] = aggregator.build_dim_date()
        
        logger.info("📌 刷新科目维度表")
        results['dim_account'] = aggregator.build_dim_account()
        
        return {'success': True, 'results': results}
        
    except Exception as e:
        logger.error(f"❌ 维度表刷新失败：{e}")
        return {'success': False, 'error': str(e), 'results': results}


# ============================================
# 任务注册表
# ============================================

TASK_REGISTRY = {
    'ods_extraction': {
        'func': job_ods_extraction,
        'name': 'ODS 数据抽取',
        'layer': 'ODS',
        'description': '从业务库抽取原始数据到 ODS 层',
        'default_schedule': {'hour': 2, 'minute': 0}
    },
    'dwd_cleaning': {
        'func': job_dwd_cleaning,
        'name': 'DWD 数据清洗',
        'layer': 'DWD',
        'description': '清洗和标准化 ODS 层数据',
        'default_schedule': {'hour': 3, 'minute': 0}
    },
    'dws_aggregation': {
        'func': job_dws_aggregation,
        'name': 'DWS 数据聚合',
        'layer': 'DWS',
        'description': '轻度聚合生成汇总数据',
        'default_schedule': {'hour': 4, 'minute': 0}
    },
    'ads_loading': {
        'func': job_ads_loading,
        'name': 'ADS 报表生成',
        'layer': 'ADS',
        'description': '生成面向应用的报表指标',
        'default_schedule': {'hour': 5, 'minute': 0}
    },
    'full_etl': {
        'func': job_full_etl,
        'name': '完整 ETL 流程',
        'layer': 'ALL',
        'description': '按顺序执行 ODS→DWD→DWS→ADS 完整流程',
        'default_schedule': {'hour': 1, 'minute': 0, 'day_of_week': 'mon'}
    },
    'dim_refresh': {
        'func': job_dim_refresh,
        'name': '维度表刷新',
        'layer': 'DWS',
        'description': '刷新项目、时间、科目维度表',
        'default_schedule': {'hour': 3, 'minute': 0, 'day_of_week': 'sun'}
    }
}


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    获取任务定义
    
    Args:
        task_id: 任务 ID
        
    Returns:
        任务定义字典
    """
    return TASK_REGISTRY.get(task_id)


def get_all_tasks() -> Dict[str, Dict[str, Any]]:
    """
    获取所有任务定义
    
    Returns:
        任务定义字典
    """
    return TASK_REGISTRY


def list_tasks() -> list:
    """
    列出所有可用任务
    
    Returns:
        任务 ID 列表
    """
    return list(TASK_REGISTRY.keys())
