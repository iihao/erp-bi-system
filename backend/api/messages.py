"""
消息功能 API
支持私信、系统通知、互动通知
提供消息发送、接收、已读/未读状态管理、批量操作等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from utils.database import execute_query, execute_update
from api.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["消息"])


# ===========================================
# 请求/响应模型
# ===========================================

class MessageSendRequest(BaseModel):
    """发送私信请求"""
    receiver_id: int = Field(..., description="接收者 ID")
    title: str = Field(..., min_length=1, max_length=200, description="消息标题")
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")


class SystemNotifyRequest(BaseModel):
    """系统通知请求"""
    receiver_id: int = Field(..., description="接收者 ID（0 表示广播给所有用户）")
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: str = Field(..., min_length=1, max_length=5000, description="通知内容")
    priority: str = Field(default="normal", description="优先级：low/normal/high/urgent")
    source_type: Optional[str] = Field(default=None, description="来源类型")
    source_id: Optional[int] = Field(default=None, description="来源 ID")
    source_url: Optional[str] = Field(default=None, description="来源链接")


class InteractionNotifyRequest(BaseModel):
    """互动通知请求（点赞、评论、关注）"""
    receiver_id: int = Field(..., description="接收者 ID")
    source_type: str = Field(..., description="来源类型：like/comment/follow")
    source_id: int = Field(..., description="来源 ID")
    content: str = Field(..., description="通知内容")
    source_url: Optional[str] = Field(default=None, description="来源链接")


class MessageBatchOperationRequest(BaseModel):
    """批量操作请求"""
    message_ids: List[int] = Field(..., description="消息 ID 列表")
    operation: str = Field(..., description="操作类型：read/unread/delete")


class MessageItem(BaseModel):
    """消息项"""
    id: int
    message_type: str
    sender_id: Optional[int]
    sender_name: Optional[str]
    sender_avatar: Optional[str]
    receiver_id: int
    title: str
    content: str
    is_read: bool
    read_at: Optional[str]
    source_type: Optional[str]
    source_id: Optional[int]
    source_url: Optional[str]
    extra_json: Optional[dict]
    created_at: str


class MessageListResponse(BaseModel):
    """消息列表响应"""
    success: bool
    data: dict
    message: str


class MessageResponse(BaseModel):
    """消息操作响应"""
    success: bool
    message: str
    data: dict


# ===========================================
# 辅助函数
# ===========================================

def get_user_info(user_id: int) -> Optional[dict]:
    """获取用户信息"""
    result = execute_query(
        "SELECT user_id, username, avatar_url FROM users WHERE user_id = ?",
        (user_id,)
    )
    return result[0] if result else None


def get_message_by_id(message_id: int) -> Optional[dict]:
    """根据 ID 获取消息"""
    result = execute_query(
        """
        SELECT m.*, s.username as sender_name, s.avatar_url as sender_avatar
        FROM messages m
        LEFT JOIN users s ON m.sender_id = s.user_id
        WHERE m.id = ?
        """,
        (message_id,)
    )
    return result[0] if result else None


def get_conversation_id(user1_id: int, user2_id: int) -> int:
    """获取或创建会话 ID"""
    # 确保 user1_id < user2_id 以保证唯一性
    if user1_id > user2_id:
        user1_id, user2_id = user2_id, user1_id

    result = execute_query(
        "SELECT id FROM message_conversations WHERE user1_id = ? AND user2_id = ?",
        (user1_id, user2_id)
    )
    if result:
        return result[0]["id"]

    # 创建新会话
    result = execute_update(
        """INSERT INTO message_conversations (user1_id, user2_id)
           VALUES (?, ?)""",
        (user1_id, user2_id)
    )
    return result


def update_conversation(user1_id: int, user2_id: int, message_id: int, preview: str):
    """更新会话信息"""
    # 确保 user1_id < user2_id
    if user1_id > user2_id:
        user1_id, user2_id = user2_id, user1_id

    execute_update(
        """UPDATE message_conversations SET
           last_message_id = ?, last_message_preview = ?, last_message_time = CURRENT_TIMESTAMP,
           unread_count_user1 = unread_count_user1 + 1,
           updated_at = CURRENT_TIMESTAMP
           WHERE user1_id = ? AND user2_id = ?""",
        (message_id, preview[:100], user1_id, user2_id)
    )


def format_message(message: dict, current_user_id: int) -> dict:
    """格式化消息数据"""
    return {
        "id": message["id"],
        "message_type": message["message_type"],
        "sender_id": message.get("sender_id"),
        "sender_name": message.get("sender_name"),
        "sender_avatar": message.get("sender_avatar"),
        "receiver_id": message["receiver_id"],
        "title": message["title"],
        "content": message["content"],
        "is_read": bool(message.get("is_read", 0)),
        "read_at": str(message.get("read_at", ""))[:19] if message.get("read_at") else None,
        "source_type": message.get("source_type"),
        "source_id": message.get("source_id"),
        "source_url": message.get("source_url"),
        "extra_json": message.get("extra_json"),
        "created_at": str(message.get("created_at", ""))[:19]
    }


def create_interaction_notification(
    receiver_id: int,
    sender_id: int,
    source_type: str,
    source_id: int,
    content: str,
    source_url: Optional[str] = None
):
    """创建互动通知"""
    # 检查用户的通知设置
    settings = execute_query(
        "SELECT * FROM notification_settings WHERE user_id = ?",
        (receiver_id,)
    )

    # 如果用户关闭了对应类型的通知，则不创建
    if settings:
        s = settings[0]
        if source_type == "like" and not s.get("enable_like_notification", 1):
            return
        if source_type == "comment" and not s.get("enable_comment_notification", 1):
            return
        if source_type == "follow" and not s.get("enable_follow_notification", 1):
            return

    # 确定标题
    title_map = {
        "like": "新的点赞",
        "comment": "新的评论",
        "follow": "新的关注"
    }
    title = title_map.get(source_type, "新的互动")

    # 插入消息
    execute_update(
        """INSERT INTO messages (message_type, sender_id, receiver_id, title, content, source_type, source_id, source_url)
           VALUES ('interaction', ?, ?, ?, ?, ?, ?, ?)""",
        (sender_id, receiver_id, title, content, source_type, source_id, source_url)
    )


# ===========================================
# API 端点
# ===========================================

@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: MessageSendRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发送私信

    Args:
        request: 发送请求
        current_user: 当前用户

    Returns:
        发送结果
    """
    from core.security import decode_token
    sender_id = decode_token(current_user.get("token"))

    # 验证接收者是否存在
    receiver = get_user_info(request.receiver_id)
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4001, "message": "接收者不存在"}
        )

    # 不能给自己发私信
    if receiver["user_id"] == sender_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4002, "message": "不能给自己发送私信"}
        )

    try:
        # 插入消息
        result = execute_update(
            """INSERT INTO messages (message_type, sender_id, receiver_id, title, content)
               VALUES ('private', ?, ?, ?, ?)""",
            (sender_id, request.receiver_id, request.title, request.content)
        )
        message_id = result

        # 更新会话
        update_conversation(sender_id, request.receiver_id, message_id, request.content)

        # 获取创建的消息
        new_message = get_message_by_id(message_id)

        return MessageResponse(
            success=True,
            message="发送成功",
            data=format_message(new_message, sender_id)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"发送失败：{str(e)}"}
        )


