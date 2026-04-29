#!/usr/bin/env python3
"""
ETL 主流程脚本
基于黄强论文的数仓分层设计，实现完整的 ETL 流程

执行方式：
    python run_etl.py [--mode full|incremental] [--layer ODS|DWD|DWS|ADS]
    
示例：
    python run_etl.py --mode incremental
    python run_etl.py --mode full --layer ODS
"""
import sys
import os
import argparse
from datetime import datetime
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl.config import setup_logging, etl_config
from etl.extractors.ods_extractor import run_ods_extraction
from etl.transformers.dwd_cleaner import run_dwd_cleaning
from etl.transformers.dws_aggregator import run_dws_aggregation
from etl.loaders.ads_loader import run_ads_loading

logger = logging.getLogger(__name__)


def run_etl_pipeline(mode: str = 'incremental', layer: str = None) -> bool:
    """
    运行 ETL 流程
    
    Args:
        mode: ETL 模式（full/incremental）
        layer: 指定层（None 表示执行全部）
        
    Returns:
        bool: 是否成功
    """
    # 设置配置
    etl_config.MODE = mode
    
    # 设置日志
    log_file = setup_logging()
    
    logger.info("=" * 80)
    logger.info("🚀 AI数据融合 数据仓库 ETL 流程")
    logger.info("=" * 80)
    logger.info(f"📅 执行时间：{datetime.now().isoformat()}")
    logger.info(f"🔄 执行模式：{mode}")
    logger.info(f"📊 数据分区：{etl_config.get_dt_str()}")
    if layer:
        logger.info(f"🎯 执行层级：{layer}")
    logger.info("=" * 80)
    
    try:
        # 定义各层执行函数
        layers = {
            'ODS': ('ODS 层数据抽取', run_ods_extraction),
            'DWD': ('DWD 层数据清洗', run_dwd_cleaning),
            'DWS': ('DWS 层数据聚合', run_dws_aggregation),
            'ADS': ('ADS 层报表生成', run_ads_loading)
        }
        
        # 确定要执行的层
        if layer:
            if layer not in layers:
                logger.error(f"❌ 无效的层级：{layer}")
                return False
            layers_to_run = {layer: layers[layer]}
        else:
            layers_to_run = layers
        
        # 执行各层
        results = {}
        for layer_name, (layer_desc, layer_func) in layers_to_run.items():
            logger.info("\n" + "=" * 80)
            logger.info(f"📌 阶段：{layer_desc}")
            logger.info("=" * 80)
            
            try:
                success = layer_func()
                results[layer_name] = {
                    'success': success,
                    'desc': layer_desc
                }
                
                if not success:
                    logger.error(f"❌ {layer_desc} 失败")
                    if layer:
                        return False
                    # 如果执行全部，某层失败则跳过后续层
                    logger.warning(f"⚠️  跳过后续层级")
                    break
                    
            except Exception as e:
                logger.error(f"❌ {layer_desc} 异常：{e}", exc_info=True)
                results[layer_name] = {
                    'success': False,
                    'desc': layer_desc,
                    'error': str(e)
                }
                if layer:
                    return False
                break
        
        # 输出执行摘要
        logger.info("\n" + "=" * 80)
        logger.info("📊 执行摘要")
        logger.info("=" * 80)
        
        for layer_name, result in results.items():
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} {layer_name}: {result['desc']}")
        
        # 判断整体是否成功
        all_success = all(r['success'] for r in results.values())
        
        logger.info("\n" + "=" * 80)
        if all_success:
            logger.info("✅ ETL 流程执行成功")
        else:
            logger.error("❌ ETL 流程执行失败")
        logger.info("=" * 80)
        
        return all_success
        
    except Exception as e:
        logger.error(f"❌ ETL 流程异常：{e}", exc_info=True)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI数据融合 数据仓库 ETL 流程')
    parser.add_argument('--mode', type=str, default='incremental',
                        choices=['full', 'incremental'],
                        help='ETL 模式：full（全量）或 incremental（增量）')
    parser.add_argument('--layer', type=str, default=None,
                        choices=['ODS', 'DWD', 'DWS', 'ADS'],
                        help='指定执行的层，不指定则执行全部')
    
    args = parser.parse_args()
    
    success = run_etl_pipeline(mode=args.mode, layer=args.layer)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
