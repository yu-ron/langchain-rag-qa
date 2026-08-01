"""
聊天服务
管理消息存储和 RAG 问答调用
"""
from typing import List, AsyncIterator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Message
from app.rag.chain import ask_stream


async def save_message(
    db: AsyncSession,
    session_id: int,
    user_id: int,
    role: str,
    content: str,
    citations: dict | None = None,
) -> Message:
    """保存一条消息到数据库"""
    msg = Message(
        session_id=session_id,
        user_id=user_id,
        role=role,
        content=content,
        citations=citations,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


async def get_chat_history(
    db: AsyncSession,
    session_id: int,
    limit: int = 50,
) -> List[dict]:
    """
    获取某个会话的聊天历史
    按时间正序返回（旧的在前）
    """
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": m.citations,
            "feedback": m.feedback,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


async def rag_chat_stream(
    db: AsyncSession,
    session_id: int,
    user_id: int,
    question: str,
) -> AsyncIterator[dict]:
    """
    完整的 RAG 问答流程（流式）：

    1. 从数据库获取历史对话
    2. 调用 RAG 链进行问答
    3. 流式输出回答内容
    4. 保存问答记录到数据库
    """
    # 获取历史记录（最近10轮）
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    recent_messages = result.scalars().all()
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(recent_messages)
    ]

    # 调用 RAG 链
    full_answer = ""
    citations = []

    async for chunk in ask_stream(question, history):
        if chunk["type"] == "content":
            full_answer += chunk["data"]
            yield {"type": "content", "data": chunk["data"]}
        elif chunk["type"] == "citations":
            citations = chunk["data"]

    # 保存消息记录
    await save_message(db, session_id, user_id, "user", question)
    await save_message(
        db, session_id, user_id, "assistant",
        full_answer, citations,
    )
    await db.commit()

    # 最后推送引用信息
    yield {"type": "citations", "data": citations}


async def set_message_feedback(
    db: AsyncSession,
    message_id: int,
    feedback: str,
) -> bool:
    """设置消息反馈（点赞/点踩）"""
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        return False
    msg.feedback = feedback
    await db.commit()
    return True
