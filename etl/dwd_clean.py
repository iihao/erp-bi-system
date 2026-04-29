"""
DWD 层数据清洗脚本
对 ODS 层数据进行清洗、标准化和转换，加载到 DWD（明细数据层）
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging
import os
import re
from typing import Optional, Dict, List, Any, Callable

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dwd_clean.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗工具类"""

    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        去除重复数据

        Args:
            df: 输入 DataFrame
            subset: 用于判断重复的列，None 表示所有列

        Returns:
            去重后的 DataFrame
        """
        before_count = len(df)
        df = df.drop_duplicates(subset=subset, keep='last')
        after_count = len(df)
        logger.info(f"去重：{before_count} -> {after_count}, 移除 {before_count - after_count} 条")
        return df

    @staticmethod
    def handle_null_values(
        df: pd.DataFrame,
        column_strategies: Dict[str, str]
    ) -> pd.DataFrame:
        """
        处理空值

        Args:
            df: 输入 DataFrame
            column_strategies: 列名到处理策略的映射
                - 'drop': 删除该列有空值的行
                - 'fill_0': 填充为 0
                - 'fill_empty': 填充为空字符串
                - 'fill_mean': 填充为平均值
                - 'fill_forward': 向前填充
                - 'fill_backward': 向后填充
                - 'drop_column': 删除该列

        Returns:
            处理后的 DataFrame
        """
        for column, strategy in column_strategies.items():
            if column not in df.columns:
                continue

            if strategy == 'drop':
                df = df.dropna(subset=[column])
            elif strategy == 'fill_0':
                df[column] = df[column].fillna(0)
            elif strategy == 'fill_empty':
                df[column] = df[column].fillna('')
            elif strategy == 'fill_mean':
                df[column] = df[column].fillna(df[column].mean())
            elif strategy == 'fill_forward':
                df[column] = df[column].ffill()
            elif strategy == 'fill_backward':
                df[column] = df[column].bfill()
            elif strategy == 'drop_column':
                df = df.drop(columns=[column])

            null_count = df[column].isnull().sum()
            logger.info(f"列 {column} 空值处理 ({strategy}), 剩余空值：{null_count}")

        return df

    @staticmethod
    def standardize_datetime(
        df: pd.DataFrame,
        columns: List[str],
        format: str = '%Y-%m-%d %H:%M:%S'
    ) -> pd.DataFrame:
        """
        标准化日期时间格式

        Args:
            df: 输入 DataFrame
            columns: 需要标准化的列
            format: 目标格式

        Returns:
            处理后的 DataFrame
        """
        for col in columns:
            if col not in df.columns:
                continue
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime(format)

        logger.info(f"日期时间标准化完成：{columns}")
        return df

    @staticmethod
    def standardize_phone(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        标准化手机号码格式（中国大陆）

        Args:
            df: 输入 DataFrame
            column: 手机号列名

        Returns:
            处理后的 DataFrame
        """
        def clean_phone(phone: Any) -> str:
            if pd.isna(phone):
                return ''
            phone_str = str(phone).strip()
            # 移除所有非数字字符
            phone_str = re.sub(r'\D', '', phone_str)
            # 处理 +86 或 86 前缀
            if phone_str.startswith('86') and len(phone_str) == 13:
                phone_str = phone_str[2:]
            # 验证是否为有效的手机号
            if len(phone_str) == 11 and phone_str.startswith('1'):
                return phone_str
            return ''

        df[column] = df[column].apply(clean_phone)
        logger.info(f"手机号列 {column} 标准化完成")
        return df

    @staticmethod
    def standardize_email(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        标准化邮箱格式

        Args:
            df: 输入 DataFrame
            column: 邮箱列名

        Returns:
            处理后的 DataFrame
        """
        def clean_email(email: Any) -> str:
            if pd.isna(email):
                return ''
            return str(email).strip().lower()

        df[column] = df[column].apply(clean_email)
        logger.info(f"邮箱列 {column} 标准化完成")
        return df

    @staticmethod
    def map_values(
        df: pd.DataFrame,
        column: str,
        mapping: Dict[Any, Any],
        default_value: Any = None
    ) -> pd.DataFrame:
        """
        映射列值

        Args:
            df: 输入 DataFrame
            column: 要映射的列
            mapping: 映射字典
            default_value: 默认值

        Returns:
            处理后的 DataFrame
        """
        df[column] = df[column].map(mapping).fillna(default_value)
        logger.info(f"列 {column} 值映射完成")
        return df

    @staticmethod
    def convert_to_numeric(
        df: pd.DataFrame,
        columns: List[str],
        fill_value: float = 0
    ) -> pd.DataFrame:
        """
        转换为数值类型

        Args:
            df: 输入 DataFrame
            columns: 要转换的列
            fill_value: 转换失败时的填充值

        Returns:
            处理后的 DataFrame
        """
        for col in columns:
            if col not in df.columns:
                continue
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(fill_value)

        logger.info(f"数值转换完成：{columns}")
        return df

    @staticmethod
    def encode_status(
        df: pd.DataFrame,
        column: str,
        status_mapping: Dict[str, int]
    ) -> pd.DataFrame:
        """
        编码状态字段为数字

        Args:
            df: 输入 DataFrame
            column: 状态列
            status_mapping: 状态映射，如 {'active': 1, 'inactive': 0}

        Returns:
            处理后的 DataFrame
        """
        df[column + '_code'] = df[column].map(status_mapping).fillna(-1)
        logger.info(f"状态编码完成：{column}")
        return df


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
        self.cleaner = DataCleaner()

    def create_engines(self):
        """创建数据库连接引擎"""
        try:
            # ODS 数据库连接
            ods_url = (
                f"mysql+pymysql://{self.ods_config['user']}:{self.ods_config['password']}@"
                f"{self.ods_config['host']}:{self.ods_config['port']}/{self.ods_config['database']}?"
                f"charset=utf8mb4"
            )
            self.ods_engine = create_engine(
                ods_url,
                pool_size=10,
                pool_recycle=3600,
                echo=False
            )

            # DWD 数据库连接
            dwd_url = (
                f"mysql+pymysql://{self.dwd_config['user']}:{self.dwd_config['password']}@"
                f"{self.dwd_config['host']}:{self.dwd_config['port']}/{self.dwd_config['database']}?"
                f"charset=utf8mb4"
            )
            self.dwd_engine = create_engine(
                dwd_url,
                pool_size=10,
                pool_recycle=3600,
                echo=False
            )

            logger.info("DWD 数据库连接引擎创建成功")
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

    def extract_from_ods(self, table_name: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        从 ODS 层抽取数据

        Args:
            table_name: 表名（带或不带 ods_ 前缀）
            columns: 需要的列

        Returns:
            抽取的 DataFrame
        """
        try:
            # 确保表名有 ods_ 前缀
            if not table_name.startswith('ods_'):
                table_name = f'ods_{table_name}'

            if columns:
                cols_str = ', '.join([f"`{col}`" for col in columns])
            else:
                cols_str = '*'

            query = f"SELECT {cols_str} FROM `{table_name}` ORDER BY id"

            logger.info(f"从 ODS 抽取：{query}")

            with self.ods_engine.connect() as conn:
                df = pd.read_sql(text(query), conn)

            logger.info(f"从 ODS 表 {table_name} 抽取 {len(df)} 条记录")
            return df

        except SQLAlchemyError as e:
            logger.error(f"从 ODS 抽取 {table_name} 失败：{str(e)}")
            raise

    def clean_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗用户数据

        Args:
            df: 原始用户数据

        Returns:
            清洗后的用户数据
        """
        logger.info("开始清洗用户数据")
        initial_count = len(df)

        # 1. 去除重复（按 username）
        df = self.cleaner.remove_duplicates(df, subset=['username'])

        # 2. 处理空值
        df = self.cleaner.handle_null_values(df, {
            'username': 'drop',  # 用户名不能为空
            'email': 'fill_empty',
            'phone': 'fill_empty',
            'status': 'fill_0'
        })

        # 3. 标准化邮箱
        if 'email' in df.columns:
            df = self.cleaner.standardize_email(df, 'email')

        # 4. 标准化手机号
        if 'phone' in df.columns:
            df = self.cleaner.standardize_phone(df, 'phone')

        # 5. 标准化日期
        date_columns = [col for col in ['created_at', 'updated_at'] if col in df.columns]
        if date_columns:
            df = self.cleaner.standardize_datetime(df, date_columns)

        # 6. 状态编码
        if 'status' in df.columns:
            status_mapping = {'active': 1, 'inactive': 0, 'deleted': -1}
            df = self.cleaner.encode_status(df, 'status', status_mapping)

        # 7. 添加清洗元数据
        df['etl_clean_time'] = datetime.now()
        df['etl_clean_flag'] = 1

        logger.info(f"用户数据清洗完成：{initial_count} -> {len(df)} 条")
        return df

    def clean_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗商品数据

        Args:
            df: 原始商品数据

        Returns:
            清洗后的商品数据
        """
        logger.info("开始清洗商品数据")
        initial_count = len(df)

        # 1. 去除重复（按 id）
        df = self.cleaner.remove_duplicates(df, subset=['id'])

        # 2. 处理空值
        df = self.cleaner.handle_null_values(df, {
            'name': 'drop',  # 商品名不能为空
            'price': 'fill_0',
            'stock': 'fill_0',
            'category_id': 'fill_0'
        })

        # 3. 数值转换
        df = self.cleaner.convert_to_numeric(df, ['price', 'stock', 'category_id'])

        # 4. 确保价格非负
        df['price'] = df['price'].apply(lambda x: max(0, x))
        df['stock'] = df['stock'].apply(lambda x: max(0, x))

        # 5. 标准化日期
        date_columns = [col for col in ['created_at', 'updated_at'] if col in df.columns]
        if date_columns:
            df = self.cleaner.standardize_datetime(df, date_columns)

        # 6. 添加清洗元数据
        df['etl_clean_time'] = datetime.now()
        df['etl_clean_flag'] = 1

        logger.info(f"商品数据清洗完成：{initial_count} -> {len(df)} 条")
        return df

    def clean_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗订单数据

        Args:
            df: 原始订单数据

        Returns:
            清洗后的订单数据
        """
        logger.info("开始清洗订单数据")
        initial_count = len(df)

        # 1. 去除重复（按 order_no）
        df = self.cleaner.remove_duplicates(df, subset=['order_no'])

        # 2. 处理空值
        df = self.cleaner.handle_null_values(df, {
            'order_no': 'drop',  # 订单号不能为空
            'user_id': 'drop',  # 用户 ID 不能为空
            'total_amount': 'fill_0',
            'status': 'fill_0'
        })

        # 3. 数值转换
        df = self.cleaner.convert_to_numeric(df, ['user_id', 'total_amount'])

        # 4. 确保金额非负
        df['total_amount'] = df['total_amount'].apply(lambda x: max(0, x))

        # 5. 标准化日期
        date_columns = [col for col in ['created_at', 'updated_at'] if col in df.columns]
        if date_columns:
            df = self.cleaner.standardize_datetime(df, date_columns)

        # 6. 订单状态编码
        if 'status' in df.columns:
            status_mapping = {
                'pending': 0,
                'paid': 1,
                'shipped': 2,
                'completed': 3,
                'cancelled': -1,
                'refunded': -2
            }
            df = self.cleaner.encode_status(df, 'status', status_mapping)

        # 7. 添加清洗元数据
        df['etl_clean_time'] = datetime.now()
        df['etl_clean_flag'] = 1

        logger.info(f"订单数据清洗完成：{initial_count} -> {len(df)} 条")
        return df

    def clean_order_items(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗订单明细数据

        Args:
            df: 原始订单明细数据

        Returns:
            清洗后的订单明细数据
        """
        logger.info("开始清洗订单明细数据")
        initial_count = len(df)

        # 1. 去除重复（按 id）
        df = self.cleaner.remove_duplicates(df, subset=['id'])

        # 2. 处理空值
        df = self.cleaner.handle_null_values(df, {
            'order_id': 'drop',
            'product_id': 'drop',
            'quantity': 'fill_0',
            'price': 'fill_0'
        })

        # 3. 数值转换
        df = self.cleaner.convert_to_numeric(df, ['order_id', 'product_id', 'quantity', 'price'])

        # 4. 确保数量和价格非负
        df['quantity'] = df['quantity'].apply(lambda x: max(0, x))
        df['price'] = df['price'].apply(lambda x: max(0, x))

        # 5. 计算小计
        df['subtotal'] = df['quantity'] * df['price']

        # 6. 标准化日期
        if 'created_at' in df.columns:
            df = self.cleaner.standardize_datetime(df, ['created_at'])

        # 7. 添加清洗元数据
        df['etl_clean_time'] = datetime.now()
        df['etl_clean_flag'] = 1

        logger.info(f"订单明细数据清洗完成：{initial_count} -> {len(df)} 条")
        return df

    def load_to_dwd(
        self,
        df: pd.DataFrame,
        dwd_table: str,
        if_exists: str = 'append'
    ) -> bool:
        """
        将清洗后的数据加载到 DWD 层

        Args:
            df: 清洗后的 DataFrame
            dwd_table: DWD 层表名
            if_exists: 表已存在时的处理方式

        Returns:
            是否成功
        """
        try:
            # 确保表名加上 dwd_ 前缀
            if not dwd_table.startswith('dwd_'):
                dwd_table = f'dwd_{dwd_table}'

            logger.info(f"将 {len(df)} 条清洗后的记录写入 DWD 表 {dwd_table}")

            df.to_sql(
                name=dwd_table,
                con=self.dwd_engine,
                if_exists=if_exists,
                index=False,
                chunksize=1000,
                method='multi'
            )

            logger.info(f"成功写入 DWD 表 {dwd_table}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"写入 DWD 表 {dwd_table} 失败：{str(e)}")
            return False

    def process_table(
        self,
        source_table: str,
        target_table: str,
        clean_func: Callable[[pd.DataFrame], pd.DataFrame]
    ) -> bool:
        """
        处理单个表的完整流程

        Args:
            source_table: 源表名
            target_table: 目标表名
            clean_func: 清洗函数

        Returns:
            是否成功
        """
        try:
            # 1. 从 ODS 抽取
            df = self.extract_from_ods(source_table)

            if df.empty:
                logger.warning(f"表 {source_table} 为空，跳过处理")
                return False

            # 2. 清洗数据
            df_cleaned = clean_func(df)

            # 3. 加载到 DWD
            success = self.load_to_dwd(df_cleaned, target_table, if_exists='append')

            return success

        except Exception as e:
            logger.error(f"处理表 {source_table} -> {target_table} 失败：{str(e)}")
            return False


def run_dwd_clean():
    """主函数：执行 DWD 数据清洗"""

    # ODS 数据库配置
    ods_config = {
        'host': os.getenv('ODS_HOST', 'localhost'),
        'port': int(os.getenv('ODS_PORT', '3306')),
        'database': os.getenv('ODS_DATABASE', 'erp_ods'),
        'user': os.getenv('ODS_USER', 'root'),
        'password': os.getenv('ODS_PASSWORD', '')
    }

    # DWD 数据库配置
    dwd_config = {
        'host': os.getenv('DWD_HOST', 'localhost'),
        'port': int(os.getenv('DWD_PORT', '3306')),
        'database': os.getenv('DWD_DATABASE', 'erp_dwd'),
        'user': os.getenv('DWD_USER', 'root'),
        'password': os.getenv('DWD_PASSWORD', '')
    }

    # 表处理配置
    table_configs = [
        {
            'source': 'users',
            'target': 'users',
            'clean_func': 'clean_users'
        },
        {
            'source': 'products',
            'target': 'products',
            'clean_func': 'clean_products'
        },
        {
            'source': 'orders',
            'target': 'orders',
            'clean_func': 'clean_orders'
        },
        {
            'source': 'order_items',
            'target': 'order_items',
            'clean_func': 'clean_order_items'
        }
    ]

    # 创建清洗器
    cleaner = DWDCleaner(ods_config, dwd_config)

    try:
        # 创建连接
        if not cleaner.create_engines():
            logger.error("无法创建数据库连接，退出")
            return

        # 执行清洗
        logger.info("=" * 50)
        logger.info("开始 DWD 数据清洗")
        logger.info("=" * 50)

        results = {}
        for config in table_configs:
            source = config['source']
            target = config['target']
            clean_func_name = config['clean_func']

            logger.info(f"\n处理：{source} -> {target}")

            # 获取清洗函数
            clean_func = getattr(cleaner, clean_func_name)

            success = cleaner.process_table(source, target, clean_func)
            results[f"{source}->{target}"] = success

        # 输出结果
        logger.info("\n" + "=" * 50)
        logger.info("DWD 清洗完成")
        for table_path, success in results.items():
            status = "成功" if success else "失败/跳过"
            logger.info(f"  {table_path}: {status}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"DWD 清洗过程发生异常：{str(e)}")
        raise

    finally:
        cleaner.close_engines()


if __name__ == '__main__':
    run_dwd_clean()
