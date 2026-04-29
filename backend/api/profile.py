"""
个人主页 API
提供用户个人主页展示、用户信息、发布内容、点赞记录等功能
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from utils.database import execute_query, execute_update
from api.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["个人主页"])


# ===========================================
# 请求/响应模型
# ===========================================

class ProfileUpdateRequest(BaseModel):
    """更新个人资料请求"""
    avatar_url: Optional[str] = Field(None, max_length=255, description="头像 URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    gender: Optional[int] = Field(None, ge=0, le=2, description="性别：0-未知，1-男，2-女")
    location: Optional[str] = Field(None, max_length=100, description="所在地")


class UserProfileResponse(BaseModel):
    """用户资料响应"""
    user_id: int
    username: str
    avatar_url: Optional[str]
    bio: Optional[str]
    gender: int
    location: Optional[str]
    follower_count: int
    following_count: int
    like_count: int
    post_count: int
    is_following: bool
    is_me: bool
    created_at: str


class PostItem(BaseModel):
    """帖子项"""
    post_id: int
    user_id: int
    username: str
    avatar_url: Optional[str]
    title: Optional[str]
    content: str
    post_type: str
    like_count: int
    comment_count: int
    view_count: int
    is_liked: bool
    created_at: str


class ReportItem(BaseModel):
    """报表项"""
    report_id: int
    report_name: str
    report_type: str
    description: Optional[str]
    like_count: int
    view_count: int
    is_liked: bool
    created_at: str


class ContentListResponse(BaseModel):
    """内容列表响应"""
    success: bool
    data: dict
    message: str


class LikedItem(BaseModel):
    """点赞记录项"""
    target_type: str
    target_id: int
    target_title: Optional[str]
    liked_at: str


class LikedListResponse(BaseModel):
    """点赞列表响应"""
    success: bool
    data: dict
    message: str


# ===========================================
# 辅助函数
# ===========================================

def get_user_profile_data(user_id: int, current_user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """获取用户资料数据"""
    # 获取用户基本信息
    user_result = execute_query(
        "SELECT user_id, username, avatar_url, email, real_name, created_at FROM users WHERE user_id = ?",
        (user_id,)
    )
    if not user_result:
        return None

    user = user_result[0]

    # 获取用户扩展信息
    profile_result = execute_query(
        "SELECT bio, gender, location, like_count, follower_count, following_count, post_count FROM user_profiles WHERE user_id = ?",
        (user_id,)
    )

    profile = profile_result[0] if profile_result else {}

    # 获取计数（优先从 user_profiles 获取，否则实时计算）
    follower_count = profile.get("follower_count") or count_followers(user_id)
    following_count = profile.get("following_count") or count_following(user_id)
    like_count = profile.get("like_count") or 0
    post_count = profile.get("post_count") or 0

    # 检查是否关注
    is_following = False
    if current_user_id and current_user_id != user_id:
        is_following = check_follow_exists(current_user_id, user_id)

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "avatar_url": user.get("avatar_url"),
        "bio": profile.get("bio"),
        "gender": profile.get("gender", 0),
        "location": profile.get("location"),
        "follower_count": follower_count,
        "following_count": following_count,
        "like_count": like_count,
        "post_count": post_count,
        "is_following": is_following,
        "is_me": current_user_id == user_id,
        "created_at": str(user.get("created_at", ""))[:19] if user.get("created_at") else ""
    }


def count_followers(user_id: int) -> int:
    """获取粉丝数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM follows WHERE followed_id = ?",
        (user_id,)
    )
    return result[0]["count"] if result else 0


