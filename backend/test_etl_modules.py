#!/usr/bin/env python3
"""
ETL 模块测试脚本
验证 ETL 流程和调度系统的功能
"""
import sys
import os
import unittest
from datetime import datetime
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestETLConfig(unittest.TestCase):
    """测试 ETL 配置模块"""
    
    def test_config_import(self):
        """测试配置模块导入"""
        from etl.config import ETLConfig, LayerConfig, get_config, get_layer_config
        self.assertIsNotNone(get_config())
        self.assertIsNotNone(get_layer_config())
    
    def test_layer_tables(self):
        """测试分层表配置"""
        from etl.config import get_layer_config
        config = get_layer_config()
        
        # 验证各层表数量
        self.assertEqual(len(config.ODS_TABLES), 9)
        self.assertEqual(len(config.DWD_TABLES), 7)
        self.assertEqual(len(config.DWS_TABLES), 5)
        self.assertEqual(len(config.ADS_TABLES), 7)
    
    def test_get_table_layer(self):
        """测试表层级查询"""
        from etl.config import get_layer_config
        config = get_layer_config()
        
        self.assertEqual(config.get_table_layer('ods_room'), 'ODS')
        self.assertEqual(config.get_table_layer('dwd_room_detail'), 'DWD')
        self.assertEqual(config.get_table_layer('dws_sales_payment_fact'), 'DWS')
        self.assertEqual(config.get_table_layer('ads_sales_dashboard'), 'ADS')


class TestETLUtils(unittest.TestCase):
    """测试 ETL 工具模块"""
    
    def test_utils_import(self):
        """测试工具模块导入"""
        from etl.utils import (
            sqlite_connection, mysql_connection, retry_on_failure,
            DataQualityChecker, batch_insert, chunk_list, ETLMetrics
        )
        self.assertIsNotNone(sqlite_connection)
        self.assertIsNotNone(mysql_connection)
    
    def test_chunk_list(self):
        """测试列表分块"""
        from etl.utils import chunk_list
        
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunks = chunk_list(data, 3)
        
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0], [1, 2, 3])
        self.assertEqual(chunks[-1], [10])
    
    def test_data_quality_checker(self):
        """测试数据质量检查器"""
        from etl.utils import DataQualityChecker
        
        checker = DataQualityChecker()
        data = [
            {'id': 1, 'name': 'A', 'value': 100},
            {'id': 2, 'name': 'B', 'value': 200},
            {'id': 3, 'name': None, 'value': 300}  # 空值
        ]
        
        # 测试空值检查
        result = checker.check_null_values(data, ['name'], 'test_table')
        self.assertFalse(result)  # 应该失败
        
        report = checker.get_report()
        self.assertGreater(report['error_count'], 0)


class TestSchedulerConfig(unittest.TestCase):
    """测试调度器配置模块"""
    
    def test_scheduler_import(self):
        """测试调度器模块导入"""
        from scheduler.config import (
            SchedulerConfig, get_scheduler_config, create_scheduler,
            cron_expression_to_trigger
        )
        self.assertIsNotNone(get_scheduler_config())
    
    def test_cron_parser(self):
        """测试 Cron 表达式解析"""
        from scheduler.config import cron_expression_to_trigger
        
        # 5 位 Cron
        result = cron_expression_to_trigger('0 2 * * *')
        self.assertEqual(result['minute'], '0')
        self.assertEqual(result['hour'], '2')
        
        # 6 位 Cron
        result = cron_expression_to_trigger('0 0 2 * * *')
        self.assertEqual(result['second'], '0')
        self.assertEqual(result['minute'], '0')
        self.assertEqual(result['hour'], '2')


class TestSchedulerJobs(unittest.TestCase):
    """测试调度任务模块"""
    
    def test_jobs_import(self):
        """测试任务模块导入"""
        from scheduler.jobs import TASK_REGISTRY, get_task, list_tasks
        self.assertIsNotNone(TASK_REGISTRY)
    
    def test_task_registry(self):
        """测试任务注册表"""
        from scheduler.jobs import TASK_REGISTRY
        
        # 验证预定义任务
        expected_tasks = [
            'ods_extraction',
            'dwd_cleaning',
            'dws_aggregation',
            'ads_loading',
            'full_etl',
            'dim_refresh'
        ]
        
        for task_id in expected_tasks:
            self.assertIn(task_id, TASK_REGISTRY)
            task = TASK_REGISTRY[task_id]
            self.assertIn('func', task)
            self.assertIn('name', task)
            self.assertIn('description', task)
    
    def test_list_tasks(self):
        """测试任务列表"""
        from scheduler.jobs import list_tasks
        
        tasks = list_tasks()
        self.assertGreater(len(tasks), 0)
        self.assertIn('full_etl', tasks)


class TestSchedulerMain(unittest.TestCase):
    """测试调度器主模块"""
    
    def test_scheduler_import(self):
        """测试调度器主模块导入"""
        from scheduler.scheduler import ETLScheduler, get_scheduler
        self.assertIsNotNone(ETLScheduler)
    
    def test_scheduler_instance(self):
        """测试调度器实例"""
        from scheduler.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        self.assertIsNotNone(scheduler)
        self.assertIsInstance(scheduler.registered_jobs, dict)


class TestETLExtractors(unittest.TestCase):
    """测试 ETL 抽取器"""
    
    def test_extractor_import(self):
        """测试抽取器导入"""
        from etl.extractors.ods_extractor import ODSExtractor, run_ods_extraction
        self.assertIsNotNone(ODSExtractor)
        self.assertIsNotNone(run_ods_extraction)


class TestETLTransformers(unittest.TestCase):
    """测试 ETL 转换器"""
    
    def test_transformer_import(self):
        """测试转换器导入"""
        from etl.transformers.dwd_cleaner import DWDCleaner, run_dwd_cleaning
        from etl.transformers.dws_aggregator import DWSAggregator, run_dws_aggregation
        
        self.assertIsNotNone(DWDCleaner)
        self.assertIsNotNone(DWSAggregator)


class TestETLLoaders(unittest.TestCase):
    """测试 ETL 加载器"""
    
    def test_loader_import(self):
        """测试加载器导入"""
        from etl.loaders.ads_loader import ADSLoader, run_ads_loading
        self.assertIsNotNone(ADSLoader)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestETLConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestETLUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestSchedulerConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestSchedulerJobs))
    suite.addTests(loader.loadTestsFromTestCase(TestSchedulerMain))
    suite.addTests(loader.loadTestsFromTestCase(TestETLExtractors))
    suite.addTests(loader.loadTestsFromTestCase(TestETLTransformers))
    suite.addTests(loader.loadTestsFromTestCase(TestETLLoaders))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 80)
    print("🧪 AI数据融合 ETL 模块测试")
    print("=" * 80)
    print(f"⏰ 测试时间：{datetime.now().isoformat()}")
    print("=" * 80)
    print()
    
    success = run_tests()
    
    print()
    print("=" * 80)
    if success:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
    print("=" * 80)
    
    sys.exit(0 if success else 1)
