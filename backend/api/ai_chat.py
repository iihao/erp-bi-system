#!/usr/bin/env python3
"""
AI Chat 接口 - 支持流式对话
模仿主流 AI 聊天 UI，接入配置的 AI 大模型
"""

import os
import json
import uuid
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from api.ai_query import BaiLianClient, get_db_connection

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-chat", tags=["AI 对话"])


# ============================================
# 数据模型
# ============================================

class ChatMessage(BaseModel):
    role: str  # user / assistant / system
    content: str


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    model: Optional[str] = None


class ConversationInfo(BaseModel):
    id: str
    title: str
    type: str = "chat"
    created_at: str
    updated_at: str
    message_count: int


# ============================================
# 对话管理
# ============================================

def create_conversation(title: str = "新对话", conv_type: str = "chat") -> str:
    """创建新对话"""
    conv_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ai_conversations (id, title, type, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, conv_type, now, now)
            )
        logger.info(f"✅ 创建新对话: {conv_id[:8]}... (type={conv_type})")
    except Exception as e:
        logger.warning(f"⚠️ 数据库创建对话失败，使用内存模式: {e}")
    return conv_id


def save_message(conv_id: str, role: str, content: str, model: str = "") -> int:
    """保存单条消息"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ai_chat_messages (conversation_id, role, content, model, created_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, role, content, model, now)
            )
            # 更新对话时间
            cursor.execute("UPDATE ai_conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
            return cursor.lastrowid
    except Exception as e:
        logger.warning(f"⚠️ 保存消息失败: {e}")
        return -1


def get_conversation_history(conv_id: str) -> List[Dict[str, Any]]:
    """获取对话历史"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM ai_chat_messages WHERE conversation_id = ? ORDER BY id ASC",
                (conv_id,)
            )
            rows = cursor.fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in rows]
    except Exception as e:
        logger.warning(f"⚠️ 获取对话历史失败: {e}")
        return []


def list_conversations(limit: int = 50, offset: int = 0, conv_type: str = None) -> List[Dict[str, Any]]:
    """获取对话列表，可按类型过滤"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if conv_type:
                cursor.execute(
                    """SELECT id, title, type, created_at, updated_at,
                       (SELECT COUNT(*) FROM ai_chat_messages WHERE conversation_id = ai_conversations.id) as message_count
                       FROM ai_conversations WHERE type = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
                    (conv_type, limit, offset)
                )
            else:
                cursor.execute(
                    """SELECT id, title, type, created_at, updated_at,
                       (SELECT COUNT(*) FROM ai_chat_messages WHERE conversation_id = ai_conversations.id) as message_count
                       FROM ai_conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
                    (limit, offset)
                )
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "type": r["type"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                    "message_count": r["message_count"],
                }
                for r in rows
            ]
    except Exception as e:
        logger.warning(f"⚠️ 获取对话列表失败: {e}")
        return []


def update_conversation_title(conv_id: str, title: str):
    """更新对话标题"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE ai_conversations SET title = ? WHERE id = ?", (title, conv_id))
    except Exception as e:
        logger.warning(f"⚠️ 更新对话标题失败: {e}")


def delete_conversation(conv_id: str):
    """删除对话及其消息"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_chat_messages WHERE conversation_id = ?", (conv_id,))
            cursor.execute("DELETE FROM ai_conversations WHERE id = ?", (conv_id,))
    except Exception as e:
        logger.warning(f"⚠️ 删除对话失败: {e}")


# ============================================
# 流式 Chat 端点
# ============================================

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式对话端点 - Server-Sent Events
    支持多轮对话上下文
    """
    bailian = BaiLianClient()

    if not bailian.api_key or bailian.api_key == 'your-api-key-here':
        raise HTTPException(status_code=503, detail="AI 服务未配置")

    # 确定使用的模型
    model = request.model or bailian.model

    # 创建或获取对话
    conv_id = request.conversation_id
    is_new = False
    if not conv_id:
        conv_id = create_conversation()
        is_new = True

    # 保存用户消息
    save_message(conv_id, "user", request.message, model)

    # 获取对话历史（最近 20 轮，保持上下文但控制 token）
    history = get_conversation_history(conv_id)

    # 构建消息列表
    messages = [
        {"role": "system", "content": "你是一个专业的 AI 助手。请用简洁、准确的方式回答用户的问题。如果涉及数据或技术问题，请给出实用的建议。回答使用 Markdown 格式，代码请用代码块包裹。"}
    ]

    # 截取最近的消息作为上下文（最多 40 条 = 20 轮对话）
    recent = history[-40:] if len(history) > 40 else history
    for msg in recent:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 调用 LLM 流式输出
    async def generate():
        try:
            client = await bailian._get_client()
            url = f"{bailian.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {bailian.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            }

            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
                "stream": True,
            }

            # 发送对话 ID
            yield f"event: conversation_id\ndata: {json.dumps({'id': conv_id, 'is_new': is_new})}\n\n"

            full_content = ""

            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    yield f"event: error\ndata: {json.dumps({'status': response.status_code, 'detail': error_body.decode()[:200]})}\n\n"
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                                    yield f"event: message\ndata: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue

            # 发送完成信号
            yield f"event: done\ndata: {json.dumps({'conv_id': conv_id})}\n\n"

            # 保存 AI 回复
            save_message(conv_id, "assistant", full_content, model)

            # 如果是新对话，自动设置标题
            if is_new:
                title = request.message[:30] + ("..." if len(request.message) > 30 else "")
                update_conversation_title(conv_id, title)

        except Exception as e:
            logger.error(f"❌ 流式对话失败: {type(e).__name__}: {e}")
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================
# 对话管理 API
# ============================================

