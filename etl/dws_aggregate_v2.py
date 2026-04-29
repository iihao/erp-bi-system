"""
DWS 层数据聚合脚本
依据：论文 4.2.3 节、4.3.2 节 DWD 层到 DWS 层数据聚合与建模实现
从 DWD 层明细数据聚合生成面向分析主题的事实表和维度表
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging
import os
from typing import Dict
import uuid

# 配置日志
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/dws_aggregate_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DWSAggregator:
    """DWS 层数据聚合类"""

    def __init__(self, dwd_config: Dict, dws_config: Dict):
        self.dwd_config = dwd_config
        self.dws_config = dws_config
        self.dwd_engine = None
        self.dws_engine = None

    def create_engines(self):
        """创建数据库连接引擎"""
        try:
            dwd_url = (
                f"mysql+pymysql://{self.dwd_config['user']}:{self.dwd_config['password']}@"
                f"{self.dwd_config['host']}:{self.dwd_config['port']}/{self.dwd_config['database']}?"
                f"charset=utf8mb4"
            )
            self.dwd_engine = create_engine(dwd_url, pool_size=10, pool_recycle=3600, echo=False)

            dws_url = (
                f"mysql+pymysql://{self.dws_config['user']}:{self.dws_config['password']}@"
                f"{self.dws_config['host']}:{self.dws_config['port']}/{self.dws_config['database']}?"
                f"charset=utf8mb4"
            )
            self.dws_engine = create_engine(dws_url, pool_size=10, pool_recycle=3600, echo=False)

            logger.info("数据库连接引擎创建成功")
            return True
        except SQLAlchemyError as e:
            logger.error(f"创建数据库连接失败：{str(e)}")
            return False

    def close_engines(self):
        """关闭数据库连接"""
        if self.dwd_engine:
            self.dwd_engine.dispose()
        if self.dws_engine:
            self.dws_engine.dispose()
        logger.info("数据库连接已关闭")

    def build_dim_date(self) -> int:
        """构建时间维度表"""
        logger.info("开始构建时间维度表...")

        try:
            # 使用存储过程生成
            with self.dws_engine.begin() as conn:
                conn.execute(text("CALL sp_init_dim_date()"))

            # 统计记录数
            result = conn.execute(text("SELECT COUNT(*) FROM Dim_date")).fetchone()
            count = result[0] if result else 0

            logger.info(f"时间维度表构建完成，记录数：{count}")
            return count

        except Exception as e:
            logger.error(f"构建时间维度表失败：{str(e)}")
            # 如果存储过程失败，使用 Python 生成
            return self._build_dim_date_python()

    def _build_dim_date_python(self) -> int:
        """使用 Python 生成时间维度数据"""
        try:
            start_date = datetime(2020, 1, 1)
            end_date = datetime(2030, 12, 31)
            current_date = start_date
            rows = []

            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']

            while current_date <= end_date:
                date_key = current_date.year * 10000 + current_date.month * 100 + current_date.day
                dow = current_date.weekday()
                is_weekend = 1 if dow >= 5 else 0

                rows.append({
                    'DateKey': date_key,
                    'FullDate': current_date,
                    'Year': current_date.year,
                    'Quarter': (current_date.month - 1) // 3 + 1,
                    'Month': current_date.month,
                    'Day': current_date.day,
                    'DayOfWeek': dow,
                    'DayName': day_names[dow],
                    'WeekOfYear': current_date.isocalendar()[1],
                    'MonthName': month_names[current_date.month - 1],
                    'IsWeekend': is_weekend,
                    'IsWorkday': 1 - is_weekend,
                    'FiscalYear': current_date.year,
                    'FiscalMonth': current_date.month,
                    'YearMonth': current_date.year * 100 + current_date.month
                })
                current_date += timedelta(days=1)

            df = pd.DataFrame(rows)
            df.to_sql('Dim_date', self.dws_engine, if_exists='replace', index=False, chunksize=1000)

            logger.info(f"时间维度表构建完成，记录数：{len(df)}")
            return len(df)

        except Exception as e:
            logger.error(f"Python 生成时间维度数据失败：{str(e)}")
            raise

    def build_dim_project(self) -> int:
        """构建项目维度表"""
        logger.info("开始构建项目维度表...")

        try:
            query = """
            SELECT DISTINCT
                ProjectGUID, ProjectName, '' as ProjectCode,
                '' as RegionGUID, ProjectName as RegionName,
                '' as CityGUID, '默认城市' as CityName,
                0 as GroupFlag, '住宅' as ProductType,
                '' as BuildingNo, '' as BuildingName,
                0 as TotalArea, 0 as TotalUnits,
                'active' as ProjectStatus,
                NULL as StartDate, NULL as EndDate,
                1 as IsCurrent, NOW() as EffectiveDate,
                NULL as ExpiryDate, NOW() as LoadTime
            FROM Dwd_room_detail
            WHERE ProjectGUID IS NOT NULL AND ProjectGUID != ''
            """

            df = pd.read_sql(query, self.dwd_engine)

            if df.empty:
                # 生成默认项目数据
                df = pd.DataFrame([{
                    'ProjectGUID': 'PROJ_001',
                    'ProjectName': '默认项目',
                    'ProjectCode': 'P001',
                    'RegionGUID': 'REG_001',
                    'RegionName': '默认区域',
                    'CityGUID': 'CITY_001',
                    'CityName': '默认城市',
                    'GroupFlag': 0,
                    'ProductType': '住宅',
                    'BuildingNo': '',
                    'BuildingName': '',
                    'TotalArea': 0,
                    'TotalUnits': 0,
                    'ProjectStatus': 'active',
                    'StartDate': None,
                    'EndDate': None,
                    'IsCurrent': 1,
                    'EffectiveDate': datetime.now(),
                    'ExpiryDate': None,
                    'LoadTime': datetime.now()
                }])

            # 添加代理键
            df['ProjectKey'] = range(1, len(df) + 1)

            # 重命名列顺序
            column_order = [
                'ProjectKey', 'ProjectGUID', 'ProjectCode', 'ProjectName',
                'CityGUID', 'CityName', 'RegionGUID', 'RegionName', 'GroupFlag',
                'ProductType', 'BuildingNo', 'BuildingName', 'TotalArea', 'TotalUnits',
                'ProjectStatus', 'StartDate', 'EndDate', 'IsCurrent',
                'EffectiveDate', 'ExpiryDate', 'LoadTime'
            ]
            df = df[[c for c in column_order if c in df.columns]]

            with self.dws_engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE Dim_project"))

            df.to_sql('Dim_project', self.dws_engine, if_exists='append', index=False, chunksize=1000)

            logger.info(f"项目维度表构建完成，记录数：{len(df)}")
            return len(df)

        except Exception as e:
            logger.error(f"构建项目维度表失败：{str(e)}")
            raise

    def build_dim_account(self) -> int:
        """构建科目维度表"""
        logger.info("开始构建科目维度表...")

        try:
            # 生成标准会计科目
            accounts = [
                {'AccountGUID': 'ACC_001', 'AccountCode': '1001', 'AccountName': '库存现金', 'AccountType': '资产', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '资产', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_002', 'AccountCode': '1002', 'AccountName': '银行存款', 'AccountType': '资产', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '资产', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_003', 'AccountCode': '1122', 'AccountName': '应收账款', 'AccountType': '资产', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '资产', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_004', 'AccountCode': '1405', 'AccountName': '库存商品', 'AccountType': '资产', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '资产', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_005', 'AccountCode': '1601', 'AccountName': '固定资产', 'AccountType': '资产', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '资产', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_006', 'AccountCode': '2001', 'AccountName': '短期借款', 'AccountType': '负债', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '负债', 'AccountDirection': '贷'},
                {'AccountGUID': 'ACC_007', 'AccountCode': '2202', 'AccountName': '应付账款', 'AccountType': '负债', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '负债', 'AccountDirection': '贷'},
                {'AccountGUID': 'ACC_008', 'AccountCode': '2211', 'AccountName': '应付职工薪酬', 'AccountType': '负债', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '负债', 'AccountDirection': '贷'},
                {'AccountGUID': 'ACC_009', 'AccountCode': '4001', 'AccountName': '实收资本', 'AccountType': '权益', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '权益', 'AccountDirection': '贷'},
                {'AccountGUID': 'ACC_010', 'AccountCode': '4101', 'AccountName': '盈余公积', 'AccountType': '权益', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '权益', 'AccountDirection': '贷'},
                {'AccountGUID': 'ACC_011', 'AccountCode': '5001', 'AccountName': '开发成本', 'AccountType': '成本', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '成本', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_012', 'AccountCode': '5002', 'AccountName': '开发间接费', 'AccountType': '成本', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '成本', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_013', 'AccountCode': '6001', 'AccountName': '主营业务收入', 'AccountType': '损益', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '损益', 'AccountDirection': '贷'},
                {'AccountGUID': 'ACC_014', 'AccountCode': '6401', 'AccountName': '主营业务成本', 'AccountType': '损益', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '损益', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_015', 'AccountCode': '6601', 'AccountName': '销售费用', 'AccountType': '损益', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '损益', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_016', 'AccountCode': '6602', 'AccountName': '管理费用', 'AccountType': '损益', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '损益', 'AccountDirection': '借'},
                {'AccountGUID': 'ACC_017', 'AccountCode': '6603', 'AccountName': '财务费用', 'AccountType': '损益', 'Level': 1, 'IsLeaf': 1, 'AccountCategory': '损益', 'AccountDirection': '借'},
            ]

            for i, acc in enumerate(accounts):
                acc['AccountKey'] = i + 1
                acc['ParentGUID'] = ''
                acc['ParentKey'] = None
                acc['AccountStatus'] = 'active'
                acc['IsCurrent'] = 1
                acc['EffectiveDate'] = datetime.now()
                acc['ExpiryDate'] = None
                acc['IsCashFlow'] = 0
                acc['AccountDirection'] = acc.get('AccountDirection', '借')
                acc['LoadTime'] = datetime.now()

            df = pd.DataFrame(accounts)

            with self.dws_engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE Dim_account"))

            df.to_sql('Dim_account', self.dws_engine, if_exists='append', index=False, chunksize=100)

            logger.info(f"科目维度表构建完成，记录数：{len(df)}")
            return len(df)

        except Exception as e:
            logger.error(f"构建科目维度表失败：{str(e)}")
            raise

    def build_sales_payment_fact(self) -> int:
        """构建销售 - 回款事实表"""
        logger.info("开始构建销售 - 回款事实表...")

        try:
            # SQL 聚合查询
            query = """
            SELECT
                t.ProjectGUID, t.ProjectName,
                t.RoomGUID, t.RoomNo,
                t.TradeGUID, t.ContractGUID,
                -- 日期维度键
                DATE_FORMAT(t.ContractSignDate, '%Y%m%d') as DateKey,
                -- 销售指标
                SUM(t.ContractAmount) as ContractAmount,
                COUNT(DISTINCT t.ContractGUID) as ContractCount,
                MAX(t.ContractSignDate) as SignedDate,
                -- 回款指标
                SUM(p.PaymentAmount) as PaymentAmount,
                COUNT(DISTINCT p.PayGUID) as PaymentCount,
                SUM(t.ContractAmount) - SUM(p.PaymentAmount) as UnpaidAmount,
                CASE
                    WHEN SUM(t.ContractAmount) > 0
                    THEN SUM(p.PaymentAmount) / SUM(t.ContractAmount)
                    ELSE 0
                END as PaymentRate
            FROM (
                SELECT
                    td.ProjectGUID,
                    pr.ProjectName,
                    td.RoomGUID,
                    rm.RoomNo,
                    td.TradeGUID,
                    td.ContractGUID,
                    td.ContractSignDate,
                    0 as ContractAmount,
                    0 as PaymentAmount,
                    '' as PayGUID
                FROM Dwd_trade_detail td
                LEFT JOIN Dwd_room_detail rm ON td.RoomGUID = rm.RoomGUID
                LEFT JOIN (
                    SELECT DISTINCT ProjectGUID, ProjectName FROM Dwd_room_detail
                ) pr ON td.ProjectGUID = pr.ProjectGUID
                WHERE td.ContractGUID IS NOT NULL AND td.ContractGUID != ''
            ) t
            LEFT JOIN (
                SELECT
                    ContractGUID,
                    SUM(PayAmount) as PaymentAmount,
                    GROUP_CONCAT(DISTINCT PayGUID) as PayGUID
                FROM Dwd_payment_detail
                WHERE DataStatus = 'valid'
                GROUP BY ContractGUID
            ) p ON t.ContractGUID = p.ContractGUID
            GROUP BY
                t.ProjectGUID, t.ProjectName,
                t.RoomGUID, t.RoomNo,
                t.TradeGUID, t.ContractGUID,
                DATE_FORMAT(t.ContractSignDate, '%Y%m%d')
            """

            df = pd.read_sql(query, self.dwd_engine)

            if df.empty:
                logger.warning("销售回款事实表无数据")
                return 0

            # 添加代理键和默认值
            df['FactKey'] = [self._generate_key() for _ in range(len(df))]
            df['DimProjectKey'] = range(1, len(df) + 1)
            df['DimRoomTypeKey'] = 1
            df['DimBuildingKey'] = 1
            df['ContractCount'] = df['ContractCount'].fillna(0).astype(int)
            df['PaymentCount'] = df['PaymentCount'].fillna(0).astype(int)
            df['PaymentRate'] = df['PaymentRate'].fillna(0).round(4)
            df['UnpaidAmount'] = df['UnpaidAmount'].fillna(0).round(2)
            df['PaymentAmount'] = df['PaymentAmount'].fillna(0).round(2)
            df['ContractAmount'] = df['ContractAmount'].fillna(0).round(2)
            df['OverdueAmount'] = 0.0
            df['OverdueDays'] = 0
            df['LoadTime'] = datetime.now()
            df['UpdateTime'] = datetime.now()

            # 选择目标列
            target_cols = [
                'FactKey', 'ProjectGUID', 'ProjectName', 'RoomGUID', 'RoomNo',
                'TradeGUID', 'ContractGUID', 'DateKey', 'DimProjectKey',
                'DimRoomTypeKey', 'DimBuildingKey', 'ContractAmount', 'ContractCount',
                'SignedDate', 'PaymentAmount', 'PaymentCount', 'UnpaidAmount',
                'PaymentRate', 'OverdueAmount', 'OverdueDays', 'LoadTime', 'UpdateTime'
            ]
            df = df[[c for c in target_cols if c in df.columns]]

            with self.dws_engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE Dws_sales_payment_fact"))

            df.to_sql('Dws_sales_payment_fact', self.dws_engine, if_exists='append', index=False, chunksize=1000)

            logger.info(f"销售 - 回款事实表构建完成，记录数：{len(df)}")
            return len(df)

        except Exception as e:
            logger.error(f"构建销售 - 回款事实表失败：{str(e)}")
            raise

    def build_cost_expense_fact(self) -> int:
        """构建成本 - 费用事实表"""
        logger.info("开始构建成本 - 费用事实表...")

        try:
            query = """
            SELECT
                c.ProjectGUID, pr.ProjectName,
                c.ContractGUID, c.AccountGUID,
                DATE_FORMAT(c.SignDate, '%Y%m%d') as DateKey,
                c.ContractType, c.ContractName, c.PartyB,
                SUM(c.ContractAmount) as ContractAmount,
                SUM(c.PaidAmount) as PaidAmount,
                SUM(c.UnpaidAmount) as UnpaidAmount,
                0 as BudgetAmount, 0 as BudgetVariance, 0 as BudgetVarianceRate,
                0 as ExpenseAmount, '' as ExpenseType
            FROM Dwd_contract_detail c
            LEFT JOIN (
                SELECT DISTINCT ProjectGUID, ProjectName FROM Dwd_room_detail
            ) pr ON c.ProjectGUID = pr.ProjectGUID
            WHERE c.DataStatus = 'valid'
            GROUP BY
                c.ProjectGUID, pr.ProjectName,
                c.ContractGUID, c.AccountGUID,
                DATE_FORMAT(c.SignDate, '%Y%m%d'),
                c.ContractType, c.ContractName, c.PartyB
            """

            df = pd.read_sql(query, self.dwd_engine)

            if df.empty:
                logger.warning("成本费用事实表无数据")
                return 0

            df['FactKey'] = [self._generate_key() for _ in range(len(df))]
            df['DimProjectKey'] = range(1, len(df) + 1)
            df['DimAccountKey'] = range(1, len(df) + 1)
            df['DimCostCenterKey'] = 1
            df['LoadTime'] = datetime.now()
            df['UpdateTime'] = datetime.now()

            target_cols = [
                'FactKey', 'ProjectGUID', 'ProjectName', 'ContractGUID', 'AccountGUID',
                'DateKey', 'DimProjectKey', 'DimAccountKey', 'DimCostCenterKey',
                'ContractType', 'ContractName', 'PartyB', 'ContractAmount',
                'PaidAmount', 'UnpaidAmount', 'BudgetAmount', 'BudgetVariance',
                'BudgetVarianceRate', 'ExpenseAmount', 'ExpenseType', 'LoadTime', 'UpdateTime'
            ]
            df = df[[c for c in target_cols if c in df.columns]]

            with self.dws_engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE Dws_cost_expense_fact"))

            df.to_sql('Dws_cost_expense_fact', self.dws_engine, if_exists='append', index=False, chunksize=1000)

            logger.info(f"成本 - 费用事实表构建完成，记录数：{len(df)}")
            return len(df)

        except Exception as e:
            logger.error(f"构建成本 - 费用事实表失败：{str(e)}")
            raise

    def _generate_key(self) -> str:
        """生成代理键"""
        return f"FACT_{uuid.uuid4().hex[:16]}"

    def run_full_aggregation(self):
        """执行全量聚合"""
        logger.info("=" * 50)
        logger.info("开始执行 DWS 层全量数据聚合")
        logger.info("=" * 50)

        results = {}
        try:
            results['Dim_date'] = self.build_dim_date()
            results['Dim_project'] = self.build_dim_project()
            results['Dim_account'] = self.build_dim_account()
            results['Dws_sales_payment_fact'] = self.build_sales_payment_fact()
            results['Dws_cost_expense_fact'] = self.build_cost_expense_fact()

            logger.info("=" * 50)
            logger.info("DWS 层全量聚合完成")
            logger.info(f"聚合结果：{results}")
            logger.info("=" * 50)

            return results

        except Exception as e:
            logger.error(f"DWS 层全量聚合失败：{str(e)}")
            raise
        finally:
            self.close_engines()


def main():
    """主函数"""
    dwd_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': 'erp_dwd',
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }

    dws_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': 'erp_dws',
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }

    aggregator = DWSAggregator(dwd_config, dws_config)

    if not aggregator.create_engines():
        logger.error("创建数据库连接失败，退出程序")
        return

    try:
        aggregator.run_full_aggregation()
        logger.info("DWS 层数据聚合成功完成")
    except Exception as e:
        logger.error(f"DWS 层数据聚合失败：{str(e)}")


if __name__ == '__main__':
    main()
