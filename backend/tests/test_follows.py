"""
关注功能单元测试
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestFollows:
    """关注功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前设置"""
        # 清理测试数据
        from utils.database import execute_update
        execute_update("DELETE FROM follows WHERE follower_id = 999 OR followed_id = 999")
        yield
        # 测试后清理
        execute_update("DELETE FROM follows WHERE follower_id = 999 OR followed_id = 999")

    def test_follow_success(self, auth_headers):
        """测试关注成功"""
        # 假设用户 ID 2 存在
        response = client.post(
            "/api/follows",
            json={"followed_id": 2},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "关注成功" in data["message"]

    def test_follow_self(self, auth_headers):
        """测试关注自己"""
        # 假设当前用户 ID 为 1
        response = client.post(
            "/api/follows",
            json={"followed_id": 1},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "不能关注自己" in str(response.json())

    def test_follow_duplicate(self, auth_headers):
        """测试重复关注"""
        # 先关注
        client.post(
            "/api/follows",
            json={"followed_id": 3},
            headers=auth_headers
        )
        # 再关注一次
        response = client.post(
            "/api/follows",
            json={"followed_id": 3},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "已关注" in str(response.json())

    def test_follow_nonexistent_user(self, auth_headers):
        """测试关注不存在的用户"""
        response = client.post(
            "/api/follows",
            json={"followed_id": 999999},
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "用户不存在" in str(response.json())

    def test_unfollow_success(self, auth_headers):
        """测试取消关注成功"""
        # 先关注
        client.post(
            "/api/follows",
            json={"followed_id": 4},
            headers=auth_headers
        )
        # 再取消关注
        response = client.delete(
            "/api/follows",
            params={"followed_id": 4},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "取消成功" in data["message"]

    def test_unfollow_not_following(self, auth_headers):
        """测试取消未关注的用户"""
        response = client.delete(
            "/api/follows",
            params={"followed_id": 5},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "尚未关注" in str(response.json())

    def test_get_follow_status(self, auth_headers):
        """测试获取关注状态"""
        response = client.get(
            "/api/follows/status",
            params={"user_id": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "follower_count" in data["data"]
        assert "following_count" in data["data"]
        assert "is_following" in data["data"]

    def test_get_follow_count_no_auth(self):
        """测试无需认证的获取关注数量"""
        response = client.get(
            "/api/follows/count",
            params={"user_id": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "follower_count" in data["data"]
        assert "following_count" in data["data"]

    def test_get_followers(self, auth_headers):
        """测试获取粉丝列表"""
        response = client.get(
            "/api/follows/followers",
            params={"user_id": 1, "limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]

    def test_get_following(self, auth_headers):
        """测试获取关注列表"""
        response = client.get(
            "/api/follows/following",
            params={"user_id": 1, "limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]

    def test_get_my_follows_following(self, auth_headers):
        """测试获取我的关注列表"""
        response = client.get(
            "/api/follows/my",
            params={"list_type": "following", "limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]

    def test_get_my_follows_followers(self, auth_headers):
        """测试获取我的粉丝列表"""
        response = client.get(
            "/api/follows/my",
            params={"list_type": "followers", "limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]

    def test_get_my_follows_invalid_type(self, auth_headers):
        """测试获取我的关注列表 - 无效类型"""
        response = client.get(
            "/api/follows/my",
            params={"list_type": "invalid", "limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "无效的列表类型" in str(response.json())


# 如果没有 pytest 配置，可以运行以下简单测试
if __name__ == "__main__":
    print("运行关注功能简单测试...")

    # 健康检查
    response = client.get("/health")
    print(f"健康检查：{response.status_code} - {response.json()}")

    # 测试关注 API 路由是否存在
    response = client.get("/api/follows/count?user_id=1")
    print(f"获取关注数：{response.status_code} - {response.json()}")

    print("测试完成！")