@router.post("/system-notify", response_model=MessageResponse)
async def send_system_notification(
    request: SystemNotifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发送系统通知（需要管理员权限）

    Args:
        request: 通知请求
        current_user: 当前用户（需要管理员）

    Returns:
        发送结果
    """
    from core.security import decode_token
    from api.auth import check_admin

    admin = check_admin(current_user)
    sender_id = decode_token(current_user.get("token"))

    try:
        if request.receiver_id == 0:
            # 广播给所有用户
            users = execute_query("SELECT user_id FROM users WHERE status = 1")
            message_ids = []
            for user in users:
                result = execute_update(
                    """INSERT INTO messages (message_type, sender_id, receiver_id, title, content, priority)
                       VALUES ('system', ?, ?, ?, ?, ?)""",
                    (sender_id, user["user_id"], request.title, request.content, request.priority)
                )
                message_ids.append(result)

            return MessageResponse(
                success=True,
                message=f"广播成功，已发送给 {len(message_ids)} 位用户",
                data={"sent_count": len(message_ids)}
            )
        else:
            # 发送给指定用户
            receiver = get_user_info(request.receiver_id)
            if not receiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error_code": 4001, "message": "接收者不存在"}
                )

            result = execute_update(
                """INSERT INTO messages (message_type, sender_id, receiver_id, title, content, priority, source_type, source_id, source_url)
                   VALUES ('system', ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sender_id, request.receiver_id, request.title, request.content, request.priority,
                 request.source_type, request.source_id, request.source_url)
            )

            return MessageResponse(
                success=True,
                message="发送成功",
                data={"message_id": result}
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"发送失败：{str(e)}"}
        )


