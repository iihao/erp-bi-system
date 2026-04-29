#!/usr/bin/env python3
"""
初始化数据源配置脚本
将当前数据库和示例数据源添加到系统
"""
import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'db', 'erp_bi.db')

def add_datasources():
    """添加示例数据源"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datasources'")
    if not cursor.fetchone():
        print("❌ datasources 表不存在")
        return
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) as count FROM datasources")
    count = cursor.fetchone()['count']
    if count > 0:
        print(f"⚠️  数据源表已有 {count} 条记录，跳过初始化")
        conn.close()
        return
    
    # 添加当前 SQLite 数据库作为数据源
    datasources = [
        # 当前系统数据库（SQLite）
        {
            'name': 'AI数据融合平台数据库',
            'department': '技术部',
            'system_name': 'AI数据融合平台',
            'category': 'system',
            'db_type': 'sqlite',
            'driver': 'sqlite3',
            'host': 'localhost',
            'port': 0,
            'database_name': './db/erp_bi.db',
            'username': '',
            'password': '',
            'collect_metadata': 1,
            'status_check': 1,
            'status': 'active',
            'description': '当前 AI数据融合平台使用的 SQLite 数据库'
        },
        # 示例 MySQL 数据源
        {
            'name': '主业务数据库',
            'department': '技术部',
            'system_name': '业务系统',
            'category': 'business',
            'db_type': 'mysql',
            'driver': 'mysql.connector',
            'host': 'localhost',
            'port': 3306,
            'database_name': 'business_db',
            'username': 'root',
            'password': 'password',
            'collect_metadata': 1,
            'status_check': 1,
            'status': 'inactive',
            'description': '公司主营业务数据库（示例配置，需修改为实际连接信息）'
        },
        # 示例数据仓库
        {
            'name': '数据仓库',
            'department': '数据部',
            'system_name': 'DataWarehouse',
            'category': 'warehouse',
            'db_type': 'mysql',
            'driver': 'mysql.connector',
            'host': 'localhost',
            'port': 3306,
            'database_name': 'data_warehouse',
            'username': 'root',
            'password': 'password',
            'collect_metadata': 1,
            'status_check': 1,
            'status': 'inactive',
            'description': '企业数据仓库（示例配置，需修改为实际连接信息）'
        }
    ]
    
    # 插入数据源
    for ds in datasources:
        cursor.execute("""
            INSERT INTO datasources 
            (name, department, system_name, category, db_type, driver, host, port, 
             database_name, username, password, collect_metadata, status_check, status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ds['name'], ds['department'], ds['system_name'], ds['category'], ds['db_type'],
            ds['driver'], ds['host'], ds['port'], ds['database_name'], ds['username'],
            ds['password'], ds['collect_metadata'], ds['status_check'], ds['status'],
            ds['description']
        ))
        print(f"✅ 添加数据源：{ds['name']}")
    
    conn.commit()
    
    # 验证结果
    cursor.execute("SELECT id, name, db_type, status FROM datasources")
    rows = cursor.fetchall()
    print(f"\n📊 当前数据源列表（共 {len(rows)} 条）：")
    for row in rows:
        status_icon = "✅" if row['status'] == 'active' else "⏸️"
        print(f"  {status_icon} [{row['id']}] {row['name']} ({row['db_type']})")
    
    conn.close()
    print("\n✅ 数据源初始化完成")

if __name__ == '__main__':
    add_datasources()