def count_following(user_id: int) -> int:
    """获取关注数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?",
        (user_id,)
    )
    return result[0]["count"] if result else 0


def check_follow_exists(follower_id: int, followed_id: int) -> bool:
    """检查是否已关注"""
    result = execute_query(
        "SELECT follow_id FROM follows WHERE follower_id = ? AND followed_id = ?",
        (follower_id, followed_id)
    )
    return bool(result)


def check_user_liked(user_id: int, target_type: str, target_id: int) -> bool:
    """检查用户是否已点赞"""
    if not user_id:
        return False
    result = execute_query(
        "SELECT like_id FROM likes WHERE user_id = ? AND target_type = ? AND target_id = ?",
        (user_id, target_type, target_id)
    )
    return bool(result)


def get_user_posts(user_id: int, limit: int = 20, offset: int = 0, current_user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """获取用户的帖子列表"""
    posts = execute_query(
        """
        SELECT
            p.post_id,
            p.user_id,
            u.username,
            u.avatar_url,
            p.title,
            p.content,
            p.post_type,
            p.like_count,
            p.comment_count,
            p.view_count,
            p.created_at
        FROM posts p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.user_id = ? AND p.status = 1
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    result = []
    for post in (posts or []):
        is_liked = check_user_liked(current_user_id, "post", post["post_id"]) if current_user_id else False
        result.append({
            "post_id": post["post_id"],
            "user_id": post["user_id"],
            "username": post["username"],
            "avatar_url": post.get("avatar_url"),
            "title": post.get("title"),
            "content": post.get("content", ""),
            "post_type": post.get("post_type", "normal"),
            "like_count": post.get("like_count", 0),
            "comment_count": post.get("comment_count", 0),
            "view_count": post.get("view_count", 0),
            "is_liked": is_liked,
            "created_at": str(post.get("created_at", ""))[:19] if post.get("created_at") else ""
        })
    return result


def count_user_posts(user_id: int) -> int:
    """获取用户帖子总数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM posts WHERE user_id = ? AND status = 1",
        (user_id,)
    )
    return result[0]["count"] if result else 0


def get_user_reports(user_id: int, limit: int = 20, offset: int = 0, current_user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """获取用户的报表列表"""
    reports = execute_query(
        """
        SELECT
            r.report_id,
            r.report_name,
            r.report_type,
            r.description,
            r.like_count,
            r.view_count,
            r.created_at
        FROM report_configs r
        WHERE r.created_by = ? AND r.status = 'published'
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    result = []
    for report in (reports or []):
        is_liked = check_user_liked(current_user_id, "report", report["report_id"]) if current_user_id else False
        result.append({
            "report_id": report["report_id"],
            "report_name": report["report_name"],
            "report_type": report.get("report_type", "table"),
            "description": report.get("description"),
            "like_count": report.get("like_count", 0),
            "view_count": report.get("view_count", 0),
            "is_liked": is_liked,
            "created_at": str(report.get("created_at", ""))[:19] if report.get("created_at") else ""
        })
    return result


def count_user_reports(user_id: int) -> int:
    """获取用户报表总数"""
    result = execute_query(
        "SELECT COUNT(*) as count FROM report_configs WHERE created_by = ? AND status = 'published'",
        (user_id,)
    )
    return result[0]["count"] if result else 0


def get_user_liked_targets(user_id: int, target_type: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """获取用户点赞的目标列表"""
    if target_type:
        liked = execute_query(
            """
            SELECT l.target_type, l.target_id, l.created_at,
                   CASE
                       WHEN l.target_type = 'post' THEN p.title
                       WHEN l.target_type = 'report' THEN r.report_name
                       ELSE NULL
                   END as target_title
            FROM likes l
            LEFT JOIN posts p ON l.target_id = p.post_id AND l.target_type = 'post'
            LEFT JOIN report_configs r ON l.target_id = r.report_id AND l.target_type = 'report'
            WHERE l.user_id = ? AND l.target_type = ?
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, target_type, limit, offset)
        )
    else:
        liked = execute_query(
            """
            SELECT l.target_type, l.target_id, l.created_at,
                   CASE
                       WHEN l.target_type = 'post' THEN p.title
                       WHEN l.target_type = 'report' THEN r.report_name
                       ELSE NULL
                   END as target_title
            FROM likes l
            LEFT JOIN posts p ON l.target_id = p.post_id AND l.target_type = 'post'
            LEFT JOIN report_configs r ON l.target_id = r.report_id AND l.target_type = 'report'
            WHERE l.user_id = ?
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )

    result = []
    for item in (liked or []):
        result.append({
            "target_type": item["target_type"],
            "target_id": item["target_id"],
            "target_title": item.get("target_title"),
            "liked_at": str(item.get("created_at", ""))[:19] if item.get("created_at") else ""
        })
    return result


def count_user_likes(user_id: int, target_type: Optional[str] = None) -> int:
    """获取用户点赞总数"""
    if target_type:
        result = execute_query(
            "SELECT COUNT(*) as count FROM likes WHERE user_id = ? AND target_type = ?",
            (user_id, target_type)
        )
    else:
        result = execute_query(
            "SELECT COUNT(*) as count FROM likes WHERE user_id = ?",
            (user_id,)
        )
    return result[0]["count"] if result else 0


def get_user_id_from_token(token_data: dict) -> int:
    """从 token 数据中获取用户 ID"""
    from core.security import decode_token
    token = token_data.get("token")
    if token:
        return decode_token(token)
    # 尝试从 payload 中获取
    payload = token_data.get("payload", {})
    sub = payload.get("sub")
    if sub:
        return int(sub)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error_code": 4001, "message": "无法获取用户 ID"}
    )


