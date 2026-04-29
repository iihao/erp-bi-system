"""
ODS 层数据抽取脚本
依据：论文 4.2.3 节、4.3 节 ETL 过程设计
从 MySQL 业务数据库抽取原始数据到 ODS（操作数据存储）层
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging
import os
from typing import Optional, Dict, List

# 配置日志
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/ods_extract_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ODSExtractor:
    """ODS 层数据抽取类"""

    def __init__(self, source_config: Dict, ods_config: Dict):
        """
        初始化抽取器

        Args:
            source_config: 源数据库配置
            ods_config: ODS 数据库配置
        """
        self.source_config = source_config
        self.ods_config = ods_config
        self.source_engine = None
        self.ods_engine = None

    def create_engines(self):
        """创建数据库连接引擎"""
        try:
            # 源数据库连接
            source_url = (
                f"mysql+pymysql://{self.source_config['user']}:{self.source_config['password']}@"
                f"{self.source_config['host']}:{self.source_config['port']}/{self.source_config['database']}?"
                f"charset=utf8mb4"
            )
            self.source_engine = create_engine(source_url, pool_size=10, pool_recycle=3600, echo=False)

            # ODS 数据库连接
            ods_url = (
                f"mysql+pymysql://{self.ods_config['user']}:{self.ods_config['password']}@"
                f"{self.ods_config['host']}:{self.ods_config['port']}/{self.ods_config['database']}?"
                f"charset=utf8mb4"
            )
            self.ods_engine = create_engine(ods_url, pool_size=10, pool_recycle=3600, echo=False)

            logger.info("数据库连接引擎创建成功")
            return True

        except SQLAlchemyError as e:
            logger.error(f"创建数据库连接失败：{str(e)}")
            return False

    def close_engines(self):
        """关闭数据库连接"""
        if self.source_engine:
            self.source_engine.dispose()
        if self.ods_engine:
            self.ods_engine.dispose()
        logger.info("数据库连接已关闭")

    def extract_full(
        self,
        source_table: str,
        ods_table: str,
        columns: Optional[List[str]] = None
    ) -> int:
        """
        全量抽取单表数据

        Args:
            source_table: 源表名
            ods_table: ODS 目标表名
            columns: 要抽取的列

        Returns:
            抽取的记录数
        """
        try:
            # 构建查询
            if columns:
                cols_str = ', '.join(columns)
                query = f"SELECT {cols_str} FROM {source_table}"
            else:
                query = f"SELECT * FROM {source_table}"

            # 读取源数据
            df = pd.read_sql(query, self.source_engine)

            if df.empty:
                logger.warning(f"源表 {source_table} 无数据")
                return 0

            # 添加抽取时间
            df['ExtractTime'] = datetime.now()

            # 写入 ODS 表
            df.to_sql(
                ods_table,
                self.ods_engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )

            logger.info(f"全量抽取 {source_table} -> {ods_table}, 记录数：{len(df)}")
            return len(df)

        except SQLAlchemyError as e:
            logger.error(f"抽取表 {source_table} 失败：{str(e)}")
            raise

    def extract_incremental(
        self,
        source_table: str,
        ods_table: str,
        incremental_field: str,
        last_extract_time: Optional[datetime] = None
    ) -> int:
        """
        增量抽取单表数据

        Args:
            source_table: 源表名
            ods_table: ODS 目标表名
            incremental_field: 增量字段（如 updated_at, created_at）
            last_extract_time: 上次抽取时间

        Returns:
            抽取的记录数
        """
        try:
            # 如果没有指定上次抽取时间，使用默认值（7 天前）
            if last_extract_time is None:
                last_extract_time = datetime.now() - timedelta(days=7)

            # 构建增量查询
            query = f"""
                SELECT * FROM {source_table}
                WHERE {incremental_field} >= :last_time
                ORDER BY {incremental_field}
            """

            # 读取源数据
            df = pd.read_sql(text(query), self.source_engine, params={'last_time': last_extract_time})

            if df.empty:
                logger.info(f"增量抽取 {source_table} 无新增数据")
                return 0

            # 添加抽取时间
            df['ExtractTime'] = datetime.now()

            # 写入 ODS 表
            df.to_sql(
                ods_table,
                self.ods_engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )

            logger.info(f"增量抽取 {source_table} -> {ods_table}, 新增记录数：{len(df)}")
            return len(df)

        except SQLAlchemyError as e:
            logger.error(f"增量抽取表 {source_table} 失败：{str(e)}")
            raise

    def extract_room(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取房间数据"""
        columns = [
            'RoomGUID', 'RoomNo', 'ProjectGUID', 'ProjectName', 'BuildingNo', 'BuildingName',
            'UnitNo', 'FloorNo', 'Area', 'InnerArea', 'PublicArea', 'RoomType', 'RoomStatus',
            'Price', 'UnitPrice', 'Orientation', 'Remark',
            'CreatedGUID', 'CreatedName', 'CreatedTime',
            'ModifiedGUID', 'ModifiedName', 'ModifiedTime', 'VersionNumber'
        ]
        if incremental:
            return self.extract_incremental('rooms', 'ODS_room', 'ModifiedTime', last_time)
        else:
            return self.extract_full('rooms', 'ODS_room', columns)

    def extract_trade(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取销售数据"""
        columns = [
            'TradeGUID', 'BUGUID', 'BuyerAllCardIds', 'BuyerAllNames', 'CloseReason',
            'ContractGUID', 'ContractQsDate', 'ContractYwgsDate', 'IsExistDelayPay',
            'LastGjDate', 'PreTradeGUID', 'ProjGUID', 'RGOrderGUID', 'RGOrderQsDate',
            'RGOrderType', 'RoomGUID', 'RoomStatus', 'TradeStatus',
            'CreatedGUID', 'CreatedName', 'CreatedTime',
            'ModifiedGUID', 'ModifiedName', 'ModifiedTime', 'VersionNumber'
        ]
        if incremental:
            return self.extract_incremental('trades', 'ODS_trade', 'ModifiedTime', last_time)
        else:
            return self.extract_full('trades', 'ODS_trade', columns)

    def extract_payment(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取回款数据"""
        columns = [
            'PayGUID', 'TradeGUID', 'ContractGUID', 'ProjGUID', 'PayAmount', 'PayDate',
            'PayType', 'PayWay', 'BankName', 'LoanType', 'PayStatus', 'Remark',
            'CreatedGUID', 'CreatedName', 'CreatedTime',
            'ModifiedGUID', 'ModifiedName', 'ModifiedTime', 'VersionNumber'
        ]
        if incremental:
            return self.extract_incremental('payments', 'ODS_payment', 'ModifiedTime', last_time)
        else:
            return self.extract_full('payments', 'ODS_payment', columns)

    def extract_pay(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取付款数据"""
        columns = [
            'PayRegGUID', 'ProjGUID', 'ContractGUID', 'PayRegAmount', 'PayRegDate',
            'PayType', 'PayeeName', 'PayeeBank', 'PayeeAccount', 'InvoiceNo', 'PayStatus', 'Remark',
            'CreatedGUID', 'CreatedName', 'CreatedTime',
            'ModifiedGUID', 'ModifiedName', 'ModifiedTime', 'VersionNumber'
        ]
        if incremental:
            return self.extract_incremental('pay_register', 'ODS_pay', 'ModifiedTime', last_time)
        else:
            return self.extract_full('pay_register', 'ODS_pay', columns)

    def extract_account(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取科目数据"""
        columns = [
            'AccountGUID', 'AccountCode', 'AccountName', 'AccountType', 'ParentGUID',
            'Level', 'IsLeaf', 'ProjGUID', 'Status', 'Remark',
            'CreatedGUID', 'CreatedName', 'CreatedTime',
            'ModifiedGUID', 'ModifiedName', 'ModifiedTime', 'VersionNumber'
        ]
        if incremental:
            return self.extract_incremental('accounts', 'ODS_account', 'ModifiedTime', last_time)
        else:
            return self.extract_full('accounts', 'ODS_account', columns)

    def extract_contract(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取合同数据"""
        columns = [
            'ContractGUID', 'ContractCode', 'ContractName', 'ContractType', 'ProjGUID',
            'PartyA', 'PartyB', 'SignDate', 'StartDate', 'EndDate',
            'ContractAmount', 'PaidAmount', 'UnpaidAmount', 'AccountGUID', 'ContractStatus', 'Remark',
            'CreatedGUID', 'CreatedName', 'CreatedTime',
            'ModifiedGUID', 'ModifiedName', 'ModifiedTime', 'VersionNumber'
        ]
        if incremental:
            return self.extract_incremental('contracts', 'ODS_contract', 'ModifiedTime', last_time)
        else:
            return self.extract_full('contracts', 'ODS_contract', columns)

    def extract_bseg(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取 SAP 凭证数据"""
        columns = [
            'BsegGUID', 'Bukrs', 'Belnr', 'Gjahr', 'Buzei', 'HKONT', 'Sghsl', 'Wrbsl',
            'Meins', 'Kstar', 'Kostl', 'ProjGUID', 'Bldat', 'Budat', 'Shkzg', 'Bstat',
            'Xblnr', 'Sgut1', 'Txt50'
        ]
        if incremental:
            return self.extract_incremental('sap_bseg', 'ODS_bseg', 'Budat', last_time)
        else:
            return self.extract_full('sap_bseg', 'ODS_bseg', columns)

    def extract_gl_actual(self, incremental: bool = False, last_time: Optional[datetime] = None) -> int:
        """抽取 SAP 总账实际数据"""
        columns = [
            'GlActualGUID', 'RYear', 'Rcver', 'Tvers', 'Lednr', 'Rdart', 'Sltpo',
            'HkmtArt', 'HkmtNr', 'Kstar', 'Kostl', 'ProjGUID', 'Prctr', 'CurrType',
            'Hsl', 'Ksl', 'Osl', 'Twaer', 'Menge', 'Meins'
        ]
        if incremental:
            return self.extract_incremental('sap_gl_actual', 'ODS_GL_Actual', 'RYear', last_time)
        else:
            return self.extract_full('sap_gl_actual', 'ODS_GL_Actual', columns)

    def run_full_extraction(self):
        """执行全量抽取"""
        logger.info("=" * 50)
        logger.info("开始执行 ODS 层全量数据抽取")
        logger.info("=" * 50)

        results = {}
        try:
            # 明源云 ERP 数据
            results['ODS_room'] = self.extract_room(incremental=False)
            results['ODS_trade'] = self.extract_trade(incremental=False)
            results['ODS_payment'] = self.extract_payment(incremental=False)
            results['ODS_pay'] = self.extract_pay(incremental=False)
            results['ODS_account'] = self.extract_account(incremental=False)
            results['ODS_contract'] = self.extract_contract(incremental=False)

            # SAP 财务数据
            results['ODS_bseg'] = self.extract_bseg(incremental=False)
            results['ODS_GL_Actual'] = self.extract_gl_actual(incremental=False)

            logger.info("=" * 50)
            logger.info("ODS 层全量抽取完成")
            logger.info(f"抽取结果：{results}")
            logger.info("=" * 50)

            return results

        except Exception as e:
            logger.error(f"ODS 层全量抽取失败：{str(e)}")
            raise
        finally:
            self.close_engines()

    def run_incremental_extraction(self):
        """执行增量抽取"""
        logger.info("=" * 50)
        logger.info("开始执行 ODS 层增量数据抽取")
        logger.info("=" * 50)

        last_time = datetime.now() - timedelta(days=1)
        results = {}
        try:
            # 明源云 ERP 数据（增量）
            results['ODS_room'] = self.extract_room(incremental=True, last_time=last_time)
            results['ODS_trade'] = self.extract_trade(incremental=True, last_time=last_time)
            results['ODS_payment'] = self.extract_payment(incremental=True, last_time=last_time)
            results['ODS_pay'] = self.extract_pay(incremental=True, last_time=last_time)
            results['ODS_contract'] = self.extract_contract(incremental=True, last_time=last_time)

            # SAP 财务数据（增量）
            results['ODS_bseg'] = self.extract_bseg(incremental=True, last_time=last_time)
            results['ODS_GL_Actual'] = self.extract_gl_actual(incremental=True, last_time=last_time)

            logger.info("=" * 50)
            logger.info("ODS 层增量抽取完成")
            logger.info(f"抽取结果：{results}")
            logger.info("=" * 50)

            return results

        except Exception as e:
            logger.error(f"ODS 层增量抽取失败：{str(e)}")
            raise
        finally:
            self.close_engines()


def main():
    """主函数"""
    # 数据库配置
    source_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': 'erp_source',
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }

    ods_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': 'erp_ods',
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }

    # 创建抽取器
    extractor = ODSExtractor(source_config, ods_config)

    if not extractor.create_engines():
        logger.error("创建数据库连接失败，退出程序")
        return

    # 执行抽取
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'

    try:
        if mode == 'incremental':
            extractor.run_incremental_extraction()
        else:
            extractor.run_full_extraction()
        logger.info("ODS 层数据抽取成功完成")
    except Exception as e:
        logger.error(f"ODS 层数据抽取失败：{str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
