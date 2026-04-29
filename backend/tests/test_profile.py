"""
个人主页功能单元测试
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestProfile:
    """个人主页功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前设置"""
        # 清理测试数据
        from utils.database import execute_update
        execute_update("DELETE FROM user_profiles WHERE user_id = 999")
        execute_update("DELETE FROM posts WHERE user_id = 999")
        execute_update("DELETE FROM likes WHERE user_id = 999")
        yield
        # 测试后清理
        execute_update("DELETE FROM user_profiles WHERE user_id = 999")
        execute_update("DELETE FROM posts WHERE user_id = 999")
        execute_update("DELETE FROM likes WHERE user_id = 999")

    def test_get_profile_success(self, auth_headers):
        """测试获取用户资料成功"""
        response = client.get(
            "/api/profile/1",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "user_id" in data["data"]
        assert "username" in data["data"]
        assert "message" in data

    def test_get_profile_not_found(self, auth_headers):
        """测试获取不存在的用户资料"""
        response = client.get(
            "/api/profile/999999",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "用户不存在" in str(response.json())

    def test_get_my_profile(self, auth_headers):
        """测试获取当前用户自己的资料"""
        response = client.get(
            "/api/profile",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "user_id" in data["data"]
        assert data["data"]["is_me"] is True

    def test_update_profile_success(self, auth_headers):
        """测试更新用户资料成功"""
        update_data = {
            "bio": "这是一个测试简介",
            "gender": 1,
            "location": "北京"
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["bio"] == "这是一个测试简介"
        assert data["data"]["gender"] == 1
        assert data["data"]["location"] == "北京"

    def test_update_profile_invalid_gender(self, auth_headers):
        """测试更新用户资料 - 性别值无效"""
        update_data = {
            "bio": "测试",
            "gender": 5,  # 无效值
            "location": "北京"
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # 验证错误

    def test_update_profile_bio_too_long(self, auth_headers):
        """测试更新用户资料 - 简介过长"""
        update_data = {
            "bio": "x" * 501,  # 超过 500 字限制
            "gender": 1,
            "location": "北京"
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # 验证错误

    def test_get_user_posts(self, auth_headers):
        """测试获取用户帖子列表"""
        response = client.get(
            "/api/profile/1/posts",
            params={"content_type": "post", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]

    def test_get_user_reports(self, auth_headers):
        """测试获取用户报表列表"""
        response = client.get(
            "/api/profile/1/posts",
            params={"content_type": "report", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]

    def test_get_user_posts_invalid_type(self, auth_headers):
        """测试获取用户内容 - 无效类型"""
        response = client.get(
            "/api/profile/1/posts",
            params={"content_type": "invalid", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "无效的内容类型" in str(response.json())

    def test_get_user_likes(self, auth_headers):
        """测试获取用户点赞列表"""
        response = client.get(
            "/api/profile/1/likes",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]

    def test_get_user_likes_by_type(self, auth_headers):
        """测试按类型获取用户点赞列表"""
        response = client.get(
            "/api/profile/1/likes",
            params={"target_type": "post", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_profile_stats(self, auth_headers):
        """测试获取用户统计信息"""
        response = client.get(
            "/api/profile/1/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        stats = data["data"]
        assert "user_id" in stats
        assert "follower_count" in stats
        assert "following_count" in stats
        assert "post_count" in stats
        assert "report_count" in stats
        assert "like_count" in stats

    def test_get_profile_no_auth(self):
        """测试无认证时访问个人资料页"""
        response = client.get("/api/profile/1")
        # 应该返回 401 或者返回公开信息
        assert response.status_code in [200, 401]

    def test_update_profile_no_auth(self):
        """测试无认证时更新资料"""
        update_data = {
            "bio": "测试"
        }
        response = client.put(
            "/api/profile",
            json=update_data
        )
        assert response.status_code == 401


# 简单集成测试
class TestProfileIntegration:
    """个人主页功能集成测试"""

    def test_profile_flow(self, auth_headers):
        """测试完整的个人资料流程"""
        # 1. 获取当前用户资料
        response = client.get("/api/profile", headers=auth_headers)
        assert response.status_code == 200
        profile = response.json()["data"]
        user_id = profile["user_id"]

        # 2. 更新资料
        update_data = {
            "bio": f"测试简介_{user_id}",
            "location": "测试城市"
        }
        response = client.put("/api/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200

        # 3. 验证更新后的资料
        response = client.get(f"/api/profile/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        updated_profile = response.json()["data"]
        assert updated_profile["bio"] == f"测试简介_{user_id}"
        assert updated_profile["location"] == "测试城市"

        # 4. 获取统计信息
        response = client.get(f"/api/profile/{user_id}/stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["data"]
        assert stats["user_id"] == user_id

        # 5. 获取用户内容
        response = client.get(
            f"/api/profile/{user_id}/posts",
            params={"content_type": "post", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200


# 如果没有 pytest 配置，可以运行以下简单测试
if __name__ == "__main__":
    print("运行个人主页功能简单测试...")

    # 健康检查
    response = client.get("/health")
    print(f"健康检查：{response.status_code} - {response.json()}")

    # 测试登录
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"登录：{login_response.status_code}")

    if login_response.status_code == 200:
        token = login_response.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # 测试获取个人资料
        response = client.get("/api/profile", headers=headers)
        print(f"获取个人资料：{response.status_code} - {response.json()}")

        # 测试获取用户统计
        response = client.get("/api/profile/1/stats", headers=headers)
        print(f"获取用户统计：{response.status_code} - {response.json()}")

        # 测试更新资料
        response = client.put(
            "/api/profile",
            json={"bio": "测试简介", "location": "北京"},
            headers=headers
        )
        print(f"更新资料：{response.status_code} - {response.json()}")

    print("测试完成！")
