"""
评论功能单元测试
测试评论创建、编辑、删除、回复、点赞等功能
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestComments:
    """评论功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置"""
        from utils.database import execute_update, execute_query

        # 创建测试帖子
        execute_update(
            "INSERT INTO posts (user_id, title, content, post_type) VALUES (?, ?, ?, ?)",
            (1, "测试帖子", "这是测试内容", "normal")
        )

        # 获取测试帖子 ID
        result = execute_query("SELECT post_id FROM posts WHERE title = '测试帖子' ORDER BY post_id DESC LIMIT 1")
        self.test_post_id = result[0]["post_id"] if result else 1

        yield

        # 测试后清理：删除测试评论和帖子
        execute_update(f"DELETE FROM comments WHERE target_type = 'post' AND target_id = {self.test_post_id}")
        execute_update(f"DELETE FROM posts WHERE post_id = {self.test_post_id}")

    def test_create_comment_success(self, auth_headers):
        """测试创建评论成功"""
        response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "这是一条测试评论"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "评论成功" in data["message"]
        assert data["data"]["content"] == "这是一条测试评论"
        assert data["data"]["parent_id"] == 0

    def test_create_comment_invalid_target_type(self, auth_headers):
        """测试无效的目标类型"""
        response = client.post(
            "/api/comments",
            json={
                "target_type": "invalid",
                "target_id": 1,
                "content": "测试评论"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "无效的目标类型" in str(response.json())

    def test_create_comment_target_not_found(self, auth_headers):
        """测试目标不存在"""
        response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": 999999,
                "content": "测试评论"
            },
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "目标内容不存在" in str(response.json())

    def test_create_comment_empty_content(self, auth_headers):
        """测试空内容"""
        response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": ""
            },
            headers=auth_headers
        )
        assert response.status_code == 422  # 参数验证失败

    def test_create_reply_success(self, auth_headers):
        """测试创建回复成功"""
        # 先创建父评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "父评论"
            },
            headers=auth_headers
        )
        parent_id = create_response.json()["data"]["comment_id"]

        # 创建回复
        reply_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "这是回复",
                "parent_id": parent_id
            },
            headers=auth_headers
        )
        assert reply_response.status_code == 200
        data = reply_response.json()
        assert data["data"]["parent_id"] == parent_id

    def test_create_reply_parent_not_found(self, auth_headers):
        """测试父评论不存在"""
        response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "回复",
                "parent_id": 999999
            },
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "父评论不存在" in str(response.json())

    def test_get_comments_list(self, auth_headers):
        """测试获取评论列表"""
        # 先创建几条评论
        for i in range(5):
            client.post(
                "/api/comments",
                json={
                    "target_type": "post",
                    "target_id": self.test_post_id,
                    "content": f"评论{i + 1}"
                },
                headers=auth_headers
            )

        # 获取评论列表
        response = client.get(
            "/api/comments/list",
            params={
                "target_type": "post",
                "target_id": self.test_post_id,
                "page": 1,
                "page_size": 10
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["total"] >= 5

    def test_get_comments_pagination(self, auth_headers):
        """测试评论分页"""
        # 创建 25 条评论
        for i in range(25):
            client.post(
                "/api/comments",
                json={
                    "target_type": "post",
                    "target_id": self.test_post_id,
                    "content": f"评论{i + 1}"
                },
                headers=auth_headers
            )

        # 获取第一页
        response1 = client.get(
            "/api/comments/list",
            params={
                "target_type": "post",
                "target_id": self.test_post_id,
                "page": 1,
                "page_size": 10
            },
            headers=auth_headers
        )
        data1 = response1.json()
        assert len(data1["data"]["list"]) == 10
        assert data1["data"]["has_more"] is True

        # 获取第二页
        response2 = client.get(
            "/api/comments/list",
            params={
                "target_type": "post",
                "target_id": self.test_post_id,
                "page": 2,
                "page_size": 10
            },
            headers=auth_headers
        )
        data2 = response2.json()
        assert len(data2["data"]["list"]) == 10
        assert data2["data"]["has_more"] is True

    def test_get_replies(self, auth_headers):
        """测试获取回复列表"""
        # 创建父评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "父评论"
            },
            headers=auth_headers
        )
        parent_id = create_response.json()["data"]["comment_id"]

        # 创建回复
        for i in range(3):
            client.post(
                "/api/comments",
                json={
                    "target_type": "post",
                    "target_id": self.test_post_id,
                    "content": f"回复{i + 1}",
                    "parent_id": parent_id
                },
                headers=auth_headers
            )

        # 获取回复列表
        response = client.get(
            "/api/comments/replies",
            params={
                "parent_id": parent_id,
                "page": 1,
                "page_size": 10
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["list"]) == 3

    def test_update_comment_success(self, auth_headers):
        """测试编辑评论成功"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "原始评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 编辑评论
        update_response = client.put(
            f"/api/comments/{comment_id}",
            json={"content": "编辑后的评论"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["success"] is True
        assert data["data"]["content"] == "编辑后的评论"

    def test_update_comment_not_author(self, auth_headers):
        """测试编辑他人的评论"""
        # 创建评论（使用默认用户）
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "原始评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 尝试用另一个用户编辑（这里模拟无权限情况）
        # 由于测试环境只有一个用户，我们通过修改用户 ID 来模拟
        from utils.database import execute_update
        # 将评论作者改为其他用户 ID
        execute_update("UPDATE comments SET user_id = 999 WHERE comment_id = ?", (comment_id,))

        # 尝试编辑
        update_response = client.put(
            f"/api/comments/{comment_id}",
            json={"content": "编辑后的评论"},
            headers=auth_headers
        )
        assert update_response.status_code == 403
        assert "无权限" in str(update_response.json())

    def test_delete_comment_success(self, auth_headers):
        """测试删除评论成功"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "待删除的评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 删除评论
        delete_response = client.delete(
            f"/api/comments/{comment_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] is True
        assert "删除成功" in data["message"]

        # 验证评论已被软删除（查询不到）
        get_response = client.get(
            "/api/comments/list",
            params={
                "target_type": "post",
                "target_id": self.test_post_id
            },
            headers=auth_headers
        )
        data = get_response.json()
        assert not any(c["comment_id"] == comment_id for c in data["data"]["list"])

    def test_delete_comment_not_author(self, auth_headers):
        """测试删除他人的评论"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "他人的评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 修改作者为其他用户
        from utils.database import execute_update
        execute_update("UPDATE comments SET user_id = 999 WHERE comment_id = ?", (comment_id,))

        # 尝试删除
        delete_response = client.delete(
            f"/api/comments/{comment_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 403
        assert "无权限" in str(delete_response.json())

    def test_like_comment_success(self, auth_headers):
        """测试点赞评论成功"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "待点赞的评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 点赞评论
        like_response = client.post(
            f"/api/comments/{comment_id}/like",
            headers=auth_headers
        )
        assert like_response.status_code == 200
        data = like_response.json()
        assert data["success"] is True
        assert data["data"]["user_liked"] is True
        assert data["data"]["like_count"] == 1

    def test_like_comment_duplicate(self, auth_headers):
        """测试重复点赞"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "待点赞的评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 第一次点赞
        client.post(f"/api/comments/{comment_id}/like", headers=auth_headers)

        # 第二次点赞
        like_response = client.post(
            f"/api/comments/{comment_id}/like",
            headers=auth_headers
        )
        assert like_response.status_code == 400
        assert "已点赞" in str(like_response.json())

    def test_unlike_comment_success(self, auth_headers):
        """测试取消点赞评论"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "待点赞的评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 先点赞
        client.post(f"/api/comments/{comment_id}/like", headers=auth_headers)

        # 取消点赞
        unlike_response = client.delete(
            f"/api/comments/{comment_id}/like",
            headers=auth_headers
        )
        assert unlike_response.status_code == 200
        data = unlike_response.json()
        assert data["success"] is True
        assert data["data"]["user_liked"] is False

    def test_unlike_comment_not_liked(self, auth_headers):
        """测试取消未点赞的评论"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "待点赞的评论"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 直接取消点赞
        unlike_response = client.delete(
            f"/api/comments/{comment_id}/like",
            headers=auth_headers
        )
        assert unlike_response.status_code == 400
        assert "尚未点赞" in str(unlike_response.json())

    def test_get_comment_detail(self, auth_headers):
        """测试获取评论详情"""
        # 创建评论
        create_response = client.post(
            "/api/comments",
            json={
                "target_type": "post",
                "target_id": self.test_post_id,
                "content": "测试评论详情"
            },
            headers=auth_headers
        )
        comment_id = create_response.json()["data"]["comment_id"]

        # 获取详情
        get_response = client.get(
            f"/api/comments/{comment_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["success"] is True
        assert data["data"]["content"] == "测试评论详情"

    def test_get_my_comments(self, auth_headers):
        """测试获取我的评论列表"""
        # 创建几条评论
        for i in range(3):
            client.post(
                "/api/comments",
                json={
                    "target_type": "post",
                    "target_id": self.test_post_id,
                    "content": f"我的评论{i + 1}"
                },
                headers=auth_headers
            )

        # 获取我的评论
        response = client.get(
            "/api/comments/my/list",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["list"]) >= 3


# 简单测试入口
if __name__ == "__main__":
    print("运行评论功能简单测试...")

    # 健康检查
    response = client.get("/health")
    print(f"健康检查：{response.status_code} - {response.json()}")

    # 测试评论 API 路由是否存在
    response = client.get("/api/comments/list?target_type=post&target_id=1&page=1&page_size=10")
    print(f"获取评论列表：{response.status_code}")

    print("测试完成！")
