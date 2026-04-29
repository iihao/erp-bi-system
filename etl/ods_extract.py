"""
ODS 层数据抽取脚本
从 MySQL 业务数据库抽取原始数据到 ODS（操作数据存储）层
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging
import os
from typing import Optional, Dict, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ods_extract.log', encoding='utf-8'),
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
                - host: MySQL 主机地址
                - port: MySQL 端口
                - database: 数据库名
                - user: 用户名
                - password: 密码
            ods_config: ODS 数据库配置（同上）
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
            self.source_engine = create_engine(
                source_url,
                pool_size=10,
                pool_recycle=3600,
                echo=False
            )

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

    def extract_table(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        incremental_field: Optional[str] = None,
        last_extract_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        抽取单表数据

        Args:
            table_name: 表名
            columns: 需要抽取的列，None 表示全部
            where_clause: 额外的 WHERE 条件
            incremental_field: 增量抽取字段（如 update_time）
            last_extract_time: 上次抽取时间

        Returns:
            抽取的数据 DataFrame
        """
        try:
            # 构建 SELECT 语句
            if columns:
                cols_str = ', '.join([f"`{col}`" for col in columns])
            else:
                cols_str = '*'

            query = f"SELECT {cols_str} FROM `{table_name}`"

            conditions = []
            params = {}

            # 增量抽取条件
            if incremental_field and last_extract_time:
                conditions.append(f"`{incremental_field}` > :last_time")
                params['last_time'] = last_extract_time

            # 额外条件
            if where_clause:
                conditions.append(where_clause)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            logger.info(f"执行抽取 SQL: {query}, 参数：{params}")

            # 执行查询
            with self.source_engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)

            # 添加抽取元数据
            df['etl_extract_time'] = datetime.now()
            df['etl_source_table'] = table_name

            logger.info(f"从表 {table_name} 抽取 {len(df)} 条记录")
            return df

        except SQLAlchemyError as e:
            logger.error(f"抽取表 {table_name} 失败：{str(e)}")
            raise

    def extract_tables(
        self,
        table_configs: List[Dict],
        extract_time: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        批量抽取多个表

        Args:
            table_configs: 表配置列表，每个配置包含：
                - table_name: 表名
                - columns: 需要的列（可选）
                - where_clause: 过滤条件（可选）
                - incremental_field: 增量字段（可选）
            extract_time: 抽取时间点，用于记录元数据

        Returns:
            表名到 DataFrame 的映射
        """
        results = {}
        extract_time = extract_time or datetime.now()

        for config in table_configs:
            table_name = config['table_name']
            logger.info(f"开始抽取表：{table_name}")

            try:
                df = self.extract_table(
                    table_name=table_name,
                    columns=config.get('columns'),
                    where_clause=config.get('where_clause'),
                    incremental_field=config.get('incremental_field'),
                    last_extract_time=config.get('last_extract_time')
                )
                results[table_name] = df

            except Exception as e:
                logger.error(f"表 {table_name} 抽取失败：{str(e)}")
                # 根据需求决定是否继续
                continue

        return results

    def load_to_ods(
        self,
        df: pd.DataFrame,
        ods_table: str,
        if_exists: str = 'append',
        index: bool = False
    ) -> bool:
        """
        将数据加载到 ODS 层

        Args:
            df: 要加载的 DataFrame
            ods_table: ODS 层表名
            if_exists: 表已存在时的处理方式 ('append', 'replace', 'fail')
            index: 是否写入索引

        Returns:
            是否成功
        """
        try:
            # 确保表名加上 ods_ 前缀
            if not ods_table.startswith('ods_'):
                ods_table = f'ods_{ods_table}'

            logger.info(f"将 {len(df)} 条记录写入 ODS 表 {ods_table}")

            df.to_sql(
                name=ods_table,
                con=self.ods_engine,
                if_exists=if_exists,
                index=index,
                chunksize=1000,
                method='multi'
            )

            logger.info(f"成功写入 ODS 表 {ods_table}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"写入 ODS 表 {ods_table} 失败：{str(e)}")
            return False

    def sync_tables(
        self,
        table_configs: List[Dict],
        extract_time: Optional[datetime] = None
    ) -> Dict[str, bool]:
        """
        同步多个表到 ODS 层

        Args:
            table_configs: 表配置列表
            extract_time: 抽取时间

        Returns:
            表名到同步状态的映射
        """
        results = {}

        # 抽取数据
        dataframes = self.extract_tables(table_configs, extract_time)

        # 加载到 ODS
        for table_name, df in dataframes.items():
            success = self.load_to_ods(df, table_name, if_exists='append')
            results[table_name] = success

        return results


def run_ods_extract():
    """主函数：执行 ODS 数据抽取"""

    # 从环境变量读取配置（实际使用时建议从配置文件读取）
    source_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'database': os.getenv('MYSQL_DATABASE', 'erp_source'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', '')
    }

    ods_config = {
        'host': os.getenv('ODS_HOST', 'localhost'),
        'port': int(os.getenv('ODS_PORT', '3306')),
        'database': os.getenv('ODS_DATABASE', 'erp_ods'),
        'user': os.getenv('ODS_USER', 'root'),
        'password': os.getenv('ODS_PASSWORD', '')
    }

    # 定义要抽取的表配置
    table_configs = [
        {
            'table_name': 'users',
            'columns': ['id', 'username', 'email', 'phone', 'status', 'created_at', 'updated_at'],
            'incremental_field': 'updated_at',
            'last_extract_time': datetime(2026, 1, 1)  # 示例：从指定时间开始增量
        },
        {
            'table_name': 'products',
            'columns': ['id', 'name', 'category_id', 'price', 'stock', 'status', 'created_at', 'updated_at'],
            'incremental_field': 'updated_at',
            'last_extract_time': datetime(2026, 1, 1)
        },
        {
            'table_name': 'orders',
            'columns': ['id', 'order_no', 'user_id', 'total_amount', 'status', 'created_at', 'updated_at'],
            'incremental_field': 'updated_at',
            'last_extract_time': datetime(2026, 1, 1)
        },
        {
            'table_name': 'order_items',
            'columns': ['id', 'order_id', 'product_id', 'quantity', 'price', 'created_at'],
            'incremental_field': 'created_at',
            'last_extract_time': datetime(2026, 1, 1)
        },
        {
            'table_name': 'categories',
            'columns': ['id', 'name', 'parent_id', 'level', 'created_at']
        }
    ]

    # 创建抽取器
    extractor = ODSExtractor(source_config, ods_config)

    try:
        # 创建连接
        if not extractor.create_engines():
            logger.error("无法创建数据库连接，退出")
            return

        # 执行同步
        extract_time = datetime.now()
        logger.info(f"开始 ODS 数据抽取，时间：{extract_time}")

        results = extractor.sync_tables(table_configs, extract_time)

        # 输出结果
        logger.info("=" * 50)
        logger.info("ODS 抽取完成")
        for table_name, success in results.items():
            status = "成功" if success else "失败"
            logger.info(f"  {table_name}: {status}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"ODS 抽取过程发生异常：{str(e)}")
        raise

    finally:
        extractor.close_engines()


if __name__ == '__main__':
    run_ods_extract()
