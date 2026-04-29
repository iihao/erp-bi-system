"""
DWD 层数据清洗脚本
依据：论文 4.2.3 节、4.3.2 节 ODS 层到 DWD 层数据清洗实现
从 ODS 层抽取原始数据，经过标准化清洗后加载到 DWD 层
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional
import uuid

# 配置日志
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/dwd_clean_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DWDCleaner:
    """DWD 层数据清洗类"""

    def __init__(self, ods_config: Dict, dwd_config: Dict):
        """
        初始化清洗器

        Args:
            ods_config: ODS 数据库配置
            dwd_config: DWD 数据库配置
        """
        self.ods_config = ods_config
        self.dwd_config = dwd_config
        self.ods_engine = None
        self.dwd_engine = None

    def create_engines(self):
        """创建数据库连接引擎"""
        try:
            # ODS 数据库连接
            ods_url = (
                f"mysql+pymysql://{self.ods_config['user']}:{self.ods_config['password']}@"
                f"{self.ods_config['host']}:{self.ods_config['port']}/{self.ods_config['database']}?"
                f"charset=utf8mb4"
            )
            self.ods_engine = create_engine(ods_url, pool_size=10, pool_recycle=3600, echo=False)

            # DWD 数据库连接
            dwd_url = (
                f"mysql+pymysql://{self.dwd_config['user']}:{self.dwd_config['password']}@"
                f"{self.dwd_config['host']}:{self.dwd_config['port']}/{self.dwd_config['database']}?"
                f"charset=utf8mb4"
            )
            self.dwd_engine = create_engine(dwd_url, pool_size=10, pool_recycle=3600, echo=False)

            logger.info("数据库连接引擎创建成功")
            return True

        except SQLAlchemyError as e:
            logger.error(f"创建数据库连接失败：{str(e)}")
            return False

    def close_engines(self):
        """关闭数据库连接"""
        if self.ods_engine:
            self.ods_engine.dispose()
        if self.dwd_engine:
            self.dwd_engine.dispose()
        logger.info("数据库连接已关闭")

    def generate_key(self, prefix: str) -> str:
        """生成代理键"""
        return f"{prefix}_{uuid.uuid4().hex}"

    def clean_room_data(self) -> int:
        """
        清洗房间数据
        从 ODS_room 清洗到 Dwd_room_detail
        """
        logger.info("开始清洗房间数据...")

        try:
            # 读取 ODS 数据
            query = "SELECT * FROM ODS_room WHERE 1=1"
            df = pd.read_sql(query, self.ods_engine)

            if df.empty:
                logger.warning("ODS_room 无数据")
                return 0

            # 数据清洗规则
            cleaned_rows = []
            error_rows = []

            for _, row in df.iterrows():
                try:
                    # 标准化房间状态
                    room_status = str(row.get('RoomStatus', '')).strip()
                    if room_status in ['可售', 'Available']:
                        room_status = 'available'
                    elif room_status in ['已售', 'Sold']:
                        room_status = 'sold'
                    elif room_status in ['已签约', 'Signed']:
                        room_status = 'signed'
                    elif room_status in ['已认购', 'Subscribed']:
                        room_status = 'subscribed'
                    else:
                        room_status = 'unknown'

                    # 数据有效性校验
                    if not row.get('RoomGUID'):
                        error_rows.append({
                            'source': 'ODS_room',
                            'error': '缺少 RoomGUID',
                            'data': row.to_dict()
                        })
                        continue

                    # 面积校验
                    area = float(row.get('Area', 0) or 0)
                    if area <= 0:
                        error_rows.append({
                            'source': 'ODS_room',
                            'error': f'面积异常：{area}',
                            'data': row.to_dict()
                        })
                        continue

                    # 价格校验
                    price = float(row.get('Price', 0) or 0)
                    if price < 0:
                        error_rows.append({
                            'source': 'ODS_room',
                            'error': f'价格异常：{price}',
                            'data': row.to_dict()
                        })
                        continue

                    cleaned_rows.append({
                        'RoomKey': self.generate_key('room'),
                        'RoomGUID': row['RoomGUID'],
                        'RoomNo': row.get('RoomNo', ''),
                        'ProjectGUID': row.get('ProjectGUID', ''),
                        'ProjectName': row.get('ProjectName', ''),
                        'BuildingNo': row.get('BuildingNo', ''),
                        'BuildingName': row.get('BuildingName', ''),
                        'UnitNo': row.get('UnitNo', ''),
                        'FloorNo': int(row.get('FloorNo', 0) or 0),
                        'Area': round(area, 2),
                        'InnerArea': round(float(row.get('InnerArea', 0) or 0), 2),
                        'PublicArea': round(float(row.get('PublicArea', 0) or 0), 2),
                        'RoomType': row.get('RoomType', ''),
                        'RoomStatus': room_status,
                        'Price': round(price, 2),
                        'UnitPrice': round(float(row.get('UnitPrice', 0) or 0), 2),
                        'Orientation': row.get('Orientation', ''),
                        'DataStatus': 'valid',
                        'ExtractTime': row.get('ExtractTime'),
                        'LoadTime': datetime.now()
                    })

                except Exception as e:
                    error_rows.append({
                        'source': 'ODS_room',
                        'error': str(e),
                        'data': row.to_dict()
                    })

            # 转换 DataFrame
            cleaned_df = pd.DataFrame(cleaned_rows)

            if not cleaned_df.empty:
                # 清空目标表（全量刷新）
                with self.dwd_engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE Dwd_room_detail"))

                # 写入 DWD 表
                cleaned_df.to_sql(
                    'Dwd_room_detail',
                    self.dwd_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )

            # 记录错误数据
            if error_rows:
                self.log_errors(error_rows)

            logger.info(f"房间数据清洗完成，有效记录：{len(cleaned_rows)}, 错误记录：{len(error_rows)}")
            return len(cleaned_rows)

        except Exception as e:
            logger.error(f"清洗房间数据失败：{str(e)}")
            raise

    def clean_trade_data(self) -> int:
        """
        清洗销售数据
        从 ODS_trade 清洗到 Dwd_trade_detail
        """
        logger.info("开始清洗销售数据...")

        try:
            query = "SELECT * FROM ODS_trade WHERE 1=1"
            df = pd.read_sql(query, self.ods_engine)

            if df.empty:
                logger.warning("ODS_trade 无数据")
                return 0

            cleaned_rows = []
            error_rows = []

            for _, row in df.iterrows():
                try:
                    # 标准化交易状态
                    trade_status = str(row.get('TradeStatus', '')).strip().lower()
                    if trade_status in ['正常', 'normal', 'active']:
                        trade_status = 'normal'
                    elif trade_status in ['已关闭', 'closed', 'close']:
                        trade_status = 'closed'
                    elif trade_status in ['已签约', 'signed']:
                        trade_status = 'signed'
                    elif trade_status in ['已认购', 'subscribed']:
                        trade_status = 'subscribed'
                    else:
                        trade_status = 'pending'

                    # 数据有效性校验
                    if not row.get('TradeGUID'):
                        error_rows.append({'source': 'ODS_trade', 'error': '缺少 TradeGUID', 'data': row.to_dict()})
                        continue

                    # 认购日期标准化
                    sub_date = row.get('RGOrderQsDate')
                    if isinstance(sub_date, str) and sub_date:
                        try:
                            sub_date = datetime.strptime(sub_date[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            sub_date = None

                    # 签约日期标准化
                    contract_date = row.get('ContractQsDate')
                    if isinstance(contract_date, str) and contract_date:
                        try:
                            contract_date = datetime.strptime(contract_date[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            contract_date = None

                    cleaned_rows.append({
                        'TradeKey': self.generate_key('trade'),
                        'TradeGUID': row['TradeGUID'],
                        'CompanyGUID': row.get('BUGUID', ''),
                        'BuyerAllCardIds': row.get('BuyerAllCardIds', ''),
                        'BuyerAllNames': row.get('BuyerAllNames', ''),
                        'CloseReason': row.get('CloseReason', ''),
                        'ContractGUID': row.get('ContractGUID', ''),
                        'ContractSignDate': contract_date,
                        'ContractBizDate': row.get('ContractYwgsDate'),
                        'HasDelayPay': 1 if row.get('IsExistDelayPay') else 0,
                        'LastFollowDate': row.get('LastGjDate'),
                        'PreTradeGUID': row.get('PreTradeGUID', ''),
                        'ProjectGUID': row.get('ProjGUID', ''),
                        'SubGUID': row.get('RGOrderGUID', ''),
                        'SubDate': sub_date,
                        'SubType': row.get('RGOrderType', ''),
                        'RoomGUID': row.get('RoomGUID', ''),
                        'RoomStatus': row.get('RoomStatus', ''),
                        'TradeStatus': trade_status,
                        'CreatorGUID': row.get('CreatedGUID', ''),
                        'CreatorName': row.get('CreatedName', ''),
                        'CreateTime': row.get('CreatedTime'),
                        'ModifierGUID': row.get('ModifiedGUID', ''),
                        'ModifierName': row.get('ModifiedName', ''),
                        'ModifyTime': row.get('ModifiedTime'),
                        'DataStatus': 'valid',
                        'ExtractTime': row.get('ExtractTime'),
                        'LoadTime': datetime.now()
                    })

                except Exception as e:
                    error_rows.append({'source': 'ODS_trade', 'error': str(e), 'data': row.to_dict()})

            cleaned_df = pd.DataFrame(cleaned_rows)

            if not cleaned_df.empty:
                with self.dwd_engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE Dwd_trade_detail"))

                cleaned_df.to_sql(
                    'Dwd_trade_detail',
                    self.dwd_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )

            if error_rows:
                self.log_errors(error_rows)

            logger.info(f"销售数据清洗完成，有效记录：{len(cleaned_rows)}, 错误记录：{len(error_rows)}")
            return len(cleaned_rows)

        except Exception as e:
            logger.error(f"清洗销售数据失败：{str(e)}")
            raise

    def clean_payment_data(self) -> int:
        """
        清洗回款数据
        从 ODS_payment 清洗到 Dwd_payment_detail
        """
        logger.info("开始清洗回款数据...")

        try:
            query = "SELECT * FROM ODS_payment WHERE 1=1"
            df = pd.read_sql(query, self.ods_engine)

            if df.empty:
                logger.warning("ODS_payment 无数据")
                return 0

            cleaned_rows = []
            error_rows = []

            for _, row in df.iterrows():
                try:
                    # 金额标准化（保留 2 位小数）
                    pay_amount = float(row.get('PayAmount', 0) or 0)
                    if pay_amount <= 0:
                        error_rows.append({
                            'source': 'ODS_payment',
                            'error': f'回款金额异常：{pay_amount}',
                            'data': row.to_dict()
                        })
                        continue

                    # 回款状态标准化
                    pay_status = str(row.get('PayStatus', '')).strip().lower()
                    if pay_status in ['已确认', 'confirmed', 'success']:
                        pay_status = 'confirmed'
                    elif pay_status in ['待确认', 'pending']:
                        pay_status = 'pending'
                    elif pay_status in ['已驳回', 'rejected']:
                        pay_status = 'rejected'
                    else:
                        pay_status = 'unknown'

                    # 回款日期标准化
                    pay_date = row.get('PayDate')
                    if isinstance(pay_date, str) and pay_date:
                        try:
                            pay_date = datetime.strptime(pay_date[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            pay_date = None

                    cleaned_rows.append({
                        'PaymentKey': self.generate_key('payment'),
                        'PayGUID': row['PayGUID'],
                        'TradeGUID': row.get('TradeGUID', ''),
                        'ContractGUID': row.get('ContractGUID', ''),
                        'ProjectGUID': row.get('ProjGUID', ''),
                        'PayAmount': round(pay_amount, 2),
                        'PayDate': pay_date,
                        'PayType': row.get('PayType', ''),
                        'PayWay': row.get('PayWay', ''),
                        'BankName': row.get('BankName', ''),
                        'LoanType': row.get('LoanType', ''),
                        'PayStatus': pay_status,
                        'DataStatus': 'valid',
                        'ExtractTime': row.get('ExtractTime'),
                        'LoadTime': datetime.now()
                    })

                except Exception as e:
                    error_rows.append({'source': 'ODS_payment', 'error': str(e), 'data': row.to_dict()})

            cleaned_df = pd.DataFrame(cleaned_rows)

            if not cleaned_df.empty:
                with self.dwd_engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE Dwd_payment_detail"))

                cleaned_df.to_sql(
                    'Dwd_payment_detail',
                    self.dwd_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )

            if error_rows:
                self.log_errors(error_rows)

            logger.info(f"回款数据清洗完成，有效记录：{len(cleaned_rows)}, 错误记录：{len(error_rows)}")
            return len(cleaned_rows)

        except Exception as e:
            logger.error(f"清洗回款数据失败：{str(e)}")
            raise

    def clean_contract_data(self) -> int:
        """清洗合同数据"""
        logger.info("开始清洗合同数据...")

        try:
            query = "SELECT * FROM ODS_contract WHERE 1=1"
            df = pd.read_sql(query, self.ods_engine)

            if df.empty:
                logger.warning("ODS_contract 无数据")
                return 0

            cleaned_rows = []
            error_rows = []

            for _, row in df.iterrows():
                try:
                    # 金额标准化
                    contract_amount = float(row.get('ContractAmount', 0) or 0)
                    paid_amount = float(row.get('PaidAmount', 0) or 0)
                    unpaid_amount = float(row.get('UnpaidAmount', 0) or 0)

                    # 合同状态标准化
                    contract_status = str(row.get('ContractStatus', '')).strip().lower()
                    if contract_status in ['履行中', 'active', 'performing']:
                        contract_status = 'performing'
                    elif contract_status in ['已完成', 'completed', 'finished']:
                        contract_status = 'completed'
                    elif contract_status in ['已终止', 'terminated', 'cancelled']:
                        contract_status = 'terminated'
                    else:
                        contract_status = 'pending'

                    cleaned_rows.append({
                        'ContractKey': self.generate_key('contract'),
                        'ContractGUID': row['ContractGUID'],
                        'ContractCode': row.get('ContractCode', ''),
                        'ContractName': row.get('ContractName', ''),
                        'ContractType': row.get('ContractType', ''),
                        'ProjectGUID': row.get('ProjGUID', ''),
                        'PartyA': row.get('PartyA', ''),
                        'PartyB': row.get('PartyB', ''),
                        'SignDate': row.get('SignDate'),
                        'StartDate': row.get('StartDate'),
                        'EndDate': row.get('EndDate'),
                        'ContractAmount': round(contract_amount, 2),
                        'PaidAmount': round(paid_amount, 2),
                        'UnpaidAmount': round(unpaid_amount, 2),
                        'AccountGUID': row.get('AccountGUID', ''),
                        'AccountCode': '',  # 从维度表关联获取
                        'ContractStatus': contract_status,
                        'DataStatus': 'valid',
                        'ExtractTime': row.get('ExtractTime'),
                        'LoadTime': datetime.now()
                    })

                except Exception as e:
                    error_rows.append({'source': 'ODS_contract', 'error': str(e), 'data': row.to_dict()})

            cleaned_df = pd.DataFrame(cleaned_rows)

            if not cleaned_df.empty:
                with self.dwd_engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE Dwd_contract_detail"))

                cleaned_df.to_sql(
                    'Dwd_contract_detail',
                    self.dwd_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )

            if error_rows:
                self.log_errors(error_rows)

            logger.info(f"合同数据清洗完成，有效记录：{len(cleaned_rows)}, 错误记录：{len(error_rows)}")
            return len(cleaned_rows)

        except Exception as e:
            logger.error(f"清洗合同数据失败：{str(e)}")
            raise

    def clean_pay_data(self) -> int:
        """清洗付款数据"""
        logger.info("开始清洗付款数据...")

        try:
            query = "SELECT * FROM ODS_pay WHERE 1=1"
            df = pd.read_sql(query, self.ods_engine)

            if df.empty:
                logger.warning("ODS_pay 无数据")
                return 0

            cleaned_rows = []

            for _, row in df.iterrows():
                try:
                    pay_amount = float(row.get('PayRegAmount', 0) or 0)
                    has_contract = 1 if row.get('ContractGUID') else 0

                    cleaned_rows.append({
                        'PayRegKey': self.generate_key('pay'),
                        'PayRegGUID': row['PayRegGUID'],
                        'ProjectGUID': row.get('ProjGUID', ''),
                        'ContractGUID': row.get('ContractGUID', ''),
                        'PayRegAmount': round(pay_amount, 2),
                        'PayRegDate': row.get('PayRegDate'),
                        'PayType': row.get('PayType', ''),
                        'PayeeName': row.get('PayeeName', ''),
                        'PayeeBank': row.get('PayeeBank', ''),
                        'PayeeAccount': row.get('PayeeAccount', ''),
                        'InvoiceNo': row.get('InvoiceNo', ''),
                        'PayStatus': row.get('PayStatus', ''),
                        'HasContract': has_contract,
                        'DataStatus': 'valid' if pay_amount > 0 else 'invalid',
                        'ExtractTime': row.get('ExtractTime'),
                        'LoadTime': datetime.now()
                    })

                except Exception as e:
                    continue

            cleaned_df = pd.DataFrame(cleaned_rows)

            if not cleaned_df.empty:
                with self.dwd_engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE Dwd_pay_detail"))

                cleaned_df.to_sql(
                    'Dwd_pay_detail',
                    self.dwd_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )

            logger.info(f"付款数据清洗完成，有效记录：{len(cleaned_rows)}")
            return len(cleaned_rows)

        except Exception as e:
            logger.error(f"清洗付款数据失败：{str(e)}")
            raise

    def log_errors(self, error_rows: List[Dict]):
        """记录错误数据到日志表"""
        try:
            for err in error_rows[:100]:  # 限制最多记录 100 条
                insert_sql = """
                INSERT INTO Dwd_error_log (SourceTable, SourceGUID, ErrorType, ErrorMsg, ErrorData, ErrorTime)
                VALUES (:source, :guid, :type, :msg, :data, :time)
                """
                with self.dwd_engine.begin() as conn:
                    conn.execute(text(insert_sql), {
                        'source': err['source'],
                        'guid': err['data'].get('RoomGUID', err['data'].get('TradeGUID', '')),
                        'type': 'data_validation',
                        'msg': err['error'],
                        'data': str(err['data'])[:1000],
                        'time': datetime.now()
                    })
        except Exception as e:
            logger.error(f"记录错误日志失败：{str(e)}")

    def run_full_cleaning(self):
        """执行全量清洗"""
        logger.info("=" * 50)
        logger.info("开始执行 DWD 层全量数据清洗")
        logger.info("=" * 50)

        results = {}
        try:
            results['Dwd_room_detail'] = self.clean_room_data()
            results['Dwd_trade_detail'] = self.clean_trade_data()
            results['Dwd_payment_detail'] = self.clean_payment_data()
            results['Dwd_contract_detail'] = self.clean_contract_data()
            results['Dwd_pay_detail'] = self.clean_pay_data()

            logger.info("=" * 50)
            logger.info("DWD 层全量清洗完成")
            logger.info(f"清洗结果：{results}")
            logger.info("=" * 50)

            return results

        except Exception as e:
            logger.error(f"DWD 层全量清洗失败：{str(e)}")
            raise
        finally:
            self.close_engines()


def main():
    """主函数"""
    ods_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': 'erp_ods',
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }

    dwd_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': 'erp_dwd',
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }

    cleaner = DWDCleaner(ods_config, dwd_config)

    if not cleaner.create_engines():
        logger.error("创建数据库连接失败，退出程序")
        return

    try:
        cleaner.run_full_cleaning()
        logger.info("DWD 层数据清洗成功完成")
    except Exception as e:
        logger.error(f"DWD 层数据清洗失败：{str(e)}")


if __name__ == '__main__':
    main()
