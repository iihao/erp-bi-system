"""
调度器主程序
基于 APScheduler 实现 ETL 任务的定时调度
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import atexit

from .config import create_scheduler, get_scheduler_config, cron_expression_to_trigger, get_predefined_schedule
from .jobs import TASK_REGISTRY, get_task, job_full_etl

logger = logging.getLogger(__name__)


class ETLScheduler:
    """ETL 调度器"""
    
    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
        self.config = get_scheduler_config()
        self.registered_jobs: Dict[str, str] = {}  # job_id -> task_id mapping
    
    def start(self) -> bool:
        """
        启动调度器
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🚀 启动 ETL 调度器...")
            
            # 创建调度器
            self.scheduler = create_scheduler()
            
            # 注册默认任务
            self.register_default_jobs()
            
            # 启动调度器
            self.scheduler.start()
            
            logger.info("✅ ETL 调度器启动成功")
            
            # 注册关闭钩子
            atexit.register(self.shutdown)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 调度器启动失败：{e}")
            return False
    
    def shutdown(self, wait: bool = True) -> bool:
        """
        关闭调度器
        
        Args:
            wait: 是否等待正在执行的任务完成
            
        Returns:
            bool: 是否成功
        """
        try:
            if self.scheduler and self.scheduler.running:
                logger.info("🛑 关闭 ETL 调度器...")
                self.scheduler.shutdown(wait=wait)
                logger.info("✅ ETL 调度器已关闭")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 调度器关闭失败：{e}")
            return False
    
    def register_default_jobs(self):
        """注册默认的 ETL 任务"""
        logger.info("📋 注册默认 ETL 任务...")
        
        # 注册完整 ETL 流程（每周一凌晨 1 点）
        self.add_job(
            task_id='full_etl',
            trigger='cron',
            cron_expr='0 1 * * mon',
            job_id='weekly_full_etl'
        )
        
        # 注册 ODS 抽取（每天凌晨 2 点）
        self.add_job(
            task_id='ods_extraction',
            trigger='cron',
            cron_expr='0 2 * * *',
            job_id='daily_ods_extraction'
        )
        
        # 注册 DWD 清洗（每天凌晨 3 点）
        self.add_job(
            task_id='dwd_cleaning',
            trigger='cron',
            cron_expr='0 3 * * *',
            job_id='daily_dwd_cleaning'
        )
        
        # 注册 DWS 聚合（每天凌晨 4 点）
        self.add_job(
            task_id='dws_aggregation',
            trigger='cron',
            cron_expr='0 4 * * *',
            job_id='daily_dws_aggregation'
        )
        
        # 注册 ADS 报表（每天凌晨 5 点）
        self.add_job(
            task_id='ads_loading',
            trigger='cron',
            cron_expr='0 5 * * *',
            job_id='daily_ads_loading'
        )
        
        logger.info(f"✅ 已注册 {len(self.registered_jobs)} 个默认任务")
    
    def add_job(
        self,
        task_id: str,
        trigger: str = 'cron',
        cron_expr: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        run_date: Optional[str] = None,
        job_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        添加调度任务
        
        Args:
            task_id: 任务 ID（来自 TASK_REGISTRY）
            trigger: 触发器类型（cron/interval/date）
            cron_expr: Cron 表达式（trigger='cron'时使用）
            interval_seconds: 间隔秒数（trigger='interval'时使用）
            run_date: 运行日期时间（trigger='date'时使用，ISO 格式）
            job_id: 作业 ID（可选，默认自动生成）
            **kwargs: 传递给任务函数的参数
            
        Returns:
            str: 作业 ID
        """
        if not self.scheduler or not self.scheduler.running:
            logger.error("❌ 调度器未启动")
            return None
        
        # 获取任务定义
        task_def = get_task(task_id)
        if not task_def:
            logger.error(f"❌ 任务不存在：{task_id}")
            return None
        
        # 生成作业 ID
        if not job_id:
            job_id = f"{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # 创建触发器
            if trigger == 'cron':
                if cron_expr:
                    trigger_params = cron_expression_to_trigger(cron_expr)
                else:
                    # 使用预定义调度
                    predefined = get_predefined_schedule(task_id)
                    if predefined:
                        trigger_params = {k: v for k, v in predefined.items() if k != 'description'}
                    else:
                        trigger_params = self.config.DEFAULT_CRON
                
                cron_trigger = CronTrigger(
                    timezone=self.config.TIMEZONE,
                    **trigger_params
                )
                actual_trigger = cron_trigger
                
            elif trigger == 'interval':
                if not interval_seconds:
                    interval_seconds = 3600  # 默认 1 小时
                actual_trigger = IntervalTrigger(
                    seconds=interval_seconds,
                    timezone=self.config.TIMEZONE
                )
                
            elif trigger == 'date':
                if not run_date:
                    run_date = datetime.now().isoformat()
                from datetime import datetime as dt
                run_datetime = dt.fromisoformat(run_date)
                actual_trigger = DateTrigger(
                    run_date=run_datetime,
                    timezone=self.config.TIMEZONE
                )
            else:
                logger.error(f"❌ 不支持的触发器类型：{trigger}")
                return None
            
            # 添加作业
            job = self.scheduler.add_job(
                func=task_def['func'],
                trigger=actual_trigger,
                id=job_id,
                name=task_def['name'],
                kwargs=kwargs,
                replace_existing=True
            )
            
            self.registered_jobs[job_id] = task_id
            
            logger.info(f"✅ 添加任务：{job_id} ({task_def['name']})")
            logger.info(f"   触发器：{trigger}, 下次运行：{job.next_run_time}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"❌ 添加任务失败：{task_id}, 错误：{e}")
            return None
    
    def remove_job(self, job_id: str) -> bool:
        """
        移除调度任务
        
        Args:
            job_id: 作业 ID
            
        Returns:
            bool: 是否成功
        """
        if not self.scheduler:
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            
            if job_id in self.registered_jobs:
                del self.registered_jobs[job_id]
            
            logger.info(f"✅ 移除任务：{job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 移除任务失败：{job_id}, 错误：{e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        if not self.scheduler:
            return False
        
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"⏸️  暂停任务：{job_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 暂停任务失败：{job_id}, 错误：{e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        if not self.scheduler:
            return False
        
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"▶️  恢复任务：{job_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 恢复任务失败：{job_id}, 错误：{e}")
            return False
    
    def run_job_now(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        立即执行任务（不等待调度时间）
        
        Args:
            task_id: 任务 ID
            **kwargs: 传递给任务函数的参数
            
        Returns:
            执行结果
        """
        task_def = get_task(task_id)
        if not task_def:
            return {'success': False, 'error': f'任务不存在：{task_id}'}
        
        logger.info(f"⚡ 立即执行任务：{task_id}")
        
        try:
            result = task_def['func'](**kwargs)
            return result
        except Exception as e:
            logger.error(f"❌ 任务执行失败：{task_id}, 错误：{e}")
            return {'success': False, 'error': str(e)}
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取作业信息"""
        if not self.scheduler:
            return None
        
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None
            
            return {
                'job_id': job.id,
                'name': job.name,
                'task_id': self.registered_jobs.get(job.id),
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'paused': job.paused
            }
        except Exception as e:
            logger.error(f"❌ 获取作业信息失败：{job_id}, 错误：{e}")
            return None
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出所有作业"""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'job_id': job.id,
                'name': job.name,
                'task_id': self.registered_jobs.get(job.id),
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'paused': job.paused
            })
        
        return jobs
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            'running': self.scheduler.running if self.scheduler else False,
            'job_count': len(self.registered_jobs),
            'jobs': self.list_jobs(),
            'timezone': self.config.TIMEZONE
        }


