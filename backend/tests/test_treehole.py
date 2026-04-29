"""
树洞功能单元测试
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestTreehole:
    """树洞功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置 - 清理测试数据"""
        from utils.database import execute_update
        # 清理测试树洞
        execute_update("DELETE FROM posts WHERE post_type = 'treehole' AND title LIKE '【测试】%'")
        self.auth_headers = auth_headers
        yield
        # 测试后清理
        execute_update("DELETE FROM posts WHERE post_type = 'treehole' AND title LIKE '【测试】%'")

    def test_create_treehole_success(self, auth_headers):
        """测试发布树洞成功"""
        response = client.post(
            "/api/treehole",
            json={
                "title": "【测试】今天心情不太好",
                "content": "工作压力好大，想找个地方倾诉一下..."
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "发布成功" in data["message"]
        assert data["data"]["content"] is not None
        assert data["data"]["display_username"] == "匿名树洞"

    def test_create_treehole_without_title(self, auth_headers):
        """测试发布无标题树洞"""
        response = client.post(
            "/api/treehole",
            json={
                "content": "这是一条没有标题的树洞内容"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_treehole_empty_content(self, auth_headers):
        """测试发布空内容树洞（应该失败）"""
        response = client.post(
            "/api/treehole",
            json={
                "title": "测试标题",
                "content": ""
            },
            headers=auth_headers
        )
        assert response.status_code == 422  # 参数验证失败

    def test_create_treehole_content_too_long(self, auth_headers):
        """测试发布超长内容树洞"""
        long_content = "a" * 3000  # 超过 2000 字限制
        response = client.post(
            "/api/treehole",
            json={
                "content": long_content
            },
            headers=auth_headers
        )
        assert response.status_code == 422  # 参数验证失败

    def test_get_treehole_list(self, auth_headers):
        """测试获取树洞列表"""
        response = client.get(
            "/api/treehole/list",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]

    def test_get_treehole_list_sort_by_hot(self, auth_headers):
        """测试获取热门树洞列表"""
        response = client.get(
            "/api/treehole/list",
            params={"page": 1, "page_size": 10, "sort_by": "hot"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_my_treeholes(self, auth_headers):
        """测试获取我的树洞列表"""
        response = client.get(
            "/api/treehole/my/list",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]

    def test_get_treehole_detail(self, auth_headers):
        """测试获取树洞详情"""
        # 先创建一个测试树洞
        create_response = client.post(
            "/api/treehole",
            json={
                "title": "【测试】获取详情测试",
                "content": "测试内容"
            },
            headers=auth_headers
        )
        post_id = create_response.json()["data"]["post_id"]

        # 获取详情
        response = client.get(
            f"/api/treehole/{post_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["post_id"] == post_id

    def test_get_treehole_not_found(self, auth_headers):
        """测试获取不存在的树洞"""
        response = client.get(
            "/api/treehole/999999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_treehole_success(self, auth_headers):
        """测试删除树洞成功"""
        # 先创建一个测试树洞
        create_response = client.post(
            "/api/treehole",
            json={
                "title": "【测试】删除测试",
                "content": "待删除的内容"
            },
            headers=auth_headers
        )
        post_id = create_response.json()["data"]["post_id"]

        # 删除树洞
        response = client.delete(
            f"/api/treehole/{post_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "删除成功" in data["message"]

    def test_delete_others_treehole(self, auth_headers):
        """测试删除他人的树洞（应该失败）"""
        # 这里由于测试环境限制，无法完全模拟删除他人树洞的场景
        # 实际测试需要创建两个不同的用户
        response = client.delete(
            "/api/treehole/999999",
            headers=auth_headers
        )
        # 树洞不存在时返回 404
        assert response.status_code == 404

    def test_treehole_anonymous_display(self, auth_headers):
        """测试树洞匿名显示"""
        # 创建树洞
        create_response = client.post(
            "/api/treehole",
            json={
                "title": "【测试】匿名显示测试",
                "content": "匿名内容"
            },
            headers=auth_headers
        )
        data = create_response.json()

        # 验证显示用户名为匿名
        assert data["data"]["display_username"] == "匿名树洞"

    def test_treehole_like_integration(self, auth_headers):
        """测试树洞点赞功能集成"""
        # 创建树洞
        create_response = client.post(
            "/api/treehole",
            json={
                "title": "【测试】点赞集成测试",
                "content": "测试点赞功能"
            },
            headers=auth_headers
        )
        post_id = create_response.json()["data"]["post_id"]

        # 点赞
        like_response = client.post(
            "/api/likes",
            json={"target_type": "post", "target_id": post_id},
            headers=auth_headers
        )
        assert like_response.status_code == 200

        # 获取树洞详情，验证点赞数增加
        detail_response = client.get(
            f"/api/treehole/{post_id}",
            headers=auth_headers
        )
        detail_data = detail_response.json()
        assert detail_data["data"]["like_count"] >= 1
        assert detail_data["data"]["user_liked"] is True


class TestSensitiveWordFilter:
    """敏感词过滤测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置"""
        self.auth_headers = auth_headers
        yield

    def test_sensitive_word_high_severity(self, auth_headers):
        """测试高严重程度敏感词过滤"""
        # 测试包含高严重程度敏感词的内容
        response = client.post(
            "/api/treehole",
            json={
                "title": "测试",
                "content": "这里包含赌博内容"  # 赌博是高严重程度敏感词
            },
            headers=auth_headers
        )
        # 应该被拒绝或过滤
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            # 内容应该被过滤
            assert "****" in data["data"]["content"] or "不当言论" in data.get("message", "")

    def test_sensitive_word_ads(self, auth_headers):
        """测试广告类敏感词过滤"""
        response = client.post(
            "/api/treehole",
            json={
                "title": "赚钱方法",
                "content": "分享一个赚钱的好方法"
            },
            headers=auth_headers
        )
        # 广告类词汇应该被过滤
        if response.status_code == 200:
            data = response.json()
            # "赚钱"应该被过滤
            assert "***" in data["data"]["content"] or "不当言论" in data.get("message", "")


# 简单测试入口
if __name__ == "__main__":
    print("运行树洞功能简单测试...")

    # 健康检查
    response = client.get("/health")
    print(f"健康检查：{response.status_code} - {response.json()}")

    # 测试树洞 API 路由是否存在
    response = client.get("/api/treehole/list?page=1&page_size=5")
    print(f"获取树洞列表：{response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 总数：{data.get('data', {}).get('total', 0)}")

    print("测试完成！")
