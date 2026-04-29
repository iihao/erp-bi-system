"""
发现页面 API
提供推荐内容、个性化推荐、分类筛选、搜索等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from utils.database import execute_query, execute_update
from api.auth import get_current_user
import math

router = APIRouter(prefix="/api/discovery", tags=["发现"])


# ===========================================
# 响应模型
# ===========================================

class ContentItem(BaseModel):
    """内容项（帖子/报表）"""
    id: int
    type: str  # post 或 report
    title: Optional[str]
    content: str
    author_id: int
    author_name: str
    author_avatar: Optional[str]
    like_count: int
    comment_count: int
    view_count: int
    category: Optional[str]
    tags: List[str]
    created_at: str
    score: float  # 热度分数


class DiscoveryListResponse(BaseModel):
    """发现列表响应"""
    success: bool
    data: dict
    message: str


class SearchResponse(BaseModel):
    """搜索结果响应"""
    success: bool
    data: dict
    message: str


class CategoryItem(BaseModel):
    """分类项"""
    id: int
    name: str
    description: Optional[str]
    content_count: int
    icon: Optional[str]


class TagItem(BaseModel):
    """标签项"""
    id: int
    name: str
    content_count: int


class RecommendationConfig(BaseModel):
    """推荐配置"""
    enable_personalized: bool
    hot_weight: float  # 热度权重
    time_weight: float  # 时间权重
    interaction_weight: float  # 互动权重


# ===========================================
# 辅助函数
# ===========================================

def calculate_hot_score(like_count: int, comment_count: int, view_count: int,
                        created_at: str, config: dict = None) -> float:
    """
    计算内容热度分数

    算法：热度 = (点赞数 * 1 + 评论数 * 2 + 浏览数 * 0.1) * 时间衰减系数

    时间衰减系数 = 2^(-天数/半衰期)，半衰期设为 7 天
    """
    from datetime import datetime

    if config is None:
        config = {
            "like_weight": 1.0,
            "comment_weight": 2.0,
            "view_weight": 0.1,
            "half_life_days": 7
        }

    # 基础互动分数
    base_score = (
        like_count * config["like_weight"] +
        comment_count * config["comment_weight"] +
        view_count * config["view_weight"]
    )

    # 时间衰减
    try:
        created_date = datetime.strptime(str(created_at)[:19], "%Y-%m-%d %H:%M:%S")
        days_old = (datetime.now() - created_date).days
        # 半衰期衰减公式
        decay_factor = math.pow(2, -days_old / config["half_life_days"])
    except Exception:
        decay_factor = 1.0

    return round(base_score * decay_factor, 2)


def format_post_item(post: dict, score: float) -> dict:
    """格式化帖子数据"""
    return {
        "id": post["post_id"],
        "type": "post",
        "title": post.get("title"),
        "content": post.get("content", "")[:200] + "..." if len(post.get("content", "")) > 200 else post.get("content", ""),
        "author_id": post.get("user_id", 0),
        "author_name": post.get("display_username", "匿名用户"),
        "author_avatar": post.get("display_avatar"),
        "like_count": post.get("like_count", 0),
        "comment_count": post.get("comment_count", 0),
        "view_count": post.get("view_count", 0),
        "category": "treehole" if post.get("is_anonymous") else "dynamic",
        "tags": [],
        "created_at": str(post.get("created_at", ""))[:19],
        "score": score
    }


def format_report_item(report: dict, score: float) -> dict:
    """格式化报表数据"""
    return {
        "id": report["report_id"],
        "type": "report",
        "title": report.get("report_name"),
        "content": report.get("description", "")[:200] + "..." if len(report.get("description", "")) > 200 else report.get("description", ""),
        "author_id": report.get("created_by", 0),
        "author_name": report.get("creator_name", "未知"),
        "author_avatar": None,
        "like_count": report.get("like_count", 0),
        "comment_count": report.get("comment_count", 0),
        "view_count": report.get("view_count", 0),
        "category": report.get("category", "general"),
        "tags": report.get("tags", []) or [],
        "created_at": str(report.get("created_at", ""))[:19],
        "score": score
    }


def get_user_interests(user_id: int) -> Dict[str, List[int]]:
    """获取用户兴趣（基于点赞和关注历史）"""
    interests = {"liked_posts": [], "liked_reports": [], "following_users": []}

    # 获取用户点赞的帖子
    result = execute_query(
        """SELECT target_id FROM likes WHERE user_id = ? AND target_type = 'post'
           ORDER BY created_at DESC LIMIT 50""",
        (user_id,)
    )
    interests["liked_posts"] = [r["target_id"] for r in (result or [])]

    # 获取用户点赞的报表
    result = execute_query(
        """SELECT target_id FROM likes WHERE user_id = ? AND target_type = 'report'
           ORDER BY created_at DESC LIMIT 50""",
        (user_id,)
    )
    interests["liked_reports"] = [r["target_id"] for r in (result or [])]

    # 获取用户关注的用户
    result = execute_query(
        """SELECT followed_id FROM follows WHERE follower_id = ?
           ORDER BY created_at DESC LIMIT 50""",
        (user_id,)
    )
    interests["following_users"] = [r["followed_id"] for r in (result or [])]

    return interests


def get_personalized_recommendations(user_id: int, limit: int = 20) -> List[dict]:
    """
    获取个性化推荐（简单版本：基于用户点赞和关注历史）

    推荐策略：
    1. 优先推荐关注用户发布的内容
    2. 推荐与用户点赞内容相似的内容（同分类）
    3. 混合热门内容
    """
    recommendations = []
    interests = get_user_interests(user_id)

    # 1. 获取关注用户的帖子（权重最高）
    if interests["following_users"]:
        following_ids = ",".join(map(str, interests["following_users"]))
        posts = execute_query(
            f"""
            SELECT p.*,
                   CASE WHEN p.is_anonymous = 1 THEN '匿名树洞' ELSE u.username END AS display_username,
                   CASE WHEN p.is_anonymous = 1 THEN NULL ELSE u.avatar_url END AS display_avatar
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.user_id
            WHERE p.post_type IN ('normal', 'treehole')
              AND p.status = 1
              AND p.user_id IN ({following_ids})
            ORDER BY p.created_at DESC
            LIMIT {limit // 3}
            """
        )
        for post in (posts or []):
            score = calculate_hot_score(
                post.get("like_count", 0),
                post.get("comment_count", 0),
                post.get("view_count", 0),
                str(post.get("created_at", ""))
            )
            recommendations.append({
                **format_post_item(post, score),
                "score": score + 50  # 关注用户的内容加权
            })

    # 2. 获取热门帖子（排除已推荐）
    recommended_ids = {r["id"] for r in recommendations if r["type"] == "post"}
    exclude_ids = ",".join(map(str, recommended_ids)) if recommended_ids else "0"

    posts = execute_query(
        f"""
        SELECT p.*,
               CASE WHEN p.is_anonymous = 1 THEN '匿名树洞' ELSE u.username END AS display_username,
               CASE WHEN p.is_anonymous = 1 THEN NULL ELSE u.avatar_url END AS display_avatar
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.user_id
        WHERE p.post_type IN ('normal', 'treehole')
          AND p.status = 1
          AND p.post_id NOT IN ({exclude_ids})
        ORDER BY (p.like_count + p.comment_count * 2) DESC, p.created_at DESC
        LIMIT {limit // 2}
        """
    )
    for post in (posts or []):
        score = calculate_hot_score(
            post.get("like_count", 0),
            post.get("comment_count", 0),
            post.get("view_count", 0),
            str(post.get("created_at", ""))
        )
        recommendations.append(format_post_item(post, score))

    # 3. 获取热门报表
    reports = execute_query(
        """
        SELECT rc.*, u.username AS creator_name
        FROM report_configs rc
        LEFT JOIN users u ON rc.created_by = u.user_id
        WHERE rc.status = 1
        ORDER BY (rc.like_count + rc.view_count * 0.1) DESC, rc.created_at DESC
        LIMIT {limit // 2}
        """.format(limit=limit // 2)
    )
    for report in (reports or []):
        score = calculate_hot_score(
            report.get("like_count", 0),
            report.get("comment_count", 0),
            report.get("view_count", 0),
            str(report.get("created_at", ""))
        )
        recommendations.append(format_report_item(report, score))

    # 按热度排序
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return recommendations[:limit]


def get_hot_content(limit: int = 20, content_type: str = "all") -> List[dict]:
    """
    获取热门内容（基于热度 + 时间算法）

    Args:
        limit: 返回数量
        content_type: 内容类型 (all/post/report)
    """
    results = []

    # 热度配置
    config = {
        "like_weight": 1.0,
        "comment_weight": 2.0,
        "view_weight": 0.1,
        "half_life_days": 7
    }

    if content_type in ["all", "post"]:
        # 获取热门帖子
        posts = execute_query(
            """
            SELECT p.*,
                   CASE WHEN p.is_anonymous = 1 THEN '匿名树洞' ELSE u.username END AS display_username,
                   CASE WHEN p.is_anonymous = 1 THEN NULL ELSE u.avatar_url END AS display_avatar
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.user_id
            WHERE p.post_type IN ('normal', 'treehole') AND p.status = 1
            ORDER BY (p.like_count + p.comment_count * 2 + p.view_count * 0.1) DESC, p.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        for post in (posts or []):
            score = calculate_hot_score(
                post.get("like_count", 0),
                post.get("comment_count", 0),
                post.get("view_count", 0),
                str(post.get("created_at", "")),
                config
            )
            results.append(format_post_item(post, score))

    if content_type in ["all", "report"]:
        # 获取热门报表
        reports = execute_query(
            """
            SELECT rc.*, u.username AS creator_name
            FROM report_configs rc
            LEFT JOIN users u ON rc.created_by = u.user_id
            WHERE rc.status = 1
            ORDER BY (rc.like_count + rc.comment_count * 2 + rc.view_count * 0.1) DESC, rc.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        for report in (reports or []):
            score = calculate_hot_score(
                report.get("like_count", 0),
                report.get("comment_count", 0),
                report.get("view_count", 0),
                str(report.get("created_at", "")),
                config
            )
            results.append(format_report_item(report, score))

    # 按热度排序
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:limit]


def search_content(keyword: str, content_type: str = "all",
                   category: str = None, limit: int = 20, offset: int = 0) -> tuple:
    """
    搜索内容

    Args:
        keyword: 搜索关键词
        content_type: 内容类型
        category: 分类筛选
        limit: 返回数量
        offset: 偏移量

    Returns:
        (results, total_count)
    """
    results = []
    total = 0

    # 构建搜索条件
    search_term = f"%{keyword}%"

    if content_type in ["all", "post"]:
        # 搜索帖子
        where_clause = """
            p.post_type IN ('normal', 'treehole') AND p.status = 1
            AND (p.title LIKE ? OR p.content LIKE ?)
        """
        params = [search_term, search_term]

        if category:
            if category == "treehole":
                where_clause += " AND p.is_anonymous = 1"
            elif category == "dynamic":
                where_clause += " AND p.is_anonymous = 0"

        # 计数
        count_sql = f"SELECT COUNT(*) as count FROM posts p WHERE {where_clause}"
        count_result = execute_query(count_sql, params)
        total += count_result[0]["count"] if count_result else 0

        # 查询
        posts = execute_query(
            f"""
            SELECT p.*,
                   CASE WHEN p.is_anonymous = 1 THEN '匿名树洞' ELSE u.username END AS display_username,
                   CASE WHEN p.is_anonymous = 1 THEN NULL ELSE u.avatar_url END AS display_avatar
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.user_id
            WHERE {where_clause}
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        for post in (posts or []):
            score = calculate_hot_score(
                post.get("like_count", 0),
                post.get("comment_count", 0),
                post.get("view_count", 0),
                str(post.get("created_at", ""))
            )
            results.append(format_post_item(post, score))

    if content_type in ["all", "report"]:
        # 搜索报表
        where_clause = """
            rc.status = 1 AND (rc.report_name LIKE ? OR rc.description LIKE ?)
        """
        params = [search_term, search_term]

        if category:
            where_clause += " AND rc.category = ?"
            params.append(category)

        # 计数
        count_sql = f"SELECT COUNT(*) as count FROM report_configs rc WHERE {where_clause}"
        count_result = execute_query(count_sql, params)
        total += count_result[0]["count"] if count_result else 0

        # 查询
        reports = execute_query(
            f"""
            SELECT rc.*, u.username AS creator_name
            FROM report_configs rc
            LEFT JOIN users u ON rc.created_by = u.user_id
            WHERE {where_clause}
            ORDER BY rc.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        for report in (reports or []):
            score = calculate_hot_score(
                report.get("like_count", 0),
                report.get("comment_count", 0),
                report.get("view_count", 0),
                str(report.get("created_at", ""))
            )
            results.append(format_report_item(report, score))

    return results, total


def get_categories() -> List[dict]:
    """获取分类列表"""
    categories = [
        {"id": 1, "name": "全部", "description": "所有内容", "icon": "all", "content_count": 0},
        {"id": 2, "name": "热门", "description": "热门内容", "icon": "hot", "content_count": 0},
        {"id": 3, "name": "树洞", "description": "匿名树洞", "icon": "treehole", "content_count": 0},
        {"id": 4, "name": "动态", "description": "用户动态", "icon": "dynamic", "content_count": 0},
        {"id": 5, "name": "报表", "description": "数据报表", "icon": "report", "content_count": 0},
    ]

    # 统计各分类内容数
    result = execute_query(
        """SELECT
            (SELECT COUNT(*) FROM posts WHERE post_type IN ('normal', 'treehole') AND status = 1) as post_count,
            (SELECT COUNT(*) FROM posts WHERE is_anonymous = 1 AND status = 1) as treehole_count,
            (SELECT COUNT(*) FROM posts WHERE is_anonymous = 0 AND status = 1) as dynamic_count,
            (SELECT COUNT(*) FROM report_configs WHERE status = 1) as report_count
        """
    )
    if result:
        categories[0]["content_count"] = result[0]["post_count"] + result[0]["report_count"]
        categories[1]["content_count"] = 0  # 热门不统计
        categories[2]["content_count"] = result[0]["treehole_count"]
        categories[3]["content_count"] = result[0]["dynamic_count"]
        categories[4]["content_count"] = result[0]["report_count"]

    return categories


def get_hot_tags(limit: int = 20) -> List[dict]:
    """获取热门标签"""
    # 从报表中获取标签
    result = execute_query(
        """
        SELECT tag_name, COUNT(*) as content_count
        FROM (
            SELECT JSON_EXTRACT(tags, CONCAT('$[', n, ']')) as tag_name
            FROM report_configs
            WHERE tags IS NOT NULL AND JSON_LENGTH(tags) > 0
            JOIN (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                  UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) numbers
            ON n < JSON_LENGTH(tags)
        ) tag_table
        GROUP BY tag_name
        ORDER BY content_count DESC
        LIMIT ?
        """,
        (limit,)
    )

    if result:
        return [{"id": i + 1, "name": r["tag_name"], "content_count": r["content_count"]}
                for i, r in enumerate(result)]

    # 默认标签
    default_tags = ["热门", "推荐", "数据分析", "销售", "财务", "运营", "产品", "技术"]
    return [{"id": i + 1, "name": tag, "content_count": 0} for i, tag in enumerate(default_tags)]


# ===========================================
# API 端点
# ===========================================

@router.get("/recommend", response_model=DiscoveryListResponse)
async def get_recommendations(
    limit: int = Query(default=20, ge=1, le=50, description="返回数量"),
    personalized: bool = Query(default=True, description="是否个性化推荐"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取推荐内容

    Args:
        limit: 返回数量
        personalized: 是否启用个性化推荐
        current_user: 当前用户

    Returns:
        推荐内容列表
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))

    if personalized:
        # 个性化推荐
        recommendations = get_personalized_recommendations(user_id, limit)
    else:
        # 热门推荐
        items = get_hot_content(limit, "all")
        recommendations = items

    return DiscoveryListResponse(
        success=True,
        data={
            "list": recommendations,
            "total": len(recommendations),
            "personalized": personalized
        },
        message="获取成功"
    )


@router.get("/hot", response_model=DiscoveryListResponse)
async def get_hot_list(
    limit: int = Query(default=20, ge=1, le=50, description="返回数量"),
    content_type: str = Query(default="all", description="内容类型：all/post/report"),
    category: str = Query(default=None, description="分类筛选")
):
    """
    获取热门内容列表

    Args:
        limit: 返回数量
        content_type: 内容类型
        category: 分类筛选

    Returns:
        热门内容列表
    """
    items = get_hot_content(limit, content_type)

    # 分类筛选
    if category:
        if category == "treehole":
            items = [i for i in items if i.get("category") == "treehole"]
        elif category == "dynamic":
            items = [i for i in items if i.get("category") == "dynamic"]
        elif category == "report":
            items = [i for i in items if i.get("type") == "report"]

    return DiscoveryListResponse(
        success=True,
        data={
            "list": items,
            "total": len(items),
            "category": category,
            "content_type": content_type
        },
        message="获取成功"
    )


@router.get("/search", response_model=SearchResponse)
async def search(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    content_type: str = Query(default="all", description="内容类型：all/post/report"),
    category: str = Query(default=None, description="分类筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量")
):
    """
    搜索内容

    Args:
        keyword: 搜索关键词
        content_type: 内容类型
        category: 分类筛选
        page: 页码
        page_size: 每页数量

    Returns:
        搜索结果
    """
    offset = (page - 1) * page_size

    results, total = search_content(keyword, content_type, category, page_size, offset)

    return SearchResponse(
        success=True,
        data={
            "list": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(results) < total,
            "keyword": keyword
        },
        message="搜索完成"
    )


@router.get("/categories")
async def get_category_list():
    """获取分类列表"""
    categories = get_categories()
    return {
        "success": True,
        "data": categories,
        "message": "获取成功"
    }


@router.get("/tags")
async def get_tag_list(
    limit: int = Query(default=20, ge=1, le=50, description="返回数量")
):
    """获取热门标签列表"""
    tags = get_hot_tags(limit)
    return {
        "success": True,
        "data": tags,
        "message": "获取成功"
    }


@router.get("/feed", response_model=DiscoveryListResponse)
async def get_feed(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    category: str = Query(default=None, description="分类筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取发现页信息流（支持无限滚动）

    Args:
        page: 页码
        page_size: 每页数量
        category: 分类筛选
        current_user: 当前用户

    Returns:
        信息流数据
    """
    from core.security import decode_token
    user_id = decode_token(current_user.get("token"))
    offset = (page - 1) * page_size

    # 根据分类获取内容
    if category == "recommend":
        # 个性化推荐
        items = get_personalized_recommendations(user_id, page_size)
    elif category == "hot":
        # 热门
        items = get_hot_content(page_size, "all")
    elif category == "treehole":
        items = get_hot_content(page_size, "post")
        items = [i for i in items if i.get("category") == "treehole"]
    elif category == "dynamic":
        items = get_hot_content(page_size, "post")
        items = [i for i in items if i.get("category") == "dynamic"]
    elif category == "report":
        items = get_hot_content(page_size, "report")
    else:
        # 默认混合内容
        items = get_hot_content(page_size, "all")

    # 获取总数（估算）
    total = 1000  # 简化处理，实际应该查询数据库

    return DiscoveryListResponse(
        success=True,
        data={
            "list": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": len(items) == page_size,
            "category": category or "all"
        },
        message="获取成功"
    )


@router.get("/config")
async def get_recommend_config():
    """获取推荐配置"""
    return {
        "success": True,
        "data": {
            "enable_personalized": True,
            "hot_weight": 0.6,
            "time_weight": 0.3,
            "interaction_weight": 0.1
        },
        "message": "获取成功"
    }
