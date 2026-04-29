#!/usr/bin/env python3
"""
ETL 主流程脚本 - 简化版本
用于快速验证 ETL 流程
"""
import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl.config import setup_logging, get_config
from etl.extractors.ods_extractor_simple import run_ods_extraction
from etl.transformers.dwd_cleaner import run_dwd_cleaning
from etl.transformers.dws_aggregator_simple import run_dws_aggregation
from etl.loaders.ads_loader_simple import run_ads_loading

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(description='AI数据融合 ETL 流程')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='incremental', help='ETL 模式')
    parser.add_argument('--stage', choices=['ods', 'dwd', 'dws', 'ads', 'all'], default='all', help='执行阶段')
    args = parser.parse_args()
    
    config = get_config()
    config.MODE = args.mode
    
    logger.info("=" * 80)
    logger.info("🚀 AI数据融合 数据仓库 ETL 流程 (简化版)")
    logger.info("=" * 80)
    logger.info(f"📅 执行时间：{datetime.now().isoformat()}")
    logger.info(f"🔄 执行模式：{args.mode}")
    logger.info(f"📊 数据分区：{config.get_dt_str()}")
    logger.info("=" * 80)
    
    stages = {
        'ods': ('ODS 层数据抽取', run_ods_extraction),
        'dwd': ('DWD 层数据清洗', run_dwd_cleaning),
        'dws': ('DWS 层数据聚合', run_dws_aggregation),
        'ads': ('ADS 层报表生成', run_ads_loading)
    }
    
    if args.stage == 'all':
        stage_list = ['ods', 'dwd', 'dws', 'ads']
    else:
        stage_list = [args.stage]
    
    for stage in stage_list:
        stage_name, stage_func = stages[stage]
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"📌 阶段：{stage_name}")
        logger.info("=" * 80)
        
        try:
            success = stage_func()
            if success:
                logger.info(f"✅ {stage_name} 完成")
            else:
                logger.error(f"❌ {stage_name} 失败")
                if stage == 'ods':
                    logger.warning("⚠️  跳过后续层级")
                    break
        except Exception as e:
            logger.error(f"❌ {stage_name} 异常：{e}")
            if stage == 'ods':
                logger.warning("⚠️  跳过后续层级")
                break
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 执行完成")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