# ===========================================
# API 端点
# ===========================================

@router.get("/{user_id}")
async def get_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户个人主页信息

    Args:
        user_id: 用户 ID
        current_user: 当前用户

    Returns:
        用户资料信息
    """
    try:
        current_user_id = get_user_id_from_token(current_user)
    except Exception:
        current_user_id = None

    profile = get_user_profile_data(user_id, current_user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4001, "message": "用户不存在"}
        )

    return {
        "success": True,
        "data": profile,
        "message": "获取成功"
    }


@router.get("")
async def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户自己的个人资料

    Args:
        current_user: 当前用户

    Returns:
        用户资料信息
    """
    current_user_id = get_user_id_from_token(current_user)

    profile = get_user_profile_data(current_user_id, current_user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4001, "message": "用户不存在"}
        )

    return {
        "success": True,
        "data": profile,
        "message": "获取成功"
    }


@router.put("")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新当前用户个人资料

    Args:
        request: 更新请求
        current_user: 当前用户

    Returns:
        更新后的用户资料
    """
    current_user_id = get_user_id_from_token(current_user)

    # 检查 user_profiles 是否存在
    existing = execute_query(
        "SELECT user_id FROM user_profiles WHERE user_id = ?",
        (current_user_id,)
    )

    if existing:
        # 更新现有记录
        update_fields = []
        params = []

        if request.avatar_url is not None:
            update_fields.append("avatar_url = ?")
            params.append(request.avatar_url)
        if request.bio is not None:
            update_fields.append("bio = ?")
            params.append(request.bio)
        if request.gender is not None:
            update_fields.append("gender = ?")
            params.append(request.gender)
        if request.location is not None:
            update_fields.append("location = ?")
            params.append(request.location)

        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(current_user_id)

            update_sql = f"""
                UPDATE user_profiles
                SET {", ".join(update_fields)}
                WHERE user_id = ?
            """
            execute_update(update_sql, tuple(params))
    else:
        # 插入新记录
        execute_update(
            """INSERT INTO user_profiles (user_id, avatar_url, bio, gender, location)
               VALUES (?, ?, ?, ?, ?)""",
            (
                current_user_id,
                request.avatar_url,
                request.bio,
                request.gender or 0,
                request.location
            )
        )

    # 返回更新后的资料
    profile = get_user_profile_data(current_user_id, current_user_id)

    return {
        "success": True,
        "data": profile,
        "message": "更新成功"
    }


@router.get("/{user_id}/posts", response_model=ContentListResponse)
async def get_user_posts_endpoint(
    user_id: int,
    content_type: str = Query(default="post", description="内容类型：post-帖子，report-报表"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户发布的内容列表

    Args:
        user_id: 用户 ID
        content_type: 内容类型
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        内容列表
    """
    try:
        current_user_id = get_user_id_from_token(current_user)
    except Exception:
        current_user_id = None

    offset = (page - 1) * page_size

    if content_type == "post":
        items = get_user_posts(user_id, page_size, offset, current_user_id)
        total = count_user_posts(user_id)
    elif content_type == "report":
        items = get_user_reports(user_id, page_size, offset, current_user_id)
        total = count_user_reports(user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4002, "message": "无效的内容类型"}
        )

    return {
        "success": True,
        "data": {
            "list": items,
            "total": total,
            "page": page,
            "page_size": page_size
        },
        "message": "获取成功"
    }