@router.post("/interaction-notify", response_model=MessageResponse)
async def send_interaction_notification(
    request: InteractionNotifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发送互动通知（点赞、评论、关注）

    Args:
        request: 通知请求
        current_user: 当前用户

    Returns:
        发送结果
    """
    from core.security import decode_token
    sender_id = decode_token(current_user.get("token"))

    # 验证接收者是否存在
    receiver = get_user_info(request.receiver_id)
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4001, "message": "接收者不存在"}
        )

    # 不能通知自己
    if receiver["user_id"] == sender_id:
        return MessageResponse(
            success=True,
            message="无需通知自己",
            data={}
        )

    try:
        create_interaction_notification(
            receiver_id=request.receiver_id,
            sender_id=sender_id,
            source_type=request.source_type,
            source_id=request.source_id,
            content=request.content,
            source_url=request.source_url
        )

        return MessageResponse(
            success=True,
            message="通知已发送",
            data={}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"发送失败：{str(e)}"}
        )


@router.get("/list", response_model=MessageListResponse)
async def get_messages(
    message_type: Optional[str] = Query(default=None, description="消息类型：private/system/interaction"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取消息列表

    Args:
        message_type: 消息类型
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        消息列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 计算分页
    offset = (page - 1) * page_size

    # 构建查询
    base_sql = """
        SELECT m.*, s.username as sender_name, s.avatar_url as sender_avatar
        FROM messages m
        LEFT JOIN users s ON m.sender_id = s.user_id
        WHERE m.receiver_id = ? AND m.deleted_by_receiver = 0
    """
    params = [user_id]

    if message_type:
        base_sql += " AND m.message_type = ?"
        params.append(message_type)

    # 查询消息列表
    messages = execute_query(
        f"{base_sql} ORDER BY m.created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    )

    # 获取总数
    count_sql = "SELECT COUNT(*) as count FROM messages WHERE receiver_id = ? AND deleted_by_receiver = 0"
    count_params = [user_id]
    if message_type:
        count_sql += " AND message_type = ?"
        count_params.append(message_type)

    count_result = execute_query(count_sql, count_params)
    total = count_result[0]["count"] if count_result else 0

    # 格式化消息数据
    message_list = [format_message(m, user_id) for m in (messages or [])]

    # 获取未读数统计
    unread_stats = execute_query(
        """SELECT
            COUNT(*) as total_unread,
            SUM(CASE WHEN message_type = 'private' THEN 1 ELSE 0 END) as private_unread,
            SUM(CASE WHEN message_type = 'system' THEN 1 ELSE 0 END) as system_unread,
            SUM(CASE WHEN message_type = 'interaction' THEN 1 ELSE 0 END) as interaction_unread
         FROM messages
         WHERE receiver_id = ? AND is_read = 0 AND deleted_by_receiver = 0""",
        (user_id,)
    )

    return MessageListResponse(
        success=True,
        data={
            "list": message_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(message_list) < total,
            "unread_stats": unread_stats[0] if unread_stats else {
                "total_unread": 0, "private_unread": 0,
                "system_unread": 0, "interaction_unread": 0
            }
        },
        message="获取成功"
    )


@router.get("/conversation/list", response_model=MessageListResponse)
async def get_conversations(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取私信会话列表

    Args:
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        会话列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 计算分页
    offset = (page - 1) * page_size

    # 查询会话列表（用户参与的会话）
    conversations = execute_query(
        """
        SELECT c.*,
               CASE WHEN c.user1_id = ? THEN c.unread_count_user1 ELSE c.unread_count_user2 END as unread_count,
               CASE WHEN c.user1_id = ? THEN u2.user_id ELSE u1.user_id END as other_user_id,
               CASE WHEN c.user1_id = ? THEN u2.username ELSE u1.username END as other_username,
               CASE WHEN c.user1_id = ? THEN u2.avatar_url ELSE u1.avatar_url END as other_avatar
        FROM message_conversations c
        JOIN users u1 ON c.user1_id = u1.user_id
        JOIN users u2 ON c.user2_id = u2.user_id
        WHERE (c.user1_id = ? OR c.user2_id = ?)
          AND NOT (c.user1_id = ? AND c.deleted_by_user1 = 1)
          AND NOT (c.user2_id = ? AND c.deleted_by_user2 = 1)
        ORDER BY c.last_message_time DESC NULLS LAST, c.updated_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, page_size, offset)
    )

    # 获取总数
    count_result = execute_query(
        """SELECT COUNT(*) as count FROM message_conversations c
           WHERE (c.user1_id = ? OR c.user2_id = ?)
             AND NOT (c.user1_id = ? AND c.deleted_by_user1 = 1)
             AND NOT (c.user2_id = ? AND c.deleted_by_user2 = 1)""",
        (user_id, user_id, user_id, user_id)
    )
    total = count_result[0]["count"] if count_result else 0

    # 格式化数据
    conversation_list = []
    for c in (conversations or []):
        conversation_list.append({
            "id": c["id"],
            "other_user_id": c["other_user_id"],
            "other_username": c["other_username"],
            "other_avatar": c.get("other_avatar"),
            "last_message_id": c.get("last_message_id"),
            "last_message_preview": c.get("last_message_preview"),
            "last_message_time": str(c.get("last_message_time", ""))[:19] if c.get("last_message_time") else None,
            "unread_count": c.get("unread_count", 0)
        })

    return MessageListResponse(
        success=True,
        data={
            "list": conversation_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(conversation_list) < total
        },
        message="获取成功"
    )


