#!/usr/bin/env python3
"""
更新日志记录工具
用法：python log_update.py "标题" "内容" --category optimize --files file1 file2
"""
import sqlite3
import json
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "db/erp_bi.db"

CATEGORY_MAP = {
    'feature': '✨ 新功能',
    'fix': '🐛 修复',
    'optimize': '⚡ 优化',
    'security': '🔒 安全',
    'other': '📝 其他'
}

def create_log(version, title, content, category, description="", files=None, operator="mac🦀"):
    """创建更新日志"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    files_json = json.dumps(files or [], ensure_ascii=False)
    
    cursor.execute("""
        INSERT INTO system_update_logs 
        (version, title, description, content, category, operator, files_changed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (version, title, description, content, category, operator, files_json))
    
    conn.commit()
    conn.close()
    
    print(f"✅ 更新日志已记录：{CATEGORY_MAP.get(category, category)} {title}")

def main():
    parser = argparse.ArgumentParser(description='记录系统更新日志')
    parser.add_argument('title', help='更新标题')
    parser.add_argument('content', help='更新内容 (支持 Markdown)')
    parser.add_argument('--version', '-v', default='1.0.0', help='版本号')
    parser.add_argument('--category', '-c', default='other', 
                       choices=['feature', 'fix', 'optimize', 'security', 'other'],
                       help='更新分类')
    parser.add_argument('--description', '-d', default='', help='简短描述')
    parser.add_argument('--files', '-f', nargs='+', default=[], help='修改的文件列表')
    parser.add_argument('--operator', '-o', default='mac🦀', help='操作人员')
    
    args = parser.parse_args()
    
    create_log(
        version=args.version,
        title=args.title,
        content=args.content,
        category=args.category,
        description=args.description,
        files=args.files,
        operator=args.operator
    )

if __name__ == "__main__":
    main()
