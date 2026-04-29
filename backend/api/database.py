"""
数据库连接模块
支持 MySQL 和 SQLite（用于开发测试）
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

# 使用 SQLite 进行简单存储（生产环境可切换为 MySQL）
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    import sqlite3
    from contextlib import contextmanager

    DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "db", "erp_bi.db"))

    @contextmanager
    def get_db_connection():
        """获取数据库连接"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_db():
        """初始化数据库表"""
        import os.path

        # 确保 db 目录存在
        db_dir = os.path.dirname(DB_PATH)
        os.makedirs(db_dir, exist_ok=True)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 用户表
            cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        email TEXT,
                        real_name TEXT,
                        role_id INTEGER,
                        status INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login_at TIMESTAMP
                    )
                ''')

            # 角色表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        role_name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # 权限表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                        permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        permission_code TEXT NOT NULL UNIQUE,
                        permission_name TEXT NOT NULL,
                        resource_type TEXT,
                        parent_id INTEGER DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # 角色权限关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS role_permissions (
                        role_id INTEGER NOT NULL,
                        permission_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (role_id, permission_id)
                    )
                ''')

            # 报表配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS report_configs (
                        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_code TEXT UNIQUE,
                        report_name TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        report_category TEXT DEFAULT 'basic',
                        description TEXT,
                        sql_query TEXT,
                        config_json TEXT,
                        status TEXT DEFAULT 'draft',
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        published_at TIMESTAMP
                    )
                ''')

            # 为已有表添加新字段（如果表已存在但缺少字段）
            # 检查 report_code 字段
            cursor.execute("PRAGMA table_info(report_configs)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'report_code' not in columns:
                cursor.execute("ALTER TABLE report_configs ADD COLUMN report_code TEXT")
            if 'report_category' not in columns:
                cursor.execute("ALTER TABLE report_configs ADD COLUMN report_category TEXT DEFAULT 'basic'")

            # ETL 任务日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_task_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_name TEXT NOT NULL,
                        task_layer TEXT,
                        status TEXT NOT NULL,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        duration_seconds INTEGER,
                        message TEXT,
                        error_message TEXT
                    )
                ''')

            # ETL 调度配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_schedules (
                        schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_name TEXT NOT NULL,
                        cron_expression TEXT NOT NULL,
                        is_enabled INTEGER DEFAULT 1,
                        last_run_at TIMESTAMP,
                        next_run_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # ETL 作业定义表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_jobs (
                        job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        layer TEXT NOT NULL,
                        script_path TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # ETL 数据源表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_datasources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        type TEXT NOT NULL,
                        host TEXT,
                        port INTEGER,
                        database TEXT,
                        username TEXT,
                        password TEXT,
                        connection_string TEXT,
                        file_path TEXT,
                        api_url TEXT,
                        description TEXT,
                        config_json TEXT,
                        is_enabled INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # ETL 抽取/加载任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_transform_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        source_datasource_id INTEGER,
                        source_table TEXT NOT NULL,
                        target_datasource_id INTEGER,
                        target_table TEXT NOT NULL,
                        transform_rules_json TEXT,
                        extract_mode TEXT DEFAULT 'full',
                        extract_field TEXT,
                        batch_size INTEGER DEFAULT 1000,
                        description TEXT,
                        is_enabled INTEGER DEFAULT 1,
                        last_run_at TIMESTAMP,
                        last_status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # ETL 开发脚本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dev_scripts (
                        script_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        script_name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        script_type TEXT DEFAULT 'sql',
                        content TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # ETL 工作流表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_workflows (
                        workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        layer TEXT NOT NULL,
                        nodes TEXT,
                        connections TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # ETL 工作流执行记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_executions (
                        execution_id TEXT PRIMARY KEY,
                        workflow_id INTEGER NOT NULL,
                        status TEXT NOT NULL DEFAULT 'running',
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        duration_seconds INTEGER,
                        variables TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_workflow ON etl_executions(workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_status ON etl_executions(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_start_time ON etl_executions(start_time)')

            # 系统日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_level TEXT DEFAULT 'INFO',
                        module TEXT,
                        action TEXT,
                        user_id INTEGER,
                        username TEXT,
                        ip_address TEXT,
                        message TEXT,
                        request_data TEXT,
                        response_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # AI 问数日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_query_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT NOT NULL,
                        generated_sql TEXT,
                        keywords TEXT,
                        input_tokens INTEGER,
                        output_tokens INTEGER,
                        total_tokens INTEGER,
                        execution_time_ms INTEGER,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        match_source TEXT DEFAULT 'AI 在线生成',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            cursor.execute("PRAGMA table_info(ai_query_logs)")
            ai_query_log_columns = [row[1] for row in cursor.fetchall()]
            if 'match_source' not in ai_query_log_columns:
                cursor.execute("ALTER TABLE ai_query_logs ADD COLUMN match_source TEXT DEFAULT 'AI 在线生成'")

            # 标准 SQL 库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS standard_sql_library (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keywords TEXT NOT NULL,
                        question_template TEXT,
                        standard_sql TEXT NOT NULL,
                        explanation TEXT,
                        usage_count INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # 插入默认数据
            cursor.execute("SELECT COUNT(*) FROM roles")
            if cursor.fetchone()[0] == 0:
                # 默认角色
                roles = [
                    ('超级管理员', '系统最高权限角色'),
                    ('管理员', '系统管理员，拥有大部分管理权限'),
                    ('普通用户', '普通用户，只能查看报表'),
                    ('数据分析师', '可以进行数据分析和 AI 问数')
                ]
                cursor.executemany("INSERT INTO roles (role_name, description) VALUES (?, ?)", roles)

                # 默认权限
                permissions = [
                    ('admin', '后台管理', 'menu', 0, 1),
                    ('admin:user', '用户管理', 'menu', 0, 2),
                    ('admin:role', '角色管理', 'menu', 0, 3),
                    ('admin:report', '报表管理', 'menu', 0, 4),
                    ('admin:etl', 'ETL 管理', 'menu', 0, 5),
                    ('admin:monitor', '运维监控', 'menu', 0, 6),
                    ('admin:user:list', '查看用户列表', 'api', 2, 1),
                    ('admin:user:create', '创建用户', 'button', 2, 2),
                    ('admin:user:edit', '编辑用户', 'button', 2, 3),
                    ('admin:user:delete', '删除用户', 'button', 2, 4),
                    ('admin:role:list', '查看角色列表', 'api', 3, 1),
                    ('admin:role:create', '创建角色', 'button', 3, 2),
                    ('admin:role:edit', '编辑角色', 'button', 3, 3),
                    ('admin:report:list', '查看报表列表', 'api', 4, 1),
                    ('admin:report:publish', '发布/取消发布', 'button', 4, 5),
                    ('admin:etl:list', '查看任务列表', 'api', 5, 1),
                    ('admin:etl:run', '运行任务', 'button', 5, 2),
                    ('admin:etl:log', '查看日志', 'button', 5, 3),
                    ('admin:monitor:system', '系统信息', 'api', 6, 1),
                    ('admin:monitor:service', '服务状态', 'api', 6, 2),
                ]
                cursor.executemany(
                    "INSERT INTO permissions (permission_code, permission_name, resource_type, parent_id, sort_order) VALUES (?, ?, ?, ?, ?)",
                    permissions
                )

                # 给超级管理员分配所有权限
                cursor.execute("SELECT permission_id FROM permissions")
                for perm in cursor.fetchall():
                    cursor.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (1, ?)", (perm[0],))

            # 默认 ETL 作业定义
            cursor.execute("SELECT COUNT(*) FROM etl_jobs")
            if cursor.fetchone()[0] == 0:
                jobs = [
                    ('ODS 数据抽取', '从业务库抽取原始数据到 ODS 层', 'ODS', 'etl/extractors/ods_extractor.py'),
                    ('DWD 数据清洗', '清洗和标准化 ODS 层数据', 'DWD', 'etl/transformers/dwd_cleaner.py'),
                    ('DWS 数据聚合', '轻度聚合生成汇总数据', 'DWS', 'etl/transformers/dws_aggregator.py'),
                    ('ADS 报表生成', '生成面向应用的报表指标', 'ADS', 'etl/loaders/ads_loader.py'),
                ]
                cursor.executemany(
                    "INSERT INTO etl_jobs (job_name, description, layer, script_path, status) VALUES (?, ?, ?, ?, 'active')",
                    jobs
                )

            # 默认数据源
            cursor.execute("SELECT COUNT(*) FROM etl_datasources")
            if cursor.fetchone()[0] == 0:
                datasources = [
                    ('业务库', 'mysql', 'localhost', 3306, 'business_db', 'root', '', None, None, None, '业务系统源库', '{}', 1),
                    ('数仓库', 'mysql', 'localhost', 3306, 'erp_bi', 'root', '', None, None, None, 'ETL 目标数仓', '{}', 1),
                    ('CSV 示例', 'csv', None, None, None, None, None, None, './data/sample.csv', None, '本地 CSV 示例文件', '{}', 1),
                ]
                cursor.executemany(
                    """
                    INSERT INTO etl_datasources (
                        name, type, host, port, database, username, password,
                        connection_string, file_path, api_url, description, config_json, is_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    datasources
                )

            # 默认抽取/加载任务
            cursor.execute("SELECT COUNT(*) FROM etl_transform_tasks")
            if cursor.fetchone()[0] == 0:
                cursor.execute("SELECT id FROM etl_datasources WHERE name = '业务库'")
                source_id = cursor.fetchone()[0]
                cursor.execute("SELECT id FROM etl_datasources WHERE name = '数仓库'")
                target_id = cursor.fetchone()[0]
                tasks = [
                    (
                        '房源 ODS 抽取',
                        source_id,
                        're_units',
                        target_id,
                        'ods_room',
                        '[]',
                        'incremental',
                        'updated_at',
                        1000,
                        '从业务库抽取房源明细到 ODS 层',
                        1,
                    ),
                    (
                        '销售 ODS 加载',
                        source_id,
                        're_contracts',
                        target_id,
                        'ods_trade',
                        '[]',
                        'incremental',
                        'updated_at',
                        1000,
                        '从业务库抽取销售合同到 ODS 层',
                        1,
                    ),
                ]
                cursor.executemany(
                    """
                    INSERT INTO etl_transform_tasks (
                        name, source_datasource_id, source_table, target_datasource_id, target_table,
                        transform_rules_json, extract_mode, extract_field, batch_size, description, is_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    tasks
                )

            # 默认开发脚本
            cursor.execute("SELECT COUNT(*) FROM dev_scripts")
            if cursor.fetchone()[0] == 0:
                scripts = [
                    (
                        'ODS 抽取模板',
                        '简单 SQL 模板，适合做基础抽取预览',
                        'sql',
                        'SELECT * FROM re_units LIMIT 20',
                        'draft',
                    ),
                    (
                        'ODS 加载模板',
                        '基础加载脚本占位内容',
                        'sql',
                        'INSERT INTO ods_room (...) SELECT ...',
                        'draft',
                    ),
                ]
                cursor.executemany(
                    """
                    INSERT INTO dev_scripts (script_name, description, script_type, content, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    scripts
                )

            # 默认管理员用户
            from api.auth import get_password_hash
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email, real_name, role_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                    ('admin', get_password_hash('admin123'), 'admin@example.com', '系统管理员', 1, 1)
                )

            # 初始化报表数据（portal 报表与 admin 报表统一管理）
            cursor.execute("SELECT COUNT(*) FROM report_configs")
            if cursor.fetchone()[0] == 0:
                portal_reports = [
                    ('sales-overview', '销售概览', 'kpi', 'basic', '核心销售指标概览，包括销售额、订单数、销售量等关键指标', None, 'published'),
                    ('sales-trend', '销售趋势', 'chart', 'basic', '销售趋势分析，展示近 12 个月的销售变化情况', None, 'published'),
                    ('product-ranking', '产品排行', 'table', 'basic', '产品销量排行榜，Top 50 产品销售额排名', None, 'published'),
                    ('category-analysis', '品类分析', 'chart', 'basic', '品类销售分析，各品类销售占比和趋势', None, 'published'),
                    ('customer-analysis', '客户分析', 'table', 'analysis', '客户分析报表，客户类型、行业分布及价值分析', None, 'published'),
                    ('profit-analysis', '利润分析', 'chart', 'analysis', '利润分析报表，毛利率、净利率等利润指标', None, 'published'),
                    ('inventory-report', '库存报表', 'table', 'analysis', '库存报表，库存周转率、滞销商品分析', None, 'published'),
                    ('forecast-report', '预测报表', 'chart', 'advanced', '销售预测报表，基于历史数据的智能预测', None, 'published'),
                ]
                cursor.executemany(
                    """
                    INSERT INTO report_configs (report_code, report_name, report_type, report_category, description, sql_query, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    portal_reports
                )

            # 为已有表添加 match_source 列（区分标准库命中 vs AI 在线生成）
            try:
                cursor.execute("ALTER TABLE ai_query_logs ADD COLUMN match_source TEXT")
            except Exception:
                pass  # 列已存在
else:
    # MySQL 连接（生产环境）
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    DB_URL = os.getenv("DATABASE_URL", "mysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi")
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)

    def get_db_connection():
        """获取数据库会话"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def init_db():
        """初始化数据库"""
        pass  # MySQL 使用 init.sql 脚本初始化


# 初始化数据库
init_db()


# ===========================================
# 通用数据库操作辅助函数
# ===========================================

def dict_from_row(row):
    """将数据库行转换为字典"""
    if hasattr(row, 'keys'):
        return dict(row)
    return row


def execute_query(sql: str, params: tuple = None) -> List[Dict[str, Any]]:
    """执行查询并返回结果列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


def execute_update(sql: str, params: tuple = None) -> int:
    """执行更新并返回影响的行数"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.rowcount


def get_current_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
