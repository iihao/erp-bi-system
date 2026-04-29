"""
树洞功能 API
提供匿名发布心事/吐槽、查看树洞列表、点赞评论等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from utils.database import execute_query, execute_update
from api.auth import get_current_user
import re

router = APIRouter(prefix="/api/treehole", tags=["树洞"])


# ===========================================
# 敏感词过滤配置
# ===========================================

# 内存缓存敏感词（启动时加载）
SENSITIVE_WORDS_CACHE = {
    "general": [],
    "ads": [],
    "politics": []
}


def load_sensitive_words():
    """加载敏感词到缓存"""
    global SENSITIVE_WORDS_CACHE
    result = execute_query(
        "SELECT word, category FROM sensitive_words WHERE is_active = 1"
    )
    SENSITIVE_WORDS_CACHE = {"general": [], "ads": [], "politics": [], "all": []}
    for row in (result or []):
        category = row.get("category", "general")
        word = row.get("word", "")
        if category not in SENSITIVE_WORDS_CACHE:
            SENSITIVE_WORDS_CACHE[category] = []
        SENSITIVE_WORDS_CACHE[category].append(word)
        SENSITIVE_WORDS_CACHE["all"].append(word)


def filter_sensitive_text(text: str) -> tuple:
    """
    过滤敏感词
    Returns:
        (is_valid, message, filtered_text)
    """
    if not SENSITIVE_WORDS_CACHE.get("all"):
        load_sensitive_words()

    filtered_text = text
    high_severity_words = []

    # 获取高严重程度的敏感词
    result = execute_query(
        "SELECT word FROM sensitive_words WHERE is_active = 1 AND severity = 3"
    )
    high_severity_words = [row["word"] for row in (result or [])]

    for word in high_severity_words:
        if word in text:
            return (False, f"内容包含不当言论：{word}", None)

    # 替换中低严重程度的敏感词
    for word in SENSITIVE_WORDS_CACHE.get("all", []):
        if word in filtered_text:
            filtered_text = filtered_text.replace(word, "*" * len(word))

    return (True, "通过过滤", filtered_text)


# ===========================================
# 请求/响应模型
# ===========================================

class TreeholeCreateRequest(BaseModel):
    """创建树洞请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="树洞内容")
    title: Optional[str] = Field(default=None, max_length=200, description="可选标题")

    @validator("content")
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()


