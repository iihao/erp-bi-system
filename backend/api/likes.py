"""
点赞功能 API
提供点赞、取消点赞、获取点赞状态和计数功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from utils.database import execute_query, execute_update
from api.auth import get_current_user

router = APIRouter(prefix="/api/likes", tags=["点赞"])


# ===========================================
# 请求/响应模型
# ===========================================

class LikeRequest(BaseModel):
    """点赞请求"""
    target_type: str = Field(..., description="目标类型：post-帖子，comment-评论，report-报表")
    target_id: int = Field(..., description="目标 ID")


class LikeResponse(BaseModel):
    """点赞响应"""
    success: bool
    message: str
    data: dict


class LikeCountResponse(BaseModel):
    """点赞数量响应"""
    target_type: str
    target_id: int
    count: int
    user_liked: bool


# ===========================================
# 辅助函数
# ===========================================

def validate_target_type(target_type: str) -> bool:
    """验证目标类型"""
    return target_type in ["post", "comment", "report"]


def get_target_like_count(target_type: str, target_id: int) -> int:
    """获取目标的点赞数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM likes WHERE target_type = ? AND target_id = ?",
        (target_type, target_id)
    )
    return result[0]["count"] if result else 0


def check_user_liked(user_id: int, target_type: str, target_id: int) -> bool:
    """检查用户是否已点赞"""
    result = execute_query(
        "SELECT like_id FROM likes WHERE user_id = ? AND target_type = ? AND target_id = ?",
        (user_id, target_type, target_id)
    )
    return bool(result)


def update_target_like_count(target_type: str, target_id: int, delta: int):
    """更新目标的点赞计数"""
    if target_type == "post":
        execute_update(
            "UPDATE posts SET like_count = GREATEST(0, like_count + ?) WHERE post_id = ?",
            (delta, target_id)
        )
    elif target_type == "comment":
        execute_update(
            "UPDATE comments SET like_count = GREATEST(0, like_count + ?) WHERE comment_id = ?",
            (delta, target_id)
        )
    elif target_type == "report":
        execute_update(
            "UPDATE report_configs SET like_count = GREATEST(0, like_count + ?) WHERE report_id = ?",
            (delta, target_id)
        )


