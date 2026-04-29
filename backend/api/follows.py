"""
关注功能 API
提供关注、取消关注、获取粉丝列表和关注列表功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from utils.database import execute_query, execute_update
from api.auth import get_current_user

router = APIRouter(prefix="/api/follows", tags=["关注"])


# ===========================================
# 请求/响应模型
# ===========================================

class FollowRequest(BaseModel):
    """关注请求"""
    followed_id: int = Field(..., description="被关注用户 ID")


class FollowResponse(BaseModel):
    """关注响应"""
    success: bool
    message: str
    data: dict


class FollowUserItem(BaseModel):
    """关注用户项"""
    user_id: int
    username: str
    avatar_url: Optional[str]
    bio: Optional[str]
    follower_count: int
    following_count: int
    is_following: bool
    created_at: str


class FollowListResponse(BaseModel):
    """关注列表响应"""
    success: bool
    data: dict
    message: str


# ===========================================
# 辅助函数
# ===========================================

def check_follow_exists(follower_id: int, followed_id: int) -> bool:
    """检查是否已关注"""
    result = execute_query(
        "SELECT follow_id FROM follows WHERE follower_id = ? AND followed_id = ?",
        (follower_id, followed_id)
    )
    return bool(result)


def get_follower_count(user_id: int) -> int:
    """获取用户的粉丝数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM follows WHERE followed_id = ?",
        (user_id,)
    )
    return result[0]["count"] if result else 0


def get_following_count(user_id: int) -> int:
    """获取用户的关注数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?",
        (user_id,)
    )
    return result[0]["count"] if result else 0


def update_user_profile_counts(user_id: int):
    """更新用户扩展表的计数"""
    follower_count = get_follower_count(user_id)
    following_count = get_following_count(user_id)

    # 检查 user_profiles 是否存在
    existing = execute_query(
        "SELECT user_id FROM user_profiles WHERE user_id = ?",
        (user_id,)
    )

    if existing:
        execute_update(
            "UPDATE user_profiles SET follower_count = ?, following_count = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (follower_count, following_count, user_id)
        )
    else:
        execute_update(
            "INSERT INTO user_profiles (user_id, follower_count, following_count) VALUES (?, ?, ?)",
            (user_id, follower_count, following_count)
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


def get_user_profile(user_id: int, current_user_id: Optional[int] = None) -> dict:
    """获取用户资料"""
    # 获取用户基本信息
    user_result = execute_query(
        "SELECT user_id, username, avatar_url FROM users WHERE user_id = ?",
        (user_id,)
    )
    if not user_result:
        return None

    user = user_result[0]

    # 获取用户扩展信息
    profile_result = execute_query(
        "SELECT bio, follower_count, following_count FROM user_profiles WHERE user_id = ?",
        (user_id,)
    )

    profile = profile_result[0] if profile_result else {}

    # 获取计数
    follower_count = get_follower_count(user_id)
    following_count = get_following_count(user_id)

    # 检查当前用户是否关注该用户
    is_following = False
    if current_user_id:
        is_following = check_follow_exists(current_user_id, user_id)

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "avatar_url": user.get("avatar_url"),
        "bio": profile.get("bio"),
        "follower_count": follower_count,
        "following_count": following_count,
        "is_following": is_following
    }


# ===========================================
# API 端点
# ===========================================

@router.post("", response_model=FollowResponse)
async def follow(
    request: FollowRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    关注用户

    Args:
        request: 关注请求
        current_user: 当前用户

    Returns:
        关注结果

    Raises:
        HTTPException: 关注失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 不能关注自己
    if user_id == request.followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": "不能关注自己"}
        )

    # 检查被关注用户是否存在
    user_exists = execute_query(
        "SELECT user_id FROM users WHERE user_id = ?",
        (request.followed_id,)
    )
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "用户不存在"}
        )

    # 检查是否已关注
    if check_follow_exists(user_id, request.followed_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4003, "message": "已关注该用户"}
        )

    try:
        # 插入关注记录
        execute_update(
            "INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (user_id, request.followed_id)
        )

        # 更新计数
        update_user_profile_counts(user_id)
        update_user_profile_counts(request.followed_id)

        # 创建通知
        create_notification(
            user_id=request.followed_id,
            sender_id=user_id,
            notification_type="follow",
            target_type=None,
            target_id=None,
            content="关注了您"
        )

        return FollowResponse(
            success=True,
            message="关注成功",
            data={
                "follower_count": get_follower_count(request.followed_id),
                "following_count": get_following_count(user_id)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"关注失败：{str(e)}"}
        )


@router.delete("", response_model=FollowResponse)
async def unfollow(
    followed_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    取消关注

    Args:
        followed_id: 被关注用户 ID
        current_user: 当前用户

    Returns:
        取消关注结果

    Raises:
        HTTPException: 取消关注失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 检查被关注用户是否存在
    user_exists = execute_query(
        "SELECT user_id FROM users WHERE user_id = ?",
        (followed_id,)
    )
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "用户不存在"}
        )

    # 检查是否已关注
    if not check_follow_exists(user_id, followed_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4004, "message": "尚未关注该用户"}
        )

    try:
        # 删除关注记录
        execute_update(
            "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
            (user_id, followed_id)
        )

        # 更新计数
        update_user_profile_counts(user_id)
        update_user_profile_counts(followed_id)

        return FollowResponse(
            success=True,
            message="取消成功",
            data={
                "follower_count": get_follower_count(followed_id),
                "following_count": get_following_count(user_id)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5002, "message": f"取消关注失败：{str(e)}"}
        )


@router.get("/status")
async def get_follow_status(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取关注状态

    Args:
        user_id: 目标用户 ID
        current_user: 当前用户

    Returns:
        关注状态信息
    """
    from core.security import decode_token
    current_user_id = decode_token(current_user.get("token"))

    # 获取用户资料
    user_profile = get_user_profile(user_id, current_user_id)

    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "用户不存在"}
        )

    return {
        "success": True,
        "data": user_profile,
        "message": "获取成功"
    }