# ============================================
# 全局调度器实例
# ============================================

_scheduler_instance: Optional[ETLScheduler] = None


def get_scheduler() -> ETLScheduler:
    """获取全局调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ETLScheduler()
    return _scheduler_instance


def start_scheduler() -> bool:
    """启动调度器"""
    scheduler = get_scheduler()
    return scheduler.start()


def stop_scheduler() -> bool:
    """停止调度器"""
    scheduler = get_scheduler()
    return scheduler.shutdown()


# ============================================
# CLI 入口
# ============================================

if __name__ == '__main__':
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'start':
            start_scheduler()
            print("调度器已启动，按 Ctrl+C 停止")
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop_scheduler()
        
        elif command == 'stop':
            stop_scheduler()
            print("调度器已停止")
        
        elif command == 'status':
            scheduler = get_scheduler()
            if scheduler.scheduler and scheduler.scheduler.running:
                print("调度器状态：运行中")
                print(f"已注册任务数：{len(scheduler.registered_jobs)}")
                for job in scheduler.list_jobs():
                    print(f"  - {job['job_id']}: {job['name']} (下次运行：{job['next_run_time']})")
            else:
                print("调度器状态：未运行")
        
        else:
            print(f"未知命令：{command}")
            print("可用命令：start, stop, status")
    else:
        print("ETL 调度器")
        print("用法：python scheduler.py [start|stop|status]")