def create_notification(user_id: int, sender_id: int, notification_type: str,
                       target_type: Optional[str], target_id: Optional[int], content: str):
    """创建通知"""
    if target_type and target_id:
        execute_update(
            """INSERT INTO notifications (user_id, sender_id, notification_type, target_type, target_id, content)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, sender_id, notification_type, target_type, target_id, content)
        )
    else:
        execute_update(
            """INSERT INTO notifications (user_id, sender_id, notification_type, content)
               VALUES (?, ?, ?, ?)""",
            (user_id, sender_id, notification_type, content)
        )


# ===========================================
# API 端点
# ===========================================

@router.post("", response_model=LikeResponse)
async def like(
    request: LikeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    点赞目标内容

    Args:
        request: 点赞请求
        current_user: 当前用户

    Returns:
        点赞结果

    Raises:
        HTTPException: 点赞失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 验证目标类型
    if not validate_target_type(request.target_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "无效的目标类型"}
        )

    # 检查是否已点赞
    if check_user_liked(user_id, request.target_type, request.target_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4002, "message": "您已点赞"}
        )

    # 开始事务（点赞 + 更新计数）
    try:
        # 插入点赞记录
        execute_update(
            "INSERT INTO likes (user_id, target_type, target_id) VALUES (?, ?, ?)",
            (user_id, request.target_type, request.target_id)
        )

        # 更新目标点赞计数
        update_target_like_count(request.target_type, request.target_id, 1)

        # 如果是点赞帖子，创建通知给作者
        if request.target_type == "post":
            post = execute_query("SELECT user_id FROM posts WHERE post_id = ?", (request.target_id,))
            if post and post[0]["user_id"] != user_id:
                create_notification(
                    user_id=post[0]["user_id"],
                    sender_id=user_id,
                    notification_type="like",
                    target_type="post",
                    target_id=request.target_id,
                    content="点赞了您的帖子"
                )

        return LikeResponse(
            success=True,
            message="点赞成功",
            data={"count": get_target_like_count(request.target_type, request.target_id)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"点赞失败：{str(e)}"}
        )


@router.delete("", response_model=LikeResponse)
async def unlike(
    target_type: str,
    target_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    取消点赞

    Args:
        target_type: 目标类型
        target_id: 目标 ID
        current_user: 当前用户

    Returns:
        取消点赞结果

    Raises:
        HTTPException: 取消点赞失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 验证目标类型
    if not validate_target_type(target_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "无效的目标类型"}
        )

    # 检查是否已点赞
    if not check_user_liked(user_id, target_type, target_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4003, "message": "您尚未点赞"}
        )

    try:
        # 删除点赞记录
        execute_update(
            "DELETE FROM likes WHERE user_id = ? AND target_type = ? AND target_id = ?",
            (user_id, target_type, target_id)
        )

        # 更新目标点赞计数
        update_target_like_count(target_type, target_id, -1)

        return LikeResponse(
            success=True,
            message="取消成功",
            data={"count": get_target_like_count(target_type, target_id)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5002, "message": f"取消点赞失败：{str(e)}"}
        )


@router.get("/status", response_model=LikeCountResponse)
async def get_like_status(
    target_type: str,
    target_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取点赞状态（总数 + 用户是否已点赞）

    Args:
        target_type: 目标类型
        target_id: 目标 ID
        current_user: 当前用户

    Returns:
        点赞状态信息
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    count = get_target_like_count(target_type, target_id)
    user_liked = check_user_liked(user_id, target_type, target_id)

    return {
        "target_type": target_type,
        "target_id": target_id,
        "count": count,
        "user_liked": user_liked
    }


@router.get("/count")
async def get_like_count(
    target_type: str,
    target_id: int
):
    """
    获取点赞数量（无需认证）

    Args:
        target_type: 目标类型
        target_id: 目标 ID

    Returns:
        点赞数量
    """
    count = get_target_like_count(target_type, target_id)
    return {
        "success": True,
        "data": {
            "target_type": target_type,
            "target_id": target_id,
            "count": count
        }
    }


@router.get("/list")
async def get_liker_list(
    target_type: str,
    target_id: int,
    limit: int = 20,
    offset: int = 0
):
    """
    获取点赞用户列表

    Args:
        target_type: 目标类型
        target_id: 目标 ID
        limit: 数量限制
        offset: 偏移量

    Returns:
        点赞用户列表
    """
    # 验证目标类型
    if not validate_target_type(target_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "无效的目标类型"}
        )

    # 查询点赞用户
    likers = execute_query(
        """
        SELECT u.user_id, u.username, u.avatar_url, l.created_at
        FROM likes l
        JOIN users u ON l.user_id = u.user_id
        LEFT JOIN user_profiles up ON u.user_id = up.user_id
        WHERE l.target_type = ? AND l.target_id = ?
        ORDER BY l.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (target_type, target_id, limit, offset)
    )

    # 获取总数
    count_result = execute_query(
        "SELECT COUNT(*) as count FROM likes WHERE target_type = ? AND target_id = ?",
        (target_type, target_id)
    )

    return {
        "success": True,
        "data": {
            "list": likers or [],
            "total": count_result[0]["count"] if count_result else 0
        },
        "message": "获取成功"
    }


@router.get("/my")
async def get_my_likes(
    target_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的点赞列表

    Args:
        target_type: 目标类型（可选，不传则返回所有类型）
        limit: 数量限制
        offset: 偏移量
        current_user: 当前用户

    Returns:
        我的点赞列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 构建查询
    if target_type:
        if not validate_target_type(target_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error_code": 4001, "message": "无效的目标类型"}
            )
        likes = execute_query(
            """
            SELECT l.target_type, l.target_id, l.created_at
            FROM likes l
            WHERE l.user_id = ? AND l.target_type = ?
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, target_type, limit, offset)
        )
        count_result = execute_query(
            "SELECT COUNT(*) as count FROM likes WHERE user_id = ? AND target_type = ?",
            (user_id, target_type)
        )
    else:
        likes = execute_query(
            """
            SELECT l.target_type, l.target_id, l.created_at
            FROM likes l
            WHERE l.user_id = ?
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )
        count_result = execute_query(
            "SELECT COUNT(*) as count FROM likes WHERE user_id = ?",
            (user_id,)
        )

    return {
        "success": True,
        "data": {
            "list": likes or [],
            "total": count_result[0]["count"] if count_result else 0
        },
        "message": "获取成功"
    }