@router.get("/conversation/{user_id}", response_model=MessageListResponse)
async def get_conversation_messages(
    user_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取与指定用户的私信记录

    Args:
        user_id: 对方用户 ID
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        私信记录列表
    """
    from core.security import decode_token
    my_id = decode_token(current_user.get("token"))

    # 计算分页
    offset = (page - 1) * page_size

    # 确保 user1_id < user2_id
    user1_id, user2_id = min(my_id, user_id), max(my_id, user_id)

    # 查询消息记录
    messages = execute_query(
        """
        SELECT m.*, s.username as sender_name, s.avatar_url as sender_avatar
        FROM messages m
        LEFT JOIN users s ON m.sender_id = s.user_id
        WHERE m.message_type = 'private'
          AND ((m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?))
          AND m.deleted_by_receiver = 0 AND m.deleted_by_sender = 0
        ORDER BY m.created_at ASC
        LIMIT ? OFFSET ?
        """,
        (my_id, user_id, user_id, my_id, page_size, offset)
    )

    # 获取总数
    count_result = execute_query(
        """SELECT COUNT(*) as count FROM messages m
           WHERE m.message_type = 'private'
             AND ((m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?))
             AND m.deleted_by_receiver = 0 AND m.deleted_by_sender = 0""",
        (my_id, user_id, user_id, my_id)
    )
    total = count_result[0]["count"] if count_result else 0

    # 格式化消息数据
    message_list = [format_message(m, my_id) for m in (messages or [])]

    return MessageListResponse(
        success=True,
        data={
            "list": message_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(message_list) < total
        },
        message="获取成功"
    )


@router.post("/mark-read", response_model=MessageResponse)
async def mark_as_read(
    request: MessageBatchOperationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    批量标记消息为已读

    Args:
        request: 批量操作请求
        current_user: 当前用户

    Returns:
        操作结果
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    if not request.message_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "消息 ID 不能为空"}
        )

    try:
        placeholders = ",".join(["?" for _ in request.message_ids])
        execute_update(
            f"""UPDATE messages SET is_read = 1, read_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders}) AND receiver_id = ?""",
            request.message_ids + [user_id]
        )

        # 更新会话未读数
        execute_update(
            f"""UPDATE message_conversations SET
                unread_count_user1 = GREATEST(0, unread_count_user1 - ?),
                unread_count_user2 = GREATEST(0, unread_count_user2 - ?)
                WHERE last_message_id IN ({placeholders})""",
            [len(request.message_ids), len(request.message_ids)] + request.message_ids
        )

        return MessageResponse(
            success=True,
            message="标记成功",
            data={"marked_count": len(request.message_ids)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"操作失败：{str(e)}"}
        )


@router.post("/mark-unread", response_model=MessageResponse)
async def mark_as_unread(
    message_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    标记单条消息为未读

    Args:
        message_id: 消息 ID
        current_user: 当前用户

    Returns:
        操作结果
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 验证消息是否存在且属于当前用户
    message = get_message_by_id(message_id)
    if not message or message["receiver_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "消息不存在"}
        )

    try:
        execute_update(
            "UPDATE messages SET is_read = 0, read_at = NULL WHERE id = ? AND receiver_id = ?",
            (message_id, user_id)
        )

        return MessageResponse(
            success=True,
            message="操作成功",
            data={}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"操作失败：{str(e)}"}
        )


@router.post("/delete", response_model=MessageResponse)
async def delete_messages(
    request: MessageBatchOperationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    批量删除消息

    Args:
        request: 批量操作请求
        current_user: 当前用户

    Returns:
        操作结果
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    if not request.message_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "消息 ID 不能为空"}
        )

    try:
        # 检查是否有私信，需要同时更新 sender 和 receiver 的删除状态
        messages = execute_query(
            f"SELECT id, message_type, sender_id, receiver_id FROM messages WHERE id IN ({','.join(['?' for _ in request.message_ids])})",
            request.message_ids
        )

        for msg in messages:
            if msg["message_type"] == "private":
                # 私信：根据发送者/接收者设置不同的删除标记
                if msg["sender_id"] == user_id:
                    execute_update(
                        "UPDATE messages SET deleted_by_sender = 1 WHERE id = ?",
                        (msg["id"],)
                    )
                elif msg["receiver_id"] == user_id:
                    execute_update(
                        "UPDATE messages SET deleted_by_receiver = 1 WHERE id = ?",
                        (msg["id"],)
                    )
            else:
                # 系统/互动消息：只设置接收者删除标记
                if msg["receiver_id"] == user_id:
                    execute_update(
                        "UPDATE messages SET deleted_by_receiver = 1 WHERE id = ?",
                        (msg["id"],)
                    )

        return MessageResponse(
            success=True,
            message="删除成功",
            data={"deleted_count": len(request.message_ids)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"删除失败：{str(e)}"}
        )


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_as_read(
    message_type: Optional[str] = Query(default=None, description="消息类型"),
    current_user: dict = Depends(get_current_user)
):
    """
    一键已读所有消息

    Args:
        message_type: 消息类型（可选）
        current_user: 当前用户

    Returns:
        操作结果
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    try:
        if message_type:
            execute_update(
                """UPDATE messages SET is_read = 1, read_at = CURRENT_TIMESTAMP
                   WHERE receiver_id = ? AND message_type = ? AND is_read = 0""",
                (user_id, message_type)
            )
        else:
            execute_update(
                """UPDATE messages SET is_read = 1, read_at = CURRENT_TIMESTAMP
                   WHERE receiver_id = ? AND is_read = 0""",
                (user_id,)
            )

        # 重置会话未读数
        if message_type == "private" or not message_type:
            execute_update(
                """UPDATE message_conversations SET
                   unread_count_user1 = 0, unread_count_user2 = 0
                   WHERE (user1_id = ? OR user2_id = ?)""",
                (user_id, user_id)
            )

        return MessageResponse(
            success=True,
            message="操作成功",
            data={}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"操作失败：{str(e)}"}
        )


