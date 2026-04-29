"""
示例数据生成脚本
为 ODS、DWD、DWS、ADS 各层数据表生成 10-50 条模拟数据
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockDataGenerator:
    """模拟数据生成器"""

    def __init__(self):
        # 基础数据配置
        self.projects = [
            {'guid': 'PROJ_001', 'name': '阳光城一期', 'city': '广州', 'region': '华南区'},
            {'guid': 'PROJ_002', 'name': '阳光城二期', 'city': '广州', 'region': '华南区'},
            {'guid': 'PROJ_003', 'name': '翡翠华庭', 'city': '深圳', 'region': '华南区'},
            {'guid': 'PROJ_004', 'name': '金域蓝湾', 'city': '珠海', 'region': '华南区'},
            {'guid': 'PROJ_005', 'name': '碧桂园·天玺', 'city': '杭州', 'region': '华东区'},
            {'guid': 'PROJ_006', 'name': '万科·翡翠之光', 'city': '上海', 'region': '华东区'},
            {'guid': 'PROJ_007', 'name': '保利·天悦', 'city': '北京', 'region': '华北区'},
            {'guid': 'PROJ_008', 'name': '中海·环宇城', 'city': '成都', 'region': '西南区'},
        ]

        self.buildings = [f'{i}栋' for i in range(1, 11)]
        self.rooms = [f'{floor}0{room}' for floor in range(1, 31) for room in range(1, 5)]
        self.room_types = ['三房两厅', '四房两厅', '两房一厅', '五房两厅', '单身公寓']
        self.orientations = ['南', '北', '东', '西', '东南', '东北', '西南', '西北']

        self.buyer_names = [
            '张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十',
            '郑十一', '冯十二', '陈十三', '褚十四', '卫十五', '蒋十六',
            '沈十七', '韩十八', '杨十九', '朱二十', '秦二十一', '尤二十二'
        ]

        self.id_cards = [
            f'440100{random.randint(1970, 2000)}{random.randint(100, 999)}{random.randint(1000, 9999)}'
            for _ in range(20)
        ]

        self.bank_names = ['工商银行', '建设银行', '农业银行', '中国银行', '招商银行', '交通银行', '中信银行', '光大银行']
        self.contract_types = ['商品房买卖合同', '认购书', '网签合同', '备案合同']
        self.account_codes = ['1001', '1002', '1122', '1405', '1601', '2001', '2202', '4001', '5001', '6001']

    def generate_guid(self, prefix: str = '') -> str:
        """生成 GUID"""
        if prefix:
            return f"{prefix}_{uuid.uuid4().hex[:12]}"
        return uuid.uuid4().hex

    def generate_datetime(self, start: datetime, end: datetime) -> datetime:
        """生成随机日期时间"""
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)

    def generate_ods_room(self, count: int = 30) -> List[Dict]:
        """生成 ODS_room 房间明细表数据"""
        logger.info(f"生成 ODS_room 数据 {count} 条...")
        rows = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 12, 31)

        for i in range(count):
            project = random.choice(self.projects)
            area = round(random.uniform(70, 200), 2)
            price = round(area * random.uniform(15000, 50000), 2)

            rows.append({
                'RoomGUID': self.generate_guid('ROOM'),
                'RoomNo': random.choice(self.rooms),
                'ProjectGUID': project['guid'],
                'ProjectName': project['name'],
                'BuildingNo': random.choice(self.buildings),
                'BuildingName': f"{project['name']}{random.choice(self.buildings)}",
                'UnitNo': f'{random.randint(1, 4)}单元',
                'FloorNo': random.randint(1, 30),
                'Area': area,
                'InnerArea': round(area * 0.82, 2),
                'PublicArea': round(area * 0.18, 2),
                'RoomType': random.choice(self.room_types),
                'RoomStatus': random.choice(['可售', '已售', '已签约', '已认购']),
                'Price': price,
                'UnitPrice': round(price / area, 2),
                'Orientation': random.choice(self.orientations),
                'Remark': f'模拟数据 {i+1}',
                'CreatedGUID': self.generate_guid('USER'),
                'CreatedName': random.choice(self.buyer_names),
                'CreatedTime': self.generate_datetime(start_date, end_date),
                'ModifiedGUID': self.generate_guid('USER'),
                'ModifiedName': random.choice(self.buyer_names),
                'ModifiedTime': self.generate_datetime(start_date, end_date),
                'VersionNumber': datetime.now(),
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_ods_trade(self, count: int = 30) -> List[Dict]:
        """生成 ODS_trade 销售表数据"""
        logger.info(f"生成 ODS_trade 数据 {count} 条...")
        rows = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 12, 31)

        for i in range(count):
            project = random.choice(self.projects)
            rows.append({
                'TradeGUID': self.generate_guid('TRADE'),
                'BUGUID': self.generate_guid('COMP'),
                'BuyerAllCardIds': random.choice(self.id_cards),
                'BuyerAllNames': random.choice(self.buyer_names),
                'CloseReason': random.choice(['', '', '客户放弃', '贷款失败']),
                'ContractGUID': self.generate_guid('CONT'),
                'ContractQsDate': self.generate_datetime(start_date, end_date),
                'ContractYwgsDate': self.generate_datetime(start_date, end_date),
                'IsExistDelayPay': random.choice([0, 0, 0, 1]),
                'LastGjDate': self.generate_datetime(start_date, end_date),
                'PreTradeGUID': '',
                'ProjGUID': project['guid'],
                'RGOrderGUID': self.generate_guid('SUB'),
                'RGOrderQsDate': self.generate_datetime(start_date, end_date),
                'RGOrderType': random.choice(['首次认购', '二次认购', '换房认购']),
                'RoomGUID': self.generate_guid('ROOM'),
                'RoomStatus': random.choice(['已售', '已签约', '已认购']),
                'TradeStatus': random.choice(['正常', '已关闭', '已签约']),
                'CreatedGUID': self.generate_guid('USER'),
                'CreatedName': random.choice(self.buyer_names),
                'CreatedTime': self.generate_datetime(start_date, end_date),
                'ModifiedGUID': self.generate_guid('USER'),
                'ModifiedName': random.choice(self.buyer_names),
                'ModifiedTime': self.generate_datetime(start_date, end_date),
                'VersionNumber': datetime.now(),
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_ods_payment(self, count: int = 40) -> List[Dict]:
        """生成 ODS_payment 回款明细表数据"""
        logger.info(f"生成 ODS_payment 数据 {count} 条...")
        rows = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 12, 31)

        for i in range(count):
            project = random.choice(self.projects)
            amount = round(random.uniform(50000, 5000000), 2)
            rows.append({
                'PayGUID': self.generate_guid('PAY'),
                'TradeGUID': self.generate_guid('TRADE'),
                'ContractGUID': self.generate_guid('CONT'),
                'ProjGUID': project['guid'],
                'PayAmount': amount,
                'PayDate': self.generate_datetime(start_date, end_date),
                'PayType': random.choice(['首付款', '按揭款', '公积金', '分期款', '尾款']),
                'PayWay': random.choice(['银行转账', 'POS 刷卡', '现金', '支票']),
                'BankName': random.choice(self.bank_names),
                'LoanType': random.choice(['商业贷款', '公积金贷款', '组合贷款', '全款']),
                'PayStatus': random.choice(['已确认', '待确认', '已驳回']),
                'Remark': f'回款备注 {i+1}',
                'CreatedGUID': self.generate_guid('USER'),
                'CreatedName': random.choice(self.buyer_names),
                'CreatedTime': self.generate_datetime(start_date, end_date),
                'ModifiedGUID': self.generate_guid('USER'),
                'ModifiedName': random.choice(self.buyer_names),
                'ModifiedTime': self.generate_datetime(start_date, end_date),
                'VersionNumber': datetime.now(),
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_ods_pay(self, count: int = 25) -> List[Dict]:
        """生成 ODS_pay 付款登记表数据"""
        logger.info(f"生成 ODS_pay 数据 {count} 条...")
        rows = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 12, 31)

        for i in range(count):
            project = random.choice(self.projects)
            amount = round(random.uniform(10000, 2000000), 2)
            rows.append({
                'PayRegGUID': self.generate_guid('PAYREG'),
                'ProjGUID': project['guid'],
                'ContractGUID': self.generate_guid('CONT') if random.random() > 0.2 else '',
                'PayRegAmount': amount,
                'PayRegDate': self.generate_datetime(start_date, end_date),
                'PayType': random.choice(['工程进度款', '材料款', '设计费', '营销费', '管理费']),
                'PayeeName': f'收款方{random.randint(1, 50)}公司',
                'PayeeBank': random.choice(self.bank_names),
                'PayeeAccount': f'6222{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}',
                'InvoiceNo': f'INV{random.randint(100000, 999999)}',
                'PayStatus': random.choice(['已付款', '待付款', '审批中']),
                'Remark': f'付款备注 {i+1}',
                'CreatedGUID': self.generate_guid('USER'),
                'CreatedName': random.choice(self.buyer_names),
                'CreatedTime': self.generate_datetime(start_date, end_date),
                'ModifiedGUID': self.generate_guid('USER'),
                'ModifiedName': random.choice(self.buyer_names),
                'ModifiedTime': self.generate_datetime(start_date, end_date),
                'VersionNumber': datetime.now(),
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_ods_account(self, count: int = 20) -> List[Dict]:
        """生成 ODS_account 科目表数据"""
        logger.info(f"生成 ODS_account 数据 {count} 条...")
        rows = []

        accounts = [
            ('1001', '库存现金', '资产', 1),
            ('1002', '银行存款', '资产', 1),
            ('1122', '应收账款', '资产', 1),
            ('1405', '库存商品', '资产', 1),
            ('1601', '固定资产', '资产', 1),
            ('2001', '短期借款', '负债', 1),
            ('2202', '应付账款', '负债', 1),
            ('2211', '应付职工薪酬', '负债', 1),
            ('4001', '实收资本', '权益', 1),
            ('4101', '盈余公积', '权益', 1),
            ('5001', '开发成本', '成本', 1),
            ('5002', '开发间接费', '成本', 1),
            ('6001', '主营业务收入', '损益', 1),
            ('6401', '主营业务成本', '损益', 1),
            ('6601', '销售费用', '损益', 1),
            ('6602', '管理费用', '损益', 1),
            ('6603', '财务费用', '损益', 1),
            ('6701', '税金及附加', '损益', 1),
            ('6801', '所得税费用', '损益', 1),
            ('6901', '以前年度损益调整', '损益', 1),
        ]

        for code, name, acc_type, level in accounts[:count]:
            rows.append({
                'AccountGUID': self.generate_guid('ACC'),
                'AccountCode': code,
                'AccountName': name,
                'AccountType': acc_type,
                'ParentGUID': '',
                'Level': level,
                'IsLeaf': 1,
                'ProjGUID': random.choice(self.projects)['guid'],
                'Status': 'active',
                'Remark': f'{name}科目',
                'CreatedGUID': self.generate_guid('USER'),
                'CreatedName': '财务管理员',
                'CreatedTime': datetime(2023, 1, 1),
                'ModifiedGUID': self.generate_guid('USER'),
                'ModifiedName': '财务管理员',
                'ModifiedTime': datetime.now(),
                'VersionNumber': datetime.now(),
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_ods_contract(self, count: int = 25) -> List[Dict]:
        """生成 ODS_contract 合同表数据"""
        logger.info(f"生成 ODS_contract 数据 {count} 条...")
        rows = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 12, 31)

        companies = ['建筑工程公司', '装修公司', '设计公司', '营销代理公司', '物业公司', '景观工程公司']

        for i in range(count):
            project = random.choice(self.projects)
            amount = round(random.uniform(100000, 50000000), 2)
            paid = round(amount * random.uniform(0.1, 0.9), 2)

            rows.append({
                'ContractGUID': self.generate_guid('CONT'),
                'ContractCode': f'HT{random.randint(100000, 999999)}',
                'ContractName': f"{project['name']}{random.choice(companies)}合同",
                'ContractType': random.choice(self.contract_types),
                'ProjGUID': project['guid'],
                'PartyA': f"{project['name']}房地产公司",
                'PartyB': f"{random.choice(companies)}{random.randint(1, 20)}公司",
                'SignDate': self.generate_datetime(start_date, end_date),
                'StartDate': self.generate_datetime(start_date, end_date),
                'EndDate': self.generate_datetime(start_date, end_date),
                'ContractAmount': amount,
                'PaidAmount': paid,
                'UnpaidAmount': round(amount - paid, 2),
                'AccountGUID': self.generate_guid('ACC'),
                'ContractStatus': random.choice(['履行中', '已完成', '已终止', '待签订']),
                'Remark': f'合同备注 {i+1}',
                'CreatedGUID': self.generate_guid('USER'),
                'CreatedName': random.choice(self.buyer_names),
                'CreatedTime': self.generate_datetime(start_date, end_date),
                'ModifiedGUID': self.generate_guid('USER'),
                'ModifiedName': random.choice(self.buyer_names),
                'ModifiedTime': self.generate_datetime(start_date, end_date),
                'VersionNumber': datetime.now(),
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_ods_bseg(self, count: int = 30) -> List[Dict]:
        """生成 ODS_bseg 凭证表数据"""
        logger.info(f"生成 ODS_bseg 数据 {count} 条...")
        rows = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 12, 31)

        for i in range(count):
            project = random.choice(self.projects)
            amount = round(random.uniform(1000, 1000000), 2)

            rows.append({
                'BsegGUID': self.generate_guid('BSEG'),
                'Bukrs': f'{random.randint(1000, 9999)}',
                'Belnr': f'{random.randint(1000000000, 9999999999)}',
                'Gjahr': str(random.randint(2023, 2025)),
                'Buzei': f'{random.randint(1, 999):03d}',
                'HKONT': random.choice(self.account_codes),
                'Sghsl': amount,
                'Wrbsl': round(random.uniform(1, 100), 3),
                'Meins': random.choice(['件', '个', '套', 'kg', 'm']),
                'Kstar': f'K{random.randint(100000, 999999)}',
                'Kostl': f'C{random.randint(1000, 9999)}',
                'ProjGUID': project['guid'],
                'Bldat': self.generate_datetime(start_date, end_date),
                'Budat': self.generate_datetime(start_date, end_date),
                'Shkzg': random.choice(['S', 'H']),
                'Bstat': random.choice(['1', '2', '3']),
                'Xblnr': f'REF{random.randint(100000, 999999)}',
                'Sgut1': f'分配{random.randint(1, 100)}',
                'Txt50': f'凭证摘要{i+1}',
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_ods_gl_actual(self, count: int = 30) -> List[Dict]:
        """生成 ODS_GL_Actual 总账实际业务表数据"""
        logger.info(f"生成 ODS_GL_Actual 数据 {count} 条...")
        rows = []

        for i in range(count):
            project = random.choice(self.projects)
            amount = round(random.uniform(1000, 5000000), 2)

            rows.append({
                'GlActualGUID': self.generate_guid('GL'),
                'RYear': str(random.randint(2023, 2025)),
                'Rcver': f'{random.randint(0, 9):02d}',
                'Tvers': f'{random.randint(0, 9):02d}',
                'Lednr': f'{random.randint(0, 9):02d}',
                'Rdart': random.choice(['0', '1', '2']),
                'Sltpo': random.randint(1, 16),
                'HkmtArt': random.choice(['01', '02', '03', '04']),
                'HkmtNr': f'{random.randint(1, 100):04d}',
                'Kstar': f'K{random.randint(100000, 999999)}',
                'Kostl': f'C{random.randint(1000, 9999)}',
                'ProjGUID': project['guid'],
                'Prctr': f'P{random.randint(1000, 9999)}',
                'CurrType': random.choice(['0', '1', '2']),
                'Hsl': amount,
                'Ksl': round(amount * random.uniform(0.1, 7), 2),
                'Osl': round(amount * random.uniform(0.5, 2), 2),
                'Twaer': random.choice(['CNY', 'USD', 'EUR', '']),
                'Menge': round(random.uniform(1, 1000), 3),
                'Meins': random.choice(['件', '个', '套', 'kg', 'm']),
                'ExtractTime': datetime.now()
            })
        return rows

    def generate_all_ods(self) -> Dict[str, List[Dict]]:
        """生成所有 ODS 层数据"""
        logger.info("=" * 50)
        logger.info("开始生成 ODS 层模拟数据")
        logger.info("=" * 50)

        return {
            'ODS_room': self.generate_ods_room(30),
            'ODS_trade': self.generate_ods_trade(30),
            'ODS_payment': self.generate_ods_payment(40),
            'ODS_pay': self.generate_ods_pay(25),
            'ODS_account': self.generate_ods_account(20),
            'ODS_contract': self.generate_ods_contract(25),
            'ODS_bseg': self.generate_ods_bseg(30),
            'ODS_GL_Actual': self.generate_ods_gl_actual(30)
        }


def main():
    """主函数 - 生成数据并导出 SQL"""
    generator = MockDataGenerator()
    all_data = generator.generate_all_ods()

    # 输出统计
    logger.info("=" * 50)
    logger.info("ODS 层数据生成完成")
    for table, rows in all_data.items():
        logger.info(f"  {table}: {len(rows)} 条")
    logger.info("=" * 50)

    # 可以导出为 SQL 文件
    output_file = 'database/ddl/05_mock_data.sql'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("-- ODS 层模拟数据\n")
        f.write("-- 由 generate_mock_data.py 自动生成\n\n")

        for table, rows in all_data.items():
            if rows:
                f.write(f"-- {table} ({len(rows)} 条)\n")
                cols = list(rows[0].keys())
                for row in rows:
                    values = []
                    for col in cols:
                        val = row[col]
                        if val is None:
                            values.append('NULL')
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        elif isinstance(val, datetime):
                            values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                        else:
                            val_str = str(val).replace("'", "''")
                            values.append(f"'{val_str}'")
                    f.write(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(values)});\n")
                f.write("\n")

    logger.info(f"SQL 文件已导出：{output_file}")
    return all_data


if __name__ == '__main__':
    main()
