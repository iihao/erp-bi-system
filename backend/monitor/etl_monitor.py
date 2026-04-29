#!/usr/bin/env python3
"""
ETL 监控告警脚本
监控 ETL 执行状态、数据质量、系统健康度
"""
import sys
import os
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ETLMonitor:
    """ETL 监控器"""
    
    def __init__(self):
        self.mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', 'root123'),
            'database': os.getenv('MYSQL_DATABASE', 'erp_bi_warehouse')
        }
        
        # 告警配置
        self.alert_config = {
            'email_enabled': os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
            'email_smtp_server': os.getenv('ALERT_EMAIL_SMTP', 'smtp.example.com'),
            'email_smtp_port': int(os.getenv('ALERT_EMAIL_PORT', '587')),
            'email_user': os.getenv('ALERT_EMAIL_USER', ''),
            'email_password': os.getenv('ALERT_EMAIL_PASSWORD', ''),
            'email_recipients': os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(','),
            'webhook_url': os.getenv('ALERT_WEBHOOK_URL', '')
        }
    
    def check_etl_status(self) -> Dict[str, Any]:
        """检查 ETL 执行状态"""
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            # 查询最新的 ETL 执行日志
            query = """
                SELECT 
                    task_name,
                    status,
                    start_time,
                    end_time,
                    TIMESTAMPDIFF(SECOND, start_time, end_time) as duration_seconds,
                    error_message
                FROM etl_task_logs
                WHERE start_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                ORDER BY start_time DESC
                LIMIT 10
            """
            
            cursor.execute(query)
            recent_jobs = cursor.fetchall()
            
            # 统计成功/失败
            success_count = sum(1 for job in recent_jobs if job['status'] == 'success')
            failed_count = len(recent_jobs) - success_count
            
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'recent_jobs': recent_jobs,
                'success_count': success_count,
                'failed_count': failed_count,
                'failure_rate': failed_count / len(recent_jobs) * 100 if recent_jobs else 0
            }
            
        except Exception as e:
            logger.error(f"❌ 检查 ETL 状态失败：{e}")
            return {'success': False, 'error': str(e)}
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """检查数据新鲜度（是否按时更新）"""
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            tables_to_check = [
                ('ods_room', 'ODS 房源'),
                ('ods_trade', 'ODS 销售'),
                ('dwd_room_detail', 'DWD 房源'),
                ('dws_sales_payment_fact', 'DWS 销售回款'),
                ('ads_sales_dashboard', 'ADS 营销驾驶舱')
            ]
            
            freshness_results = []
            
            for table, table_name_cn in tables_to_check:
                query = f"""
                    SELECT MAX(dt) as latest_dt, COUNT(*) as row_count
                    FROM {table}
                """
                cursor.execute(query)
                result = cursor.fetchone()
                
                latest_dt = result['latest_dt']
                row_count = result['row_count']
                
                # 检查是否是昨天的数据（T+1）
                expected_dt = (datetime.now() - timedelta(days=1)).date()
                is_fresh = latest_dt >= expected_dt if latest_dt else False
                
                freshness_results.append({
                    'table': table,
                    'table_name_cn': table_name_cn,
                    'latest_dt': str(latest_dt),
                    'row_count': row_count,
                    'is_fresh': is_fresh,
                    'status': '✅' if is_fresh else '⚠️'
                })
            
            cursor.close()
            conn.close()
            
            all_fresh = all(item['is_fresh'] for item in freshness_results)
            
            return {
                'success': True,
                'tables': freshness_results,
                'all_fresh': all_fresh
            }
            
        except Exception as e:
            logger.error(f"❌ 检查数据新鲜度失败：{e}")
            return {'success': False, 'error': str(e)}
    
    def check_data_quality(self) -> Dict[str, Any]:
        """检查数据质量"""
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            quality_issues = []
            
            # 检查空值
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN room_guid IS NULL THEN 1 ELSE 0 END) as null_count
                FROM ods_room
                WHERE dt = CURDATE() - INTERVAL 1 DAY
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result['null_count'] > 0:
                quality_issues.append({
                    'table': 'ods_room',
                    'issue': '主键空值',
                    'count': result['null_count'],
                    'severity': 'high'
                })
            
            # 检查重复
            query = """
                SELECT room_guid, COUNT(*) as cnt
                FROM ods_room
                WHERE dt = CURDATE() - INTERVAL 1 DAY
                GROUP BY room_guid
                HAVING COUNT(*) > 1
                LIMIT 10
            """
            cursor.execute(query)
            duplicates = cursor.fetchall()
            
            if duplicates:
                quality_issues.append({
                    'table': 'ods_room',
                    'issue': '重复数据',
                    'count': len(duplicates),
                    'severity': 'medium'
                })
            
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'issues': quality_issues,
                'has_issues': len(quality_issues) > 0
            }
            
        except Exception as e:
            logger.error(f"❌ 检查数据质量失败：{e}")
            return {'success': False, 'error': str(e)}
    
    def send_alert(self, subject: str, message: str, severity: str = 'info'):
        """发送告警"""
        logger.warning(f"🚨 告警 [{severity}]: {subject}")
        logger.warning(message)
        
        # 邮件告警
        if self.alert_config['email_enabled']:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.alert_config['email_user']
                msg['To'] = ', '.join(self.alert_config['email_recipients'])
                msg['Subject'] = f"[ETL 告警] {subject}"
                
                body = f"""
ETL 监控告警

级别：{severity}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}

--
AI数据融合 监控系统
                """
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                server = smtplib.SMTP(
                    self.alert_config['email_smtp_server'],
                    self.alert_config['email_smtp_port']
                )
                server.starttls()
                server.login(
                    self.alert_config['email_user'],
                    self.alert_config['email_password']
                )
                server.send_message(msg)
                server.quit()
                
                logger.info("✅ 告警邮件已发送")
                
            except Exception as e:
                logger.error(f"❌ 发送告警邮件失败：{e}")
        
        # Webhook 告警（钉钉/企业微信）
        if self.alert_config['webhook_url']:
            try:
                import requests
                payload = {
                    'msgtype': 'text',
                    'text': {
                        'content': f"[ETL 告警] {severity}\n{subject}\n{message}"
                    }
                }
                requests.post(self.alert_config['webhook_url'], json=payload)
                logger.info("✅ 告警 Webhook 已发送")
            except Exception as e:
                logger.error(f"❌ 发送告警 Webhook 失败：{e}")
    
    def run_health_check(self) -> bool:
        """执行健康检查"""
        logger.info("=" * 60)
        logger.info("🏥 开始 ETL 健康检查")
        logger.info("=" * 60)
        
        alerts = []
        
        # 1. 检查 ETL 状态
        etl_status = self.check_etl_status()
        if etl_status.get('success'):
            failure_rate = etl_status.get('failure_rate', 0)
            if failure_rate > 50:
                alerts.append(f"ETL 失败率过高：{failure_rate:.1f}%")
            logger.info(f"✅ ETL 状态检查完成 - 成功率：{100-failure_rate:.1f}%")
        else:
            alerts.append("ETL 状态检查失败")
        
        # 2. 检查数据新鲜度
        freshness = self.check_data_freshness()
        if freshness.get('success'):
            if not freshness.get('all_fresh'):
                stale_tables = [t['table_name_cn'] for t in freshness['tables'] if not t['is_fresh']]
                alerts.append(f"数据未及时更新：{', '.join(stale_tables)}")
            logger.info(f"✅ 数据新鲜度检查完成 - {'全部及时' if freshness['all_fresh'] else '存在延迟'}")
        else:
            alerts.append("数据新鲜度检查失败")
        
        # 3. 检查数据质量
        quality = self.check_data_quality()
        if quality.get('success'):
            if quality.get('has_issues'):
                issues = [f"{i['table']}.{i['issue']}" for i in quality['issues']]
                alerts.append(f"数据质量问题：{', '.join(issues)}")
            logger.info(f"✅ 数据质量检查完成 - {'无问题' if not quality['has_issues'] else '存在问题'}")
        else:
            alerts.append("数据质量检查失败")
        
        # 发送告警
        if alerts:
            alert_message = "\n".join([f"  - {alert}" for alert in alerts])
            self.send_alert(
                subject="ETL 健康检查异常",
                message=f"发现以下问题:\n{alert_message}",
                severity='warning'
            )
            return False
        else:
            logger.info("✅ 健康检查通过 - 所有指标正常")
            return True


def main():
    """主函数"""
    monitor = ETLMonitor()
    success = monitor.run_health_check()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