@router.get("/unread/count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user)
):
    """
    获取未读消息数量

    Args:
        current_user: 当前用户

    Returns:
        未读数量统计
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    result = execute_query(
        """SELECT
            COUNT(*) as total,
            SUM(CASE WHEN message_type = 'private' THEN 1 ELSE 0 END) as private,
            SUM(CASE WHEN message_type = 'system' THEN 1 ELSE 0 END) as system,
            SUM(CASE WHEN message_type = 'interaction' THEN 1 ELSE 0 END) as interaction
         FROM messages
         WHERE receiver_id = ? AND is_read = 0 AND deleted_by_receiver = 0""",
        (user_id,)
    )

    stats = result[0] if result else {"total": 0, "private": 0, "system": 0, "interaction": 0}

    return {
        "success": True,
        "data": {
            "total": stats["total"] or 0,
            "private": stats["private"] or 0,
            "system": stats["system"] or 0,
            "interaction": stats["interaction"] or 0
        },
        "message": "获取成功"
    }


@router.get("/{message_id}")
async def get_message(
    message_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取单条消息详情

    Args:
        message_id: 消息 ID
        current_user: 当前用户

    Returns:
        消息详情
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    message = get_message_by_id(message_id)
    if not message or message["receiver_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "消息不存在"}
        )

    # 自动标记为已读
    if not message["is_read"]:
        execute_update(
            "UPDATE messages SET is_read = 1, read_at = CURRENT_TIMESTAMP WHERE id = ?",
            (message_id,)
        )

    return {
        "success": True,
        "data": format_message(message, user_id),
        "message": "获取成功"
    }


# ===========================================
# 公告 API
# ===========================================

announcement_router = APIRouter(prefix="/api/announcements", tags=["公告"])


@announcement_router.get("/list")
async def get_announcements(
    status_filter: Optional[str] = Query(default="published", description="状态：draft/published/archived"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """获取公告列表"""
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    offset = (page - 1) * page_size

    # 只返回已发布的公告（普通用户）或已发布 + 草稿（管理员）
    is_admin = current_user.get("role") == "admin"

    if is_admin and status_filter:
        status_condition = "status = ?"
        status_params = [status_filter]
    else:
        status_condition = "status = 'published'"
        status_params = []

    # 查询公告
    announcements = execute_query(
        f"""
        SELECT a.*, u.username as author_name
        FROM announcements a
        LEFT JOIN users u ON a.author_id = u.user_id
        WHERE {status_condition}
        ORDER BY a.is_sticky DESC, a.published_at DESC
        LIMIT ? OFFSET ?
        """,
        status_params + [page_size, offset]
    )

    # 总数
    count_result = execute_query(
        f"SELECT COUNT(*) as count FROM announcements WHERE {status_condition}",
        status_params
    )
    total = count_result[0]["count"] if count_result else 0

    # 格式化数据
    announcement_list = []
    for a in (announcements or []):
        announcement_list.append({
            "id": a["id"],
            "title": a["title"],
            "content": a["content"],
            "status": a["status"],
            "priority": a.get("priority", "normal"),
            "is_sticky": bool(a.get("is_sticky", 0)),
            "view_count": a.get("view_count", 0),
            "author_name": a.get("author_name"),
            "published_at": str(a.get("published_at", ""))[:19] if a.get("published_at") else None,
            "created_at": str(a.get("created_at", ""))[:19]
        })

    return {
        "success": True,
        "data": {
            "list": announcement_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(announcement_list) < total
        },
        "message": "获取成功"
    }


@announcement_router.get("/{announcement_id}")
async def get_announcement(
    announcement_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取公告详情"""
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    announcement = execute_query(
        """
        SELECT a.*, u.username as author_name, u.avatar_url as author_avatar
        FROM announcements a
        LEFT JOIN users u ON a.author_id = u.user_id
        WHERE a.id = ?
        """,
        (announcement_id,)
    )

    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4001, "message": "公告不存在"}
        )

    a = announcement[0]

    # 检查权限：非管理员不能查看未发布的公告
    if a["status"] != "published" and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": 4002, "message": "无权查看此公告"}
        )

    # 记录查看（仅已发布公告）
    if a["status"] == "published":
        # 检查是否已查看
        viewed = execute_query(
            "SELECT id FROM announcement_views WHERE announcement_id = ? AND user_id = ?",
            (announcement_id, user_id)
        )
        if not viewed:
            execute_update(
                "INSERT INTO announcement_views (announcement_id, user_id) VALUES (?, ?)",
                (announcement_id, user_id)
            )
            execute_update(
                "UPDATE announcements SET view_count = view_count + 1 WHERE id = ?",
                (announcement_id,)
            )

    return {
        "success": True,
        "data": {
            "id": a["id"],
            "title": a["title"],
            "content": a["content"],
            "content_html": a.get("content_html"),
            "status": a["status"],
            "priority": a.get("priority", "normal"),
            "is_sticky": bool(a.get("is_sticky", 0)),
            "view_count": a.get("view_count", 0),
            "author_name": a.get("author_name"),
            "author_avatar": a.get("author_avatar"),
            "published_at": str(a.get("published_at", ""))[:19] if a.get("published_at") else None,
            "created_at": str(a.get("created_at", ""))[:19]
        },
        "message": "获取成功"
    }
