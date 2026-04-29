"""
点赞功能单元测试
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestLikes:
    """点赞功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前设置"""
        # 清理测试数据
        from utils.database import execute_update
        execute_update("DELETE FROM likes WHERE target_type = 'test'")
        yield
        # 测试后清理
        execute_update("DELETE FROM likes WHERE target_type = 'test'")

    def test_like_success(self, auth_headers):
        """测试点赞成功"""
        response = client.post(
            "/api/likes",
            json={"target_type": "post", "target_id": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "点赞成功" in data["message"]

    def test_like_duplicate(self, auth_headers):
        """测试重复点赞"""
        # 第一次点赞
        client.post(
            "/api/likes",
            json={"target_type": "post", "target_id": 2},
            headers=auth_headers
        )
        # 第二次点赞
        response = client.post(
            "/api/likes",
            json={"target_type": "post", "target_id": 2},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "已点赞" in str(response.json())

    def test_unlike_success(self, auth_headers):
        """测试取消点赞成功"""
        # 先点赞
        client.post(
            "/api/likes",
            json={"target_type": "post", "target_id": 3},
            headers=auth_headers
        )
        # 再取消点赞
        response = client.delete(
            "/api/likes",
            params={"target_type": "post", "target_id": 3},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "取消成功" in data["message"]

    def test_unlike_not_liked(self, auth_headers):
        """测试取消未点赞的内容"""
        response = client.delete(
            "/api/likes",
            params={"target_type": "post", "target_id": 999},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "尚未点赞" in str(response.json())

    def test_get_like_status(self, auth_headers):
        """测试获取点赞状态"""
        response = client.get(
            "/api/likes/status",
            params={"target_type": "post", "target_id": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "target_type" in data
        assert "target_id" in data
        assert "count" in data
        assert "user_liked" in data

    def test_get_like_count_no_auth(self):
        """测试无需认证的获取点赞数量"""
        response = client.get(
            "/api/likes/count",
            params={"target_type": "post", "target_id": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "count" in data["data"]

    def test_invalid_target_type(self, auth_headers):
        """测试无效的目标类型"""
        response = client.post(
            "/api/likes",
            json={"target_type": "invalid", "target_id": 1},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "无效的目标类型" in str(response.json())

    def test_get_liker_list(self, auth_headers):
        """测试获取点赞用户列表"""
        response = client.get(
            "/api/likes/list",
            params={"target_type": "post", "target_id": 1, "limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]

    def test_get_my_likes(self, auth_headers):
        """测试获取我的点赞列表"""
        response = client.get(
            "/api/likes/my",
            params={"limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]


# 如果没有 pytest 配置，可以运行以下简单测试
if __name__ == "__main__":
    print("运行点赞功能简单测试...")

    # 健康检查
    response = client.get("/health")
    print(f"健康检查：{response.status_code} - {response.json()}")

    # 测试点赞 API 路由是否存在
    response = client.get("/api/likes/count?target_type=post&target_id=1")
    print(f"获取点赞数：{response.status_code} - {response.json()}")

    print("测试完成！")