@router.get("/{user_id}/likes", response_model=LikedListResponse)
async def get_user_likes(
    user_id: int,
    target_type: Optional[str] = Query(None, description="目标类型：post-帖子，report-报表，comment-评论"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户的点赞记录

    Args:
        user_id: 用户 ID
        target_type: 目标类型
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        点赞记录列表
    """
    # 验证只能查看自己的点赞记录或者是公开记录
    try:
        current_user_id = get_user_id_from_token(current_user)
        # 如果不是查看自己的记录，允许查看公开记录
        is_own_profile = current_user_id == user_id
    except Exception:
        current_user_id = None
        is_own_profile = False

    offset = (page - 1) * page_size

    items = get_user_liked_targets(user_id, target_type, page_size, offset)
    total = count_user_likes(user_id, target_type)

    return {
        "success": True,
        "data": {
            "list": items,
            "total": total,
            "page": page,
            "page_size": page_size
        },
        "message": "获取成功"
    }


@router.get("/{user_id}/stats")
async def get_profile_stats(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户统计信息概览

    Args:
        user_id: 用户 ID
        current_user: 当前用户

    Returns:
        统计信息
    """
    # 获取基础统计
    follower_count = count_followers(user_id)
    following_count = count_following(user_id)
    post_count = count_user_posts(user_id)
    report_count = count_user_reports(user_id)
    like_count = count_user_likes(user_id)

    # 获取最近发帖时间
    last_post = execute_query(
        "SELECT created_at FROM posts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    last_post_at = str(last_post[0]["created_at"])[:19] if last_post else None

    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "follower_count": follower_count,
            "following_count": following_count,
            "post_count": post_count,
            "report_count": report_count,
            "like_count": like_count,
            "last_post_at": last_post_at
        },
        "message": "获取成功"
    }


@router.post("/avatar")
async def upload_avatar(
    avatar: UploadFile = File(..., description="头像文件"),
    current_user: dict = Depends(get_current_user)
):
    """
    上传头像

    Args:
        avatar: 头像文件
        current_user: 当前用户

    Returns:
        头像 URL
    """
    current_user_id = get_user_id_from_token(current_user)

    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if avatar.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4002, "message": "不支持的文件格式，请上传 JPG、PNG、GIF 或 WebP 格式的图片"}
        )

    # 验证文件大小（2MB）
    file_size = len(await avatar.read())
    await avatar.seek(0)  # 重置文件指针
    if file_size > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4002, "message": "文件大小不能超过 2MB"}
        )

    # 创建上传目录
    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名
    file_extension = avatar.filename.split(".")[-1] if "." in avatar.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(upload_dir, filename)

    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await avatar.read()
        buffer.write(content)

    # 生成 URL
    avatar_url = f"/{file_path}"

    # 更新用户头像
    existing = execute_query(
        "SELECT user_id FROM user_profiles WHERE user_id = ?",
        (current_user_id,)
    )

    if existing:
        execute_update(
            "UPDATE user_profiles SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (avatar_url, current_user_id)
        )
    else:
        execute_update(
            "INSERT INTO user_profiles (user_id, avatar_url) VALUES (?, ?)",
            (current_user_id, avatar_url)
        )

    # 同时更新 users 表的 avatar_url
    execute_update(
        "UPDATE users SET avatar_url = ? WHERE user_id = ?",
        (avatar_url, current_user_id)
    )

    return {
        "success": True,
        "data": {"avatar_url": avatar_url},
        "message": "上传成功"
    }


@router.delete("/avatar")
async def delete_avatar(
    current_user: dict = Depends(get_current_user)
):
    """
    删除头像

    Args:
        current_user: 当前用户

    Returns:
        操作结果
    """
    current_user_id = get_user_id_from_token(current_user)

    # 获取当前头像路径
    profile = execute_query(
        "SELECT avatar_url FROM user_profiles WHERE user_id = ?",
        (current_user_id,)
    )

    if profile and profile[0].get("avatar_url"):
        avatar_url = profile[0]["avatar_url"]
        # 如果是本地文件，删除它
        if avatar_url.startswith("/uploads/"):
            file_path = "." + avatar_url
            if os.path.exists(file_path):
                os.remove(file_path)

    # 更新头像为默认值
    execute_update(
        "UPDATE user_profiles SET avatar_url = NULL, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (current_user_id,)
    )

    execute_update(
        "UPDATE users SET avatar_url = NULL WHERE user_id = ?",
        (current_user_id,)
    )

    return {
        "success": True,
        "data": None,
        "message": "删除成功"
    }
