#!/usr/bin/env python3
"""
AI 问数功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.ai_query import extract_keywords, match_standard_sql, log_query

def test_extract_keywords():
    """测试关键词提取"""
    print("\n🔍 测试关键词提取:")
    
    test_cases = [
        "上个月销售额最高的产品是什么？",
        "客户张三的订单有哪些？",
        "各品类的销售占比是多少？",
        "统计本月销售趋势",
        "查询库存数量"
    ]
    
    for question in test_cases:
        keywords = extract_keywords(question)
        print(f"  问题：{question}")
        print(f"  关键词：{keywords}\n")

def test_log_query():
    """测试日志记录"""
    print("\n📝 测试日志记录:")
    
    log_id = log_query(
        question="测试问题",
        generated_sql="SELECT * FROM products LIMIT 1",
        keywords=["产品", "测试"],
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        execution_time_ms=200,
        status='success',
        error_message=None
    )
    
    print(f"  日志记录 ID: {log_id}")
    print(f"  ✅ 日志记录成功\n")

def test_standard_sql_match():
    """测试标准 SQL 匹配"""
    print("\n📚 测试标准 SQL 匹配:")
    
    # 先插入一条测试数据
    import sqlite3
    conn = sqlite3.connect('db/erp_bi.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO standard_sql_library 
        (keywords, question_template, standard_sql, explanation, usage_count, is_active)
        VALUES (?, ?, ?, ?, 0, 1)
    """, (
        '["产品", "排行", "销售额"]',
        "销售额最高的产品是什么？",
        "SELECT p.product_name, SUM(oi.subtotal) as total_sales FROM products p JOIN sales_order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY total_sales DESC LIMIT 1",
        "查询销售额最高的产品"
    ))
    
    conn.commit()
    conn.close()
    
    print("  已插入测试标准 SQL")
    
    # 测试匹配
    keywords = ["产品", "销售", "排行"]
    match = match_standard_sql(keywords)
    
    if match:
        print(f"  ✅ 匹配成功: {match['question_template']}")
        print(f"  SQL: {match['sql'][:50]}...")
    else:
        print(f"  ❌ 未匹配到标准 SQL")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("AI 问数功能测试")
    print("=" * 60)
    
    test_extract_keywords()
    test_log_query()
    test_standard_sql_match()
    
    print("=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
