"""
评论功能 API
提供评论发布、回复、编辑、删除、点赞等功能
支持嵌套评论（回复评论）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from utils.database import execute_query, execute_update
from api.auth import get_current_user

router = APIRouter(prefix="/api/comments", tags=["评论"])


# ===========================================
# 请求/响应模型
# ===========================================

class CommentCreateRequest(BaseModel):
    """创建评论请求"""
    target_type: str = Field(..., description="目标类型：post-帖子，report-报表")
    target_id: int = Field(..., description="目标 ID")
    content: str = Field(..., min_length=1, max_length=2000, description="评论内容")
    parent_id: Optional[int] = Field(default=0, description="父评论 ID，用于回复评论")


class CommentUpdateRequest(BaseModel):
    """更新评论请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="评论内容")


class CommentItem(BaseModel):
    """评论项"""
    comment_id: int
    user_id: int
    username: str
    avatar_url: Optional[str]
    target_type: str
    target_id: int
    parent_id: int
    content: str
    like_count: int
    reply_count: int
    status: int
    created_at: str
    updated_at: str
    user_liked: bool


class CommentListResponse(BaseModel):
    """评论列表响应"""
    success: bool
    data: dict
    message: str


class CommentResponse(BaseModel):
    """评论操作响应"""
    success: bool
    message: str
    data: dict


# ===========================================
# 辅助函数
# ===========================================

def validate_target_type(target_type: str) -> bool:
    """验证目标类型"""
    return target_type in ["post", "report"]


def get_comment_by_id(comment_id: int) -> Optional[dict]:
    """根据 ID 获取评论"""
    result = execute_query(
        """
        SELECT c.*, u.username, u.avatar_url
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.comment_id = ?
        """,
        (comment_id,)
    )
    return result[0] if result else None


def check_user_liked(user_id: int, comment_id: int) -> bool:
    """检查用户是否已点赞评论"""
    result = execute_query(
        "SELECT like_id FROM likes WHERE user_id = ? AND target_type = 'comment' AND target_id = ?",
        (user_id, comment_id)
    )
    return bool(result)


def get_reply_count(parent_id: int) -> int:
    """获取评论的回复数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM comments WHERE parent_id = ? AND status = 1",
        (parent_id,)
    )
    return result[0]["count"] if result else 0


def update_target_comment_count(target_type: str, target_id: int, delta: int):
    """更新目标的评论计数"""
    if target_type == "post":
        execute_update(
            "UPDATE posts SET comment_count = GREATEST(0, comment_count + ?) WHERE post_id = ?",
            (delta, target_id)
        )
    elif target_type == "report":
        execute_update(
            "UPDATE report_configs SET comment_count = GREATEST(0, comment_count + ?) WHERE report_id = ?",
            (delta, target_id)
        )


def create_notification(user_id: int, sender_id: int, notification_type: str,
                       target_type: str, target_id: int, content: str):
    """创建通知"""
    execute_update(
        """INSERT INTO notifications (user_id, sender_id, notification_type, target_type, target_id, content)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, sender_id, notification_type, target_type, target_id, content)
    )


def format_comment(comment: dict, current_user_id: Optional[int] = None) -> dict:
    """格式化评论数据"""
    return {
        "comment_id": comment["comment_id"],
        "user_id": comment["user_id"],
        "username": comment["username"],
        "avatar_url": comment.get("avatar_url"),
        "target_type": comment["target_type"],
        "target_id": comment["target_id"],
        "parent_id": comment.get("parent_id", 0),
        "content": comment["content"],
        "like_count": comment.get("like_count", 0),
        "reply_count": get_reply_count(comment["comment_id"]),
        "status": comment.get("status", 1),
        "created_at": str(comment.get("created_at", ""))[:19],
        "updated_at": str(comment.get("updated_at", ""))[:19],
        "user_liked": check_user_liked(current_user_id, comment["comment_id"]) if current_user_id else False
    }


# ===========================================
# API 端点
# ===========================================