class TreeholeUpdateRequest(BaseModel):
    """更新树洞请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="树洞内容")
    title: Optional[str] = Field(default=None, max_length=200, description="可选标题")


class TreeholeItem(BaseModel):
    """树洞项"""
    post_id: int
    content: str
    title: Optional[str]
    like_count: int
    comment_count: int
    view_count: int
    is_anonymous: bool
    created_at: str
    updated_at: str
    # 匿名显示字段
    display_username: str
    display_avatar: Optional[str]
    user_liked: bool


class TreeholeListResponse(BaseModel):
    """树洞列表响应"""
    success: bool
    data: dict
    message: str


class TreeholeResponse(BaseModel):
    """树洞操作响应"""
    success: bool
    message: str
    data: dict


# ===========================================
# 辅助函数
# ===========================================

def get_treehole_by_id(post_id: int) -> Optional[dict]:
    """根据 ID 获取树洞"""
    result = execute_query(
        """
        SELECT
            p.post_id, p.content, p.title, p.like_count, p.comment_count, p.view_count,
            p.is_anonymous, p.created_at, p.updated_at, p.status,
            CASE
                WHEN p.is_anonymous = 1 THEN '匿名树洞'
                ELSE u.username
            END AS display_username,
            CASE
                WHEN p.is_anonymous = 1 THEN NULL
                ELSE u.avatar_url
            END AS display_avatar
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.user_id
        WHERE p.post_id = ? AND p.post_type = 'treehole'
        """,
        (post_id,)
    )
    return result[0] if result else None


def check_user_liked(user_id: int, post_id: int) -> bool:
    """检查用户是否已点赞"""
    result = execute_query(
        "SELECT like_id FROM likes WHERE user_id = ? AND target_type = 'post' AND target_id = ?",
        (user_id, post_id)
    )
    return bool(result)


def format_treehole(treehole: dict, current_user_id: Optional[int] = None) -> dict:
    """格式化树洞数据"""
    return {
        "post_id": treehole["post_id"],
        "content": treehole["content"],
        "title": treehole.get("title"),
        "like_count": treehole.get("like_count", 0),
        "comment_count": treehole.get("comment_count", 0),
        "view_count": treehole.get("view_count", 0),
        "is_anonymous": treehole.get("is_anonymous", 1),
        "created_at": str(treehole.get("created_at", ""))[:19],
        "updated_at": str(treehole.get("updated_at", ""))[:19],
        "display_username": treehole.get("display_username", "匿名树洞"),
        "display_avatar": treehole.get("display_avatar"),
        "user_liked": check_user_liked(current_user_id, treehole["post_id"]) if current_user_id else False
    }


def record_post_view(post_id: int, user_id: Optional[int] = None, ip_address: str = None):
    """记录帖子浏览"""
    try:
        # 尝试插入浏览记录（如果已存在则忽略）
        execute_update(
            """INSERT IGNORE INTO post_views (post_id, user_id, ip_address)
               VALUES (?, ?, ?)""",
            (post_id, user_id, ip_address)
        )
        # 增加浏览计数
        execute_update(
            "UPDATE posts SET view_count = view_count + 1 WHERE post_id = ?",
            (post_id,)
        )
    except Exception:
        pass  # 浏览记录失败不影响主流程


# ===========================================
# API 端点
# ===========================================

@router.get("/list", response_model=TreeholeListResponse)
async def get_treehole_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    sort_by: str = Query(default="created_at", description="排序字段：created_at-时间，hot-热度"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取树洞列表

    Args:
        page: 页码
        page_size: 每页数量
        sort_by: 排序字段
        current_user: 当前用户

    Returns:
        树洞列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 计算分页
    offset = (page - 1) * page_size

    # 构建排序 SQL
    if sort_by == "hot":
        order_sql = "(like_count + comment_count * 2) DESC, created_at DESC"
    else:
        order_sql = "created_at DESC"

    # 查询树洞列表
    treeholes = execute_query(
        f"""
        SELECT
            p.post_id, p.content, p.title, p.like_count, p.comment_count, p.view_count,
            p.is_anonymous, p.created_at, p.updated_at,
            CASE
                WHEN p.is_anonymous = 1 THEN '匿名树洞'
                ELSE u.username
            END AS display_username,
            CASE
                WHEN p.is_anonymous = 1 THEN NULL
                ELSE u.avatar_url
            END AS display_avatar
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.user_id
        WHERE p.post_type = 'treehole' AND p.status = 1
        ORDER BY {order_sql}
        LIMIT ? OFFSET ?
        """,
        (page_size, offset)
    )

    # 获取总数
    count_result = execute_query(
        "SELECT COUNT(*) as count FROM posts WHERE post_type = 'treehole' AND status = 1"
    )
    total = count_result[0]["count"] if count_result else 0

    # 格式化数据
    treehole_list = [format_treehole(t, user_id) for t in (treeholes or [])]

    return TreeholeListResponse(
        success=True,
        data={
            "list": treehole_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(treehole_list) < total
        },
        message="获取成功"
    )


@router.post("", response_model=TreeholeResponse)
async def create_treehole(
    request: TreeholeCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发布树洞（匿名）

    Args:
        request: 创建树洞请求
        current_user: 当前用户

    Returns:
        发布结果

    Raises:
        HTTPException: 发布失败
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 敏感词过滤
    is_valid, message, filtered_content = filter_sensitive_text(request.content)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": 4001, "message": message}
        )

    # 处理标题
    title = request.title
    if title:
        _, _, filtered_title = filter_sensitive_text(title)
        title = filtered_title

    try:
        # 插入树洞（is_anonymous=1, post_type='treehole'）
        result = execute_update(
            """INSERT INTO posts (user_id, title, content, post_type, is_anonymous, status)
               VALUES (?, ?, ?, 'treehole', 1, 1)""",
            (user_id, title, filtered_content)
        )
        post_id = result

        # 更新用户发帖数
        execute_update(
            """INSERT INTO user_profiles (user_id, post_count) VALUES (?, 1)
               ON DUPLICATE KEY UPDATE post_count = post_count + 1""",
            (user_id,)
        )

        # 获取新创建的树洞
        new_treehole = get_treehole_by_id(post_id)

        return TreeholeResponse(
            success=True,
            message="发布成功",
            data=format_treehole(new_treehole, user_id)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5001, "message": f"发布失败：{str(e)}"}
        )


@router.get("/{post_id}")
async def get_treehole(
    post_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取树洞详情

    Args:
        post_id: 树洞 ID
        current_user: 当前用户

    Returns:
        树洞详情

    Raises:
        HTTPException: 树洞不存在
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    treehole = get_treehole_by_id(post_id)
    if not treehole:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "树洞不存在"}
        )

    # 记录浏览
    # record_post_view(post_id, user_id)

    return {
        "success": True,
        "data": format_treehole(treehole, user_id),
        "message": "获取成功"
    }


@router.delete("/{post_id}", response_model=TreeholeResponse)
async def delete_treehole(
    post_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    删除树洞（软删除）

    Args:
        post_id: 树洞 ID
        current_user: 当前用户

    Returns:
        删除结果

    Raises:
        HTTPException: 删除失败或无权限
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 获取树洞
    treehole = get_treehole_by_id(post_id)
    if not treehole:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 4002, "message": "树洞不存在"}
        )

    # 检查权限（只有作者可以删除）
    result = execute_query(
        "SELECT user_id FROM posts WHERE post_id = ?",
        (post_id,)
    )
    if result and result[0]["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": 4003, "message": "无权限删除他人的树洞"}
        )

    try:
        # 软删除
        execute_update(
            "UPDATE posts SET status = 0 WHERE post_id = ?",
            (post_id,)
        )

        # 更新用户发帖数
        execute_update(
            "UPDATE user_profiles SET post_count = GREATEST(0, post_count - 1) WHERE user_id = ?",
            (user_id,)
        )

        return TreeholeResponse(
            success=True,
            message="删除成功",
            data={"post_id": post_id}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": 5002, "message": f"删除失败：{str(e)}"}
        )


@router.get("/my/list", response_model=TreeholeListResponse)
async def get_my_treeholes(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的树洞列表

    Args:
        page: 页码
        page_size: 每页数量
        current_user: 当前用户

    Returns:
        我的树洞列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    # 计算分页
    offset = (page - 1) * page_size

    # 查询我的树洞列表
    treeholes = execute_query(
        """
        SELECT
            p.post_id, p.content, p.title, p.like_count, p.comment_count, p.view_count,
            p.is_anonymous, p.created_at, p.updated_at,
            '匿名树洞' AS display_username,
            NULL AS display_avatar
        FROM posts p
        WHERE p.post_type = 'treehole' AND p.user_id = ? AND p.status = 1
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, page_size, offset)
    )

    # 获取总数
    count_result = execute_query(
        "SELECT COUNT(*) as count FROM posts WHERE post_type = 'treehole' AND user_id = ? AND status = 1",
        (user_id,)
    )
    total = count_result[0]["count"] if count_result else 0

    # 格式化数据
    treehole_list = [format_treehole(t, user_id) for t in (treeholes or [])]

    return TreeholeListResponse(
        success=True,
        data={
            "list": treehole_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(treehole_list) < total
        },
        message="获取成功"
    )


@router.post("/reload-sensitive")
async def reload_sensitive_words(
    current_user: dict = Depends(get_current_user)
):
    """
    重新加载敏感词库（管理员功能）

    Args:
        current_user: 当前用户

    Returns:
        加载结果
    """
    # 这里可以添加权限检查，只允许管理员调用
    load_sensitive_words()
    return {
        "success": True,
        "message": "敏感词库已重新加载",
        "data": {"count": len(SENSITIVE_WORDS_CACHE.get("all", []))}
    }
