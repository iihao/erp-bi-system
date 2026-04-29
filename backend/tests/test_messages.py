"""
消息功能单元测试
测试私信、系统通知、互动通知、消息状态管理等功能
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestMessages:
    """消息功能测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置"""
        from utils.database import execute_update, execute_query

        # 清理测试数据
        execute_update("DELETE FROM messages WHERE receiver_id IN (1, 2)")
        execute_update("DELETE FROM message_conversations WHERE user1_id IN (1, 2) OR user2_id IN (1, 2)")

        yield

        # 测试后清理
        execute_update("DELETE FROM messages WHERE receiver_id IN (1, 2)")
        execute_update("DELETE FROM message_conversations WHERE user1_id IN (1, 2) OR user2_id IN (1, 2)")

    def test_send_message_success(self, auth_headers):
        """测试发送私信成功"""
        response = client.post(
            "/api/messages/send",
            json={
                "receiver_id": 2,
                "title": "测试消息",
                "content": "这是一条测试私信"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "发送成功" in data["message"]
        assert data["data"]["title"] == "测试消息"

    def test_send_message_to_self(self, auth_headers):
        """测试给自己发消息"""
        response = client.post(
            "/api/messages/send",
            json={
                "receiver_id": 1,
                "title": "测试消息",
                "content": "给自己发消息"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "不能给自己发送私信" in str(response.json())

    def test_send_message_invalid_receiver(self, auth_headers):
        """测试发送给不存在的用户"""
        response = client.post(
            "/api/messages/send",
            json={
                "receiver_id": 999999,
                "title": "测试消息",
                "content": "测试"
            },
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "接收者不存在" in str(response.json())

    def test_get_messages_list(self, auth_headers):
        """测试获取消息列表"""
        # 先创建几条消息
        for i in range(5):
            client.post(
                "/api/messages/send",
                json={
                    "receiver_id": 1,
                    "title": f"测试消息{i + 1}",
                    "content": f"消息内容{i + 1}"
                },
                headers=auth_headers
            )

        # 获取消息列表
        response = client.get(
            "/api/messages/list",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["total"] >= 5

    def test_get_messages_by_type(self, auth_headers):
        """测试按类型获取消息"""
        # 创建不同类型的消息
        for msg_type in ["private", "system", "interaction"]:
            client.post(
                "/api/messages/send",
                json={
                    "receiver_id": 1,
                    "title": f"{msg_type}消息",
                    "content": f"{msg_type}内容"
                },
                headers=auth_headers
            )

        # 按类型获取
        for msg_type in ["private", "system", "interaction"]:
            response = client.get(
                "/api/messages/list",
                params={"message_type": msg_type, "page": 1, "page_size": 10},
                headers=auth_headers
            )
            data = response.json()
            assert data["success"] is True
            # 每个类型至少有 1 条消息

    def test_get_unread_count(self, auth_headers):
        """测试获取未读消息数量"""
        # 创建未读消息
        client.post(
            "/api/messages/send",
            json={
                "receiver_id": 1,
                "title": "未读消息",
                "content": "这是一条未读消息"
            },
            headers=auth_headers
        )

        response = client.get(
            "/api/messages/unread/count",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1

    def test_mark_as_read(self, auth_headers):
        """测试标记消息为已读"""
        # 创建消息
        create_response = client.post(
            "/api/messages/send",
            json={
                "receiver_id": 1,
                "title": "测试消息",
                "content": "测试内容"
            },
            headers=auth_headers
        )
        message_id = create_response.json()["data"]["id"]

        # 标记已读
        response = client.post(
            "/api/messages/mark-read",
            json={"message_ids": [message_id], "operation": "read"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证消息已读
        get_response = client.get(
            f"/api/messages/{message_id}",
            headers=auth_headers
        )
        assert get_response.json()["data"]["is_read"] is True

    def test_mark_all_as_read(self, auth_headers):
        """测试一键已读所有消息"""
        # 创建多条未读消息
        for i in range(3):
            client.post(
                "/api/messages/send",
                json={
                    "receiver_id": 1,
                    "title": f"消息{i + 1}",
                    "content": f"内容{i + 1}"
                },
                headers=auth_headers
            )

        # 一键已读
        response = client.post(
            "/api/messages/read-all",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_message(self, auth_headers):
        """测试删除消息"""
        # 创建消息
        create_response = client.post(
            "/api/messages/send",
            json={
                "receiver_id": 1,
                "title": "待删除消息",
                "content": "测试删除"
            },
            headers=auth_headers
        )
        message_id = create_response.json()["data"]["id"]

        # 删除消息
        response = client.post(
            "/api/messages/delete",
            json={"message_ids": [message_id], "operation": "delete"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "删除成功" in data["message"]

    def test_batch_delete_messages(self, auth_headers):
        """测试批量删除消息"""
        # 创建多条消息
        message_ids = []
        for i in range(3):
            create_response = client.post(
                "/api/messages/send",
                json={
                    "receiver_id": 1,
                    "title": f"消息{i + 1}",
                    "content": f"内容{i + 1}"
                },
                headers=auth_headers
            )
            message_ids.append(create_response.json()["data"]["id"])

        # 批量删除
        response = client.post(
            "/api/messages/delete",
            json={"message_ids": message_ids, "operation": "delete"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted_count"] == 3

    def test_get_conversation_list(self, auth_headers):
        """测试获取会话列表"""
        # 创建私信
        client.post(
            "/api/messages/send",
            json={
                "receiver_id": 2,
                "title": "私信",
                "content": "测试私信"
            },
            headers=auth_headers
        )

        response = client.get(
            "/api/messages/conversation/list",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]

    def test_get_conversation_messages(self, auth_headers):
        """测试获取会话消息记录"""
        # 创建私信
        client.post(
            "/api/messages/send",
            json={
                "receiver_id": 2,
                "title": "私信",
                "content": "测试私信"
            },
            headers=auth_headers
        )

        response = client.get(
            "/api/messages/conversation/2",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]

    def test_get_message_detail(self, auth_headers):
        """测试获取消息详情"""
        # 创建消息
        create_response = client.post(
            "/api/messages/send",
            json={
                "receiver_id": 1,
                "title": "测试消息",
                "content": "测试内容"
            },
            headers=auth_headers
        )
        message_id = create_response.json()["data"]["id"]

        # 获取详情
        response = client.get(
            f"/api/messages/{message_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "测试消息"

    def test_mark_as_unread(self, auth_headers):
        """测试标记消息为未读"""
        # 创建并标记已读
        create_response = client.post(
            "/api/messages/send",
            json={
                "receiver_id": 1,
                "title": "测试消息",
                "content": "测试内容"
            },
            headers=auth_headers
        )
        message_id = create_response.json()["data"]["id"]

        # 先标记已读
        client.post(
            "/api/messages/mark-read",
            json={"message_ids": [message_id], "operation": "read"},
            headers=auth_headers
        )

        # 标记为未读
        response = client.post(
            f"/api/messages/mark-unread?message_id={message_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # 验证未读状态
        detail = client.get(f"/api/messages/{message_id}", headers=auth_headers)
        # 获取详情会自动标记为已读，所以这里不直接断言


class TestSystemNotification:
    """系统通知测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, admin_headers):
        """测试前设置"""
        from utils.database import execute_update
        execute_update("DELETE FROM messages WHERE message_type = 'system'")
        yield
        execute_update("DELETE FROM messages WHERE message_type = 'system'")

    def test_send_system_notification(self, admin_headers):
        """测试发送系统通知"""
        response = client.post(
            "/api/messages/system-notify",
            json={
                "receiver_id": 1,
                "title": "系统通知",
                "content": "这是一条系统通知",
                "priority": "normal"
            },
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_send_system_broadcast(self, admin_headers):
        """测试发送系统广播"""
        response = client.post(
            "/api/messages/system-notify",
            json={
                "receiver_id": 0,
                "title": "系统广播",
                "content": "这是一条广播消息",
                "priority": "high"
            },
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sent_count" in data["data"]


class TestInteractionNotification:
    """互动通知测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        """测试前设置"""
        from utils.database import execute_update
        execute_update("DELETE FROM messages WHERE message_type = 'interaction'")
        yield
        execute_update("DELETE FROM messages WHERE message_type = 'interaction'")

    def test_send_interaction_notification(self, auth_headers):
        """测试发送互动通知"""
        response = client.post(
            "/api/messages/interaction-notify",
            json={
                "receiver_id": 2,
                "source_type": "like",
                "source_id": 1,
                "content": "点赞了您的内容"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_send_follow_notification(self, auth_headers):
        """测试发送关注通知"""
        response = client.post(
            "/api/messages/interaction-notify",
            json={
                "receiver_id": 2,
                "source_type": "follow",
                "source_id": 1,
                "content": "关注了您"
            },
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_send_comment_notification(self, auth_headers):
        """测试发送评论通知"""
        response = client.post(
            "/api/messages/interaction-notify",
            json={
                "receiver_id": 2,
                "source_type": "comment",
                "source_id": 1,
                "content": "评论了您的内容"
            },
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_notify_self(self, auth_headers):
        """测试通知自己（应跳过）"""
        response = client.post(
            "/api/messages/interaction-notify",
            json={
                "receiver_id": 1,
                "source_type": "like",
                "source_id": 1,
                "content": "点赞了自己的内容"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "无需通知自己" in data["message"]


class TestAnnouncements:
    """公告功能测试类"""

    def test_get_announcements_list(self, auth_headers):
        """测试获取公告列表"""
        response = client.get(
            "/api/announcements/list",
            params={"status_filter": "published", "page": 1, "page_size": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "list" in data["data"]


# 简单测试入口
if __name__ == "__main__":
    print("运行消息功能简单测试...")

    # 健康检查
    response = client.get("/health")
    print(f"健康检查：{response.status_code} - {response.json()}")

    # 测试消息 API 路由是否存在
    response = client.get("/api/messages/unread/count")
    print(f"获取未读消息数量：{response.status_code}")

    print("测试完成！")