@router.get("/count")
async def get_follow_count(
    user_id: int
):
    """
    获取关注数量（无需认证）

    Args:
        user_id: 用户 ID

    Returns:
        关注数量
    """
    follower_count = get_follower_count(user_id)
    following_count = get_following_count(user_id)

    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "follower_count": follower_count,
            "following_count": following_count
        }
    }


@router.get("/followers", response_model=FollowListResponse)
async def get_followers(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100, description="数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户的粉丝列表

    Args:
        user_id: 用户 ID
        limit: 数量限制
        offset: 偏移量
        current_user: 当前用户

    Returns:
        粉丝列表
    """
    from core.security import decode_token
    current_user_id = decode_token(current_user.get("token"))

    # 查询粉丝列表
    followers = execute_query(
        """
        SELECT
            u.user_id,
            u.username,
            u.avatar_url,
            COALESCE(up.bio, '') as bio,
            f.created_at
        FROM follows f
        JOIN users u ON f.follower_id = u.user_id
        LEFT JOIN user_profiles up ON u.user_id = up.user_id
        WHERE f.followed_id = ?
        ORDER BY f.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    # 获取总数
    count_result = execute_query(
        "SELECT COUNT(*) as count FROM follows WHERE followed_id = ?",
        (user_id,)
    )
    total = count_result[0]["count"] if count_result else 0

    # 为每个粉丝添加计数和关注状态
    follower_list = []
    for follower in (followers or []):
        follower_count = get_follower_count(follower["user_id"])
        following_count = get_following_count(follower["user_id"])
        is_following = check_follow_exists(current_user_id, follower["user_id"])

        follower_list.append({
            "user_id": follower["user_id"],
            "username": follower["username"],
            "avatar_url": follower.get("avatar_url"),
            "bio": follower.get("bio"),
            "follower_count": follower_count,
            "following_count": following_count,
            "is_following": is_following,
            "created_at": str(follower.get("created_at", ""))[:19]
        })

    return {
        "success": True,
        "data": {
            "list": follower_list,
            "total": total
        },
        "message": "获取成功"
    }


@router.get("/following", response_model=FollowListResponse)
async def get_following(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100, description="数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户的关注列表

    Args:
        user_id: 用户 ID
        limit: 数量限制
        offset: 偏移量
        current_user: 当前用户

    Returns:
        关注列表
    """
    from core.security import decode_token
    current_user_id = decode_token(current_user.get("token"))

    # 查询关注列表
    following = execute_query(
        """
        SELECT
            u.user_id,
            u.username,
            u.avatar_url,
            COALESCE(up.bio, '') as bio,
            f.created_at
        FROM follows f
        JOIN users u ON f.followed_id = u.user_id
        LEFT JOIN user_profiles up ON u.user_id = up.user_id
        WHERE f.follower_id = ?
        ORDER BY f.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    # 获取总数
    count_result = execute_query(
        "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?",
        (user_id,)
    )
    total = count_result[0]["count"] if count_result else 0

    # 为每个关注对象添加计数和关注状态
    following_list = []
    for user in (following or []):
        follower_count = get_follower_count(user["user_id"])
        following_count = get_following_count(user["user_id"])
        is_following = check_follow_exists(current_user_id, user["user_id"])

        following_list.append({
            "user_id": user["user_id"],
            "username": user["username"],
            "avatar_url": user.get("avatar_url"),
            "bio": user.get("bio"),
            "follower_count": follower_count,
            "following_count": following_count,
            "is_following": is_following,
            "created_at": str(user.get("created_at", ""))[:19]
        })

    return {
        "success": True,
        "data": {
            "list": following_list,
            "total": total
        },
        "message": "获取成功"
    }


@router.get("/my")
async def get_my_follows(
    list_type: str = Query(default="following", description="列表类型：following-关注的人，followers-粉丝"),
    limit: int = Query(default=20, ge=1, le=100, description="数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的关注/粉丝列表

    Args:
        list_type: 列表类型 (following 或 followers)
        limit: 数量限制
        offset: 偏移量
        current_user: 当前用户

    Returns:
        我的关注/粉丝列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    if list_type == "following":
        # 获取我关注的人
        following = execute_query(
            """
            SELECT
                u.user_id,
                u.username,
                u.avatar_url,
                COALESCE(up.bio, '') as bio,
                f.created_at
            FROM follows f
            JOIN users u ON f.followed_id = u.user_id
            LEFT JOIN user_profiles up ON u.user_id = up.user_id
            WHERE f.follower_id = ?
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )

        count_result = execute_query(
            "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?",
            (user_id,)
        )

        following_list = []
        for user in (following or []):
            follower_count = get_follower_count(user["user_id"])
            following_count = get_following_count(user["user_id"])
            is_following = check_follow_exists(user_id, user["user_id"])

            following_list.append({
                "user_id": user["user_id"],
                "username": user["username"],
                "avatar_url": user.get("avatar_url"),
                "bio": user.get("bio"),
                "follower_count": follower_count,
                "following_count": following_count,
                "is_following": is_following,
                "created_at": str(user.get("created_at", ""))[:19]
            })

        return {
            "success": True,
            "data": {
                "list": following_list,
                "total": count_result[0]["count"] if count_result else 0
            },
            "message": "获取成功"
        }

    elif list_type == "followers":
        # 获取我的粉丝
        followers = execute_query(
            """
            SELECT
                u.user_id,
                u.username,
                u.avatar_url,
                COALESCE(up.bio, '') as bio,
                f.created_at
            FROM follows f
            JOIN users u ON f.follower_id = u.user_id
            LEFT JOIN user_profiles up ON u.user_id = up.user_id
            WHERE f.followed_id = ?
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )

        count_result = execute_query(
            "SELECT COUNT(*) as count FROM follows WHERE followed_id = ?",
            (user_id,)
        )

        follower_list = []
        for follower in (followers or []):
            follower_count = get_follower_count(follower["user_id"])
            following_count = get_following_count(follower["user_id"])
            is_following = check_follow_exists(user_id, follower["user_id"])

            follower_list.append({
                "user_id": follower["user_id"],
                "username": follower["username"],
                "avatar_url": follower.get("avatar_url"),
                "bio": follower.get("bio"),
                "follower_count": follower_count,
                "following_count": following_count,
                "is_following": is_following,
                "created_at": str(follower.get("created_at", ""))[:19]
            })

        return {
            "success": True,
            "data": {
                "list": follower_list,
                "total": count_result[0]["count"] if count_result else 0
            },
            "message": "获取成功"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4005, "message": "无效的列表类型"}
        )