@router.post("", response_model=CommentResponse)
async def create_comment(
    request: CommentCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建评论或回复评论

    Args:
        request: 创建评论请求
        current_user: 当前用户

    Returns:
        创建结果

    Raises:
        HTTPException: 创建失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 验证目标类型
    if not validate_target_type(request.target_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "无效的目标类型"}
        )

    # 验证目标是否存在
    if request.target_type == "post":
        target = execute_query("SELECT post_id, user_id FROM posts WHERE post_id = ? AND status = 1", (request.target_id,))
    else:  # report
        target = execute_query("SELECT report_id, user_id FROM report_configs WHERE report_id = ?", (request.target_id,))

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "目标内容不存在"}
        )

    # 如果是回复评论，验证父评论是否存在
    if request.parent_id and request.parent_id != 0:
        parent_comment = get_comment_by_id(request.parent_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": 4003, "message": "父评论不存在"}
            )
        # 确保回复的是同一目标
        if parent_comment["target_type"] != request.target_type or parent_comment["target_id"] != request.target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error_code": 4004, "message": "评论目标不匹配"}
            )

    try:
        # 插入评论
        result = execute_update(
            """INSERT INTO comments (user_id, target_type, target_id, parent_id, content)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, request.target_type, request.target_id, request.parent_id or 0, request.content)
        )
        comment_id = result

        # 更新目标评论计数
        update_target_comment_count(request.target_type, request.target_id, 1)

        # 创建通知（如果是回复评论，通知父评论作者；否则通知目标作者）
        if request.parent_id and request.parent_id != 0:
            parent_comment = get_comment_by_id(request.parent_id)
            if parent_comment and parent_comment["user_id"] != user_id:
                create_notification(
                    user_id=parent_comment["user_id"],
                    sender_id=user_id,
                    notification_type="reply",
                    target_type=request.target_type,
                    target_id=request.target_id,
                    content="回复了您的评论"
                )
        else:
            # 通知目标作者
            if target[0]["user_id"] != user_id:
                create_notification(
                    user_id=target[0]["user_id"],
                    sender_id=user_id,
                    notification_type="comment",
                    target_type=request.target_type,
                    target_id=request.target_id,
                    content="评论了您的内容"
                )

        # 获取新创建的评论
        new_comment = get_comment_by_id(comment_id)

        return CommentResponse(
            success=True,
            message="评论成功",
            data=format_comment(new_comment, user_id)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"评论失败：{str(e)}"}
        )


@router.get("/list", response_model=CommentListResponse)
async def get_comments(
    target_type: str,
    target_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query(default="created_at", description="排序字段：created_at-时间，like_count-热度"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取评论列表（支持分页和排序）

    Args:
        target_type: 目标类型
        target_id: 目标 ID
        page: 页码
        page_size: 每页数量
        sort_by: 排序字段
        current_user: 当前用户

    Returns:
        评论列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 验证目标类型
    if not validate_target_type(target_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "无效的目标类型"}
        )

    # 验证排序字段
    if sort_by not in ["created_at", "like_count"]:
        sort_by = "created_at"

    # 计算分页
    offset = (page - 1) * page_size

    # 构建排序 SQL
    order_sql = f"c.{sort_by} DESC"

    # 查询评论列表（只获取一级评论）
    comments = execute_query(
        f"""
        SELECT c.*, u.username, u.avatar_url
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.target_type = ? AND c.target_id = ? AND c.parent_id = 0 AND c.status = 1
        ORDER BY {order_sql}
        LIMIT ? OFFSET ?
        """,
        (target_type, target_id, page_size, offset)
    )

    # 获取总数
    count_result = execute_query(
        "SELECT COUNT(*) as count FROM comments WHERE target_type = ? AND target_id = ? AND parent_id = 0 AND status = 1",
        (target_type, target_id)
    )
    total = count_result[0]["count"] if count_result else 0

    # 格式化评论数据
    comment_list = [format_comment(c, user_id) for c in (comments or [])]

    return CommentListResponse(
        success=True,
        data={
            "list": comment_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(comment_list) < total
        },
        message="获取成功"
    )


@router.get("/replies", response_model=CommentListResponse)
async def get_replies(
    parent_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取评论的回复列表

    Args:
        parent_id: 父评论 ID
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        回复列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 验证父评论是否存在
    parent_comment = get_comment_by_id(parent_id)
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4003, "message": "父评论不存在"}
        )

    # 计算分页
    offset = (page - 1) * page_size

    # 查询回复列表
    replies = execute_query(
        """
        SELECT c.*, u.username, u.avatar_url
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.parent_id = ? AND c.status = 1
        ORDER BY c.created_at ASC
        LIMIT ? OFFSET ?
        """,
        (parent_id, page_size, offset)
    )

    # 获取总数
    count_result = execute_query(
        "SELECT COUNT(*) as count FROM comments WHERE parent_id = ? AND status = 1",
        (parent_id,)
    )
    total = count_result[0]["count"] if count_result else 0

    # 格式化评论数据
    reply_list = [format_comment(r, user_id) for r in (replies or [])]

    return CommentListResponse(
        success=True,
        data={
            "list": reply_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(reply_list) < total
        },
        message="获取成功"
    )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    request: CommentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    编辑评论

    Args:
        comment_id: 评论 ID
        request: 更新请求
        current_user: 当前用户

    Returns:
        更新结果

    Raises:
        HTTPException: 更新失败或无权限
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 获取评论
    comment = get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4003, "message": "评论不存在"}
        )

    # 检查权限
    if comment["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": 4005, "message": "无权限编辑他人的评论"}
        )

    try:
        # 更新评论
        execute_update(
            "UPDATE comments SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE comment_id = ?",
            (request.content, comment_id)
        )

        # 获取更新后的评论
        updated_comment = get_comment_by_id(comment_id)

        return CommentResponse(
            success=True,
            message="编辑成功",
            data=format_comment(updated_comment, user_id)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5002, "message": f"编辑失败：{str(e)}"}
        )


@router.delete("/{comment_id}", response_model=CommentResponse)
async def delete_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    删除评论（软删除，设置 status=0）

    Args:
        comment_id: 评论 ID
        current_user: 当前用户

    Returns:
        删除结果

    Raises:
        HTTPException: 删除失败或无权限
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 获取评论
    comment = get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4003, "message": "评论不存在"}
        )

    # 检查权限（只有评论作者可以删除）
    if comment["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": 4005, "message": "无权限删除他人的评论"}
        )

    try:
        # 获取评论的回复数
        reply_count = get_reply_count(comment_id)

        # 软删除评论
        execute_update(
            "UPDATE comments SET status = 0 WHERE comment_id = ?",
            (comment_id,)
        )

        # 更新目标评论计数
        update_target_comment_count(comment["target_type"], comment["target_id"], -1)

        return CommentResponse(
            success=True,
            message="删除成功",
            data={"comment_id": comment_id, "reply_count": reply_count}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5003, "message": f"删除失败：{str(e)}"}
        )


@router.post("/{comment_id}/like", response_model=CommentResponse)
async def like_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    点赞评论

    Args:
        comment_id: 评论 ID
        current_user: 当前用户

    Returns:
        点赞结果

    Raises:
        HTTPException: 点赞失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 获取评论
    comment = get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4003, "message": "评论不存在"}
        )

    # 检查是否已点赞
    if check_user_liked(user_id, comment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4006, "message": "您已点赞"}
        )

    try:
        # 插入点赞记录
        execute_update(
            "INSERT INTO likes (user_id, target_type, target_id) VALUES (?, 'comment', ?)",
            (user_id, comment_id)
        )

        # 更新评论点赞数
        execute_update(
            "UPDATE comments SET like_count = like_count + 1 WHERE comment_id = ?",
            (comment_id,)
        )

        # 创建通知
        if comment["user_id"] != user_id:
            create_notification(
                user_id=comment["user_id"],
                sender_id=user_id,
                notification_type="like",
                target_type="comment",
                target_id=comment_id,
                content="点赞了您的评论"
            )

        # 获取更新后的评论
        updated_comment = get_comment_by_id(comment_id)

        return CommentResponse(
            success=True,
            message="点赞成功",
            data=format_comment(updated_comment, user_id)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5004, "message": f"点赞失败：{str(e)}"}
        )


@router.delete("/{comment_id}/like", response_model=CommentResponse)
async def unlike_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    取消点赞评论

    Args:
        comment_id: 评论 ID
        current_user: 当前用户

    Returns:
        取消点赞结果

    Raises:
        HTTPException: 取消失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 获取评论
    comment = get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4003, "message": "评论不存在"}
        )

    # 检查是否已点赞
    if not check_user_liked(user_id, comment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4007, "message": "您尚未点赞"}
        )

    try:
        # 删除点赞记录
        execute_update(
            "DELETE FROM likes WHERE user_id = ? AND target_type = 'comment' AND target_id = ?",
            (user_id, comment_id)
        )

        # 更新评论点赞数
        execute_update(
            "UPDATE comments SET like_count = GREATEST(0, like_count - 1) WHERE comment_id = ?",
            (comment_id,)
        )

        # 获取更新后的评论
        updated_comment = get_comment_by_id(comment_id)

        return CommentResponse(
            success=True,
            message="取消成功",
            data=format_comment(updated_comment, user_id)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5005, "message": f"取消失败：{str(e)}"}
        )


@router.get("/{comment_id}")
async def get_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取单条评论详情

    Args:
        comment_id: 评论 ID
        current_user: 当前用户

    Returns:
        评论详情
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    comment = get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4003, "message": "评论不存在"}
        )

    return {
        "success": True,
        "data": format_comment(comment, user_id),
        "message": "获取成功"
    }


@router.get("/my/list", response_model=CommentListResponse)
async def get_my_comments(
    target_type: Optional[str] = None,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的评论列表

    Args:
        target_type: 目标类型（可选）
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        我的评论列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 计算分页
    offset = (page - 1) * page_size

    # 构建查询
    if target_type:
        if not validate_target_type(target_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error_code": 4001, "message": "无效的目标类型"}
            )
        comments = execute_query(
            """
            SELECT c.*, u.username, u.avatar_url
            FROM comments c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.user_id = ? AND c.target_type = ? AND c.status = 1
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, target_type, page_size, offset)
        )
        count_result = execute_query(
            "SELECT COUNT(*) as count FROM comments WHERE user_id = ? AND target_type = ? AND status = 1",
            (user_id, target_type)
        )
    else:
        comments = execute_query(
            """
            SELECT c.*, u.username, u.avatar_url
            FROM comments c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.user_id = ? AND c.status = 1
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, page_size, offset)
        )
        count_result = execute_query(
            "SELECT COUNT(*) as count FROM comments WHERE user_id = ? AND status = 1",
            (user_id,)
        )

    total = count_result[0]["count"] if count_result else 0
    comment_list = [format_comment(c, user_id) for c in (comments or [])]

    return CommentListResponse(
        success=True,
        data={
            "list": comment_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(comment_list) < total
        },
        message="获取成功"
    )
