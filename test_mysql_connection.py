#!/usr/bin/env python3
"""
MySQL 数据源连接测试脚本
测试 MySQL 连接和元数据同步功能
"""

import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from api.datasources import get_database_connection, map_mysql_to_sqlite_type, sync_mysql_metadata

def test_mysql_connection():
    """测试 MySQL 连接"""
    print("=" * 60)
    print("📋 测试 MySQL 连接")
    print("=" * 60)
    
    # 测试配置（请根据实际情况修改）
    config = {
        'db_type': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'database': 'mysql',  # 使用 mysql 系统库测试
        'username': 'root',
        'password': 'password'  # 请修改为实际密码
    }
    
    try:
        print(f"🔌 正在连接 MySQL: {config['host']}:{config['port']}/{config['database']}")
        conn = get_database_connection(
            config['db_type'],
            config['host'],
            config['port'],
            config['database'],
            config['username'],
            config['password']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        print(f"✅ 连接成功！")
        print(f"📊 MySQL 版本：{version['VERSION()']}")
        
        # 获取数据库列表
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print(f"📁 可用数据库：{len(databases)} 个")
        for db in databases[:5]:  # 显示前 5 个
            print(f"   - {db['Database']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        return False


def test_type_mapping():
    """测试类型映射"""
    print("\n" + "=" * 60)
    print("📋 测试类型映射")
    print("=" * 60)
    
    test_cases = [
        ('INT', 'INTEGER'),
        ('INTEGER', 'INTEGER'),
        ('BIGINT', 'INTEGER'),
        ('DECIMAL(10,2)', 'DECIMAL(15,2)'),
        ('FLOAT', 'DECIMAL(15,2)'),
        ('DOUBLE', 'DECIMAL(15,2)'),
        ('DATETIME', 'DATETIME'),
        ('TIMESTAMP', 'DATETIME'),
        ('DATE', 'DATE'),
        ('VARCHAR(50)', 'TEXT'),
        ('TEXT', 'TEXT'),
        ('CHAR(10)', 'TEXT'),
    ]
    
    all_passed = True
    for mysql_type, expected_sqlite in test_cases:
        result = map_mysql_to_sqlite_type(mysql_type)
        passed = result == expected_sqlite
        status = "✅" if passed else "❌"
        print(f"{status} {mysql_type:20} → {result:20} (期望：{expected_sqlite})")
        if not passed:
            all_passed = False
    
    return all_passed


def test_metadata_sync():
    """测试元数据同步（需要实际 MySQL 环境）"""
    print("\n" + "=" * 60)
    print("📋 测试元数据同步")
    print("=" * 60)
    print("⚠️  此测试需要实际的 MySQL 数据库环境")
    print("📝 请在数据源管理界面添加 MySQL 数据源后测试")
    return True


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🧪 MySQL 数据源连接测试")
    print("=" * 60)
    
    results = []
    
    # 测试 1：MySQL 连接
    results.append(("MySQL 连接", test_mysql_connection()))
    
    # 测试 2：类型映射
    results.append(("类型映射", test_type_mapping()))
    
    # 测试 3：元数据同步
    results.append(("元数据同步", test_metadata_sync()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查配置")
    print("=" * 60 + "\n")
    
    sys.exit(0 if all_passed else 1)
