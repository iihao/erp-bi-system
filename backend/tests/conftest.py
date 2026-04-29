"""
测试配置文件
"""
import os
import sys
from pathlib import Path
import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置测试环境变量
os.environ["ENVIRONMENT"] = "testing"
os.environ["USE_SQLITE"] = "true"
os.environ["SQLITE_DB_PATH"] = "./db/test_erp_bi.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-at-least-32-chars"
os.environ["RATE_LIMIT_ENABLED"] = "false"

# pytest 配置
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def auth_headers():
    """提供认证头部的 fixture"""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)

    # 先登录获取 token
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )

    if response.status_code == 200:
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}

    # 如果登录失败，返回空头部（某些测试可能不需要认证）
    return {}
