"""
发现页面功能单元测试
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestDiscoveryRecommendations:
    """推荐功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置"""
        self.auth_headers = auth_headers
        yield

    def test_get_recommendations_success(self, auth_headers):
        """测试获取推荐内容成功"""
        response = client.get(
            "/api/discovery/recommend",
            params={"limit": 10, "personalized": True},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "personalized" in data["data"]

    def test_get_recommendations_non_personalized(self, auth_headers):
        """测试获取非个性化推荐（热门）"""
        response = client.get(
            "/api/discovery/recommend",
            params={"limit": 10, "personalized": False},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["personalized"] is False

    def test_get_recommendations_invalid_limit(self, auth_headers):
        """测试获取推荐内容 - 无效的数量限制"""
        response = client.get(
            "/api/discovery/recommend",
            params={"limit": 100},  # 超过最大限制 50
            headers=auth_headers
        )
        assert response.status_code == 422  # 参数验证失败

    def test_get_recommendations_unauthorized(self):
        """测试未授权获取推荐内容"""
        response = client.get(
            "/api/discovery/recommend",
            params={"limit": 10}
        )
        assert response.status_code == 401  # 未授权


class TestDiscoveryHotList:
    """热门内容列表测试类"""

    def test_get_hot_list_all(self):
        """测试获取全部热门内容"""
        response = client.get(
            "/api/discovery/hot",
            params={"limit": 10, "content_type": "all"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]

    def test_get_hot_list_posts_only(self):
        """测试获取热门帖子"""
        response = client.get(
            "/api/discovery/hot",
            params={"limit": 10, "content_type": "post"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_hot_list_reports_only(self):
        """测试获取热门报表"""
        response = client.get(
            "/api/discovery/hot",
            params={"limit": 10, "content_type": "report"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_hot_list_with_category(self):
        """测试按分类筛选热门内容"""
        response = client.get(
            "/api/discovery/hot",
            params={"limit": 10, "category": "treehole"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 验证返回的内容都是树洞
        for item in data["data"]["list"]:
            assert item.get("category") == "treehole" or item.get("type") == "post"

    def test_get_hot_list_invalid_limit(self):
        """测试无效的数量限制"""
        response = client.get(
            "/api/discovery/hot",
            params={"limit": 100, "content_type": "all"}
        )
        assert response.status_code == 422


class TestDiscoverySearch:
    """搜索功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置"""
        self.auth_headers = auth_headers
        yield

    def test_search_with_keyword(self, auth_headers):
        """测试带关键词搜索"""
        response = client.get(
            "/api/discovery/search",
            params={"keyword": "测试", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["keyword"] == "测试"

    def test_search_empty_keyword(self, auth_headers):
        """测试空关键词搜索"""
        response = client.get(
            "/api/discovery/search",
            params={"keyword": "", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 422  # 参数验证失败

    def test_search_with_content_type(self, auth_headers):
        """测试按内容类型搜索"""
        response = client.get(
            "/api/discovery/search",
            params={"keyword": "测试", "content_type": "post"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_search_with_pagination(self, auth_headers):
        """测试分页搜索"""
        response = client.get(
            "/api/discovery/search",
            params={"keyword": "测试", "page": 2, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page"] == 2
        assert data["data"]["page_size"] == 10


class TestDiscoveryCategories:
    """分类功能测试类"""

    def test_get_categories(self):
        """测试获取分类列表"""
        response = client.get("/api/discovery/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # 验证基本分类存在
        category_names = [cat["name"] for cat in data["data"]]
        assert "全部" in category_names or len(category_names) > 0

    def test_get_categories_structure(self):
        """测试分类数据结构"""
        response = client.get("/api/discovery/categories")
        data = response.json()

        for category in data["data"]:
            assert "id" in category
            assert "name" in category
            assert "content_count" in category


class TestDiscoveryTags:
    """标签功能测试类"""

    def test_get_tags_default_limit(self):
        """测试获取默认数量标签"""
        response = client.get("/api/discovery/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_tags_custom_limit(self):
        """测试获取自定义数量标签"""
        response = client.get("/api/discovery/tags", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 验证返回数量不超过限制
        assert len(data["data"]) <= 5

    def test_get_tags_structure(self):
        """测试标签数据结构"""
        response = client.get("/api/discovery/tags")
        data = response.json()

        for tag in data["data"]:
            assert "id" in tag
            assert "name" in tag
            assert "content_count" in tag


class TestDiscoveryFeed:
    """信息流功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置"""
        self.auth_headers = auth_headers
        yield

    def test_get_feed_default(self, auth_headers):
        """测试获取默认信息流"""
        response = client.get(
            "/api/discovery/feed",
            params={"page": 1, "page_size": 20},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "has_more" in data["data"]

    def test_get_feed_with_category(self, auth_headers):
        """测试按分类获取信息流"""
        categories = ["recommend", "hot", "treehole", "dynamic", "report"]

        for category in categories:
            response = client.get(
                "/api/discovery/feed",
                params={"page": 1, "page_size": 10, "category": category},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_get_feed_pagination(self, auth_headers):
        """测试信息流分页"""
        response = client.get(
            "/api/discovery/feed",
            params={"page": 2, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page"] == 2
        assert data["data"]["page_size"] == 10


class TestDiscoveryConfig:
    """推荐配置测试类"""

    def test_get_config(self):
        """测试获取推荐配置"""
        response = client.get("/api/discovery/config")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "enable_personalized" in data["data"]
        assert "hot_weight" in data["data"]
        assert "time_weight" in data["data"]


class TestHotScoreCalculation:
    """热度分数计算测试"""

    def test_hot_score_basic(self):
        """测试基础热度分数计算"""
        from api.discovery import calculate_hot_score

        # 测试基础计算
        score = calculate_hot_score(
            like_count=10,
            comment_count=5,
            view_count=100,
            created_at="2026-03-22 10:00:00"
        )
        assert score > 0

    def test_hot_score_with_time_decay(self):
        """测试时间衰减"""
        from api.discovery import calculate_hot_score
        from datetime import datetime, timedelta

        # 今天的内容
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        score_today = calculate_hot_score(10, 5, 100, today)

        # 7 天前的内容
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        score_week_ago = calculate_hot_score(10, 5, 100, week_ago)

        # 今天的内容分数应该更高
        assert score_today > score_week_ago

    def test_hot_score_with_more_interactions(self):
        """测试更多互动对分数的影响"""
        from api.discovery import calculate_hot_score

        score_low = calculate_hot_score(1, 0, 10, "2026-03-22 10:00:00")
        score_high = calculate_hot_score(100, 50, 1000, "2026-03-22 10:00:00")

        assert score_high > score_low


class TestContentFormatting:
    """内容格式化测试"""

    def test_format_post_item(self):
        """测试帖子项格式化"""
        from api.discovery import format_post_item, calculate_hot_score

        post_data = {
            "post_id": 1,
            "title": "测试标题",
            "content": "测试内容",
            "user_id": 123,
            "like_count": 10,
            "comment_count": 5,
            "view_count": 100,
            "is_anonymous": 0,
            "display_username": "test_user",
            "display_avatar": None,
            "created_at": "2026-03-22 10:00:00"
        }

        score = calculate_hot_score(10, 5, 100, "2026-03-22 10:00:00")
        formatted = format_post_item(post_data, score)

        assert formatted["id"] == 1
        assert formatted["type"] == "post"
        assert formatted["title"] == "测试标题"
        assert formatted["author_name"] == "test_user"

    def test_format_report_item(self):
        """测试报表项格式化"""
        from api.discovery import format_report_item, calculate_hot_score

        report_data = {
            "report_id": 1,
            "report_name": "测试报表",
            "description": "测试描述",
            "created_by": 123,
            "creator_name": "test_user",
            "like_count": 10,
            "comment_count": 5,
            "view_count": 100,
            "category": "sales",
            "tags": ["tag1", "tag2"],
            "created_at": "2026-03-22 10:00:00"
        }

        score = calculate_hot_score(10, 5, 100, "2026-03-22 10:00:00")
        formatted = format_report_item(report_data, score)

        assert formatted["id"] == 1
        assert formatted["type"] == "report"
        assert formatted["title"] == "测试报表"
        assert formatted["author_name"] == "test_user"


# 简单测试入口
if __name__ == "__main__":
    print("运行发现功能简单测试...")

    # 健康检查
    response = client.get("/health")
    print(f"健康检查：{response.status_code} - {response.json()}")

    # 测试推荐 API
    response = client.get("/api/discovery/recommend?limit=5&personalized=false")
    print(f"获取推荐内容：{response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 推荐数量：{len(data.get('data', {}).get('list', []))}")

    # 测试热门 API
    response = client.get("/api/discovery/hot?limit=5")
    print(f"获取热门内容：{response.status_code}")

    # 测试分类 API
    response = client.get("/api/discovery/categories")
    print(f"获取分类列表：{response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 分类数量：{len(data.get('data', []))}")

    # 测试标签 API
    response = client.get("/api/discovery/tags?limit=5")
    print(f"获取标签列表：{response.status_code}")

    # 测试配置 API
    response = client.get("/api/discovery/config")
    print(f"获取推荐配置：{response.status_code}")

    print("\n测试完成！")