@router.get("/conversations")
async def get_conversations(limit: int = 50, offset: int = 0, type: str = None):
    """获取对话列表，支持按类型过滤"""
    conversations = list_conversations(limit, offset, conv_type=type)
    return {"data": conversations, "total": len(conversations)}


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, type: str = None):
    """获取对话详情，可选验证类型"""
    # 如果指定了type，先验证对话类型是否匹配
    if type:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT type FROM ai_conversations WHERE id = ?", (conv_id,))
                row = cursor.fetchone()
                if row and row["type"] != type:
                    raise HTTPException(status_code=403, detail="对话类型不匹配")
        except HTTPException:
            raise
        except Exception:
            pass  # 数据库查询失败时不阻塞
    history = get_conversation_history(conv_id)
    return {"id": conv_id, "messages": history}


@router.put("/conversations/{conv_id}/title")
async def update_title(conv_id: str, request: dict, type: str = None):
    """更新对话标题，可选验证类型"""
    if type:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT type FROM ai_conversations WHERE id = ?", (conv_id,))
                row = cursor.fetchone()
                if row and row["type"] != type:
                    raise HTTPException(status_code=403, detail="对话类型不匹配")
        except HTTPException:
            raise
        except Exception:
            pass
    title = request.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    update_conversation_title(conv_id, title)
    return {"message": "标题已更新"}


@router.delete("/conversations/{conv_id}")
async def delete_conv(conv_id: str, type: str = None):
    """删除对话，可选验证类型"""
    if type:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT type FROM ai_conversations WHERE id = ?", (conv_id,))
                row = cursor.fetchone()
                if row and row["type"] != type:
                    raise HTTPException(status_code=403, detail="对话类型不匹配")
        except HTTPException:
            raise
        except Exception:
            pass
    delete_conversation(conv_id)
    return {"message": "对话已删除"}


@router.post("/conversations/new")
async def create_new_conv(type: str = "chat"):
    """创建新对话，指定类型"""
    conv_id = create_conversation(conv_type=type)
    return {"id": conv_id, "title": "新对话", "type": type}


@router.post("/conversations/{conv_id}/messages")
async def save_message_to_conv(conv_id: str, request: dict, type: str = None):
    """保存单条消息到指定对话，可选验证类型"""
    if type:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT type FROM ai_conversations WHERE id = ?", (conv_id,))
                row = cursor.fetchone()
                if row and row["type"] != type:
                    raise HTTPException(status_code=403, detail="对话类型不匹配")
        except HTTPException:
            raise
        except Exception:
            pass
    role = request.get("role", "")
    content = request.get("content", "")
    if not role or not content:
        raise HTTPException(status_code=400, detail="role 和 content 不能为空")
    save_message(conv_id, role, content)
    return {"message": "消息已保存"}


# ============================================
# 数据库初始化
# ============================================

def init_ai_chat_tables():
    """初始化 AI 对话相关表"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 对话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 为已存在的表添加 type 列（如果不存在）
            try:
                cursor.execute("ALTER TABLE ai_conversations ADD COLUMN type TEXT NOT NULL DEFAULT 'chat'")
                logger.info("✅ 为 ai_conversations 添加了 type 列")
            except Exception:
                pass  # 列已存在

            # 消息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_conv ON ai_chat_messages(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_type ON ai_conversations(type, updated_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_updated ON ai_conversations(updated_at)')

            logger.info("✅ AI 对话表初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ AI 对话表初始化失败: {e}")


# 启动时初始化表
init_ai_chat_tables()
