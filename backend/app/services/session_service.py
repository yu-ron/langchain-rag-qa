"""
会话管理服务
创建、查询、删除、命名会话
"""
from typing import List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Session, Message


async def create_session(
    db: AsyncSession,
    user_id: int,
    title: str = "新对话",
) -> Session:
    """创建新会话"""
    session = Session(user_id=user_id, title=title)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 30,
) -> dict:
    """
    获取用户的所有会话列表
    按更新时间倒序（最近对话的在前）
    """
    # 查询总数
    total_result = await db.execute(
        select(Session).where(Session.user_id == user_id)
    )
    total = len(total_result.scalars().all())

    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(desc(Session.updated_at))
        .offset(offset)
        .limit(page_size)
    )
    sessions = result.scalars().all()

    # 获取每个会话的最后一条消息预览
    items = []
    for s in sessions:
        preview = ""
        msg_result = await db.execute(
            select(Message)
            .where(Message.session_id == s.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()
        if last_msg:
            preview = last_msg.content[:50] + ("..." if len(last_msg.content) > 50 else "")

        items.append({
            "id": s.id,
            "title": s.title,
            "preview": preview,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


async def get_session_detail(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> dict | None:
    """获取会话详情（含消息列表）"""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return None

    # 获取消息列表
    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(50)
    )
    messages = msg_result.scalars().all()

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": m.citations,
                "feedback": m.feedback,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


async def update_session_title(
    db: AsyncSession,
    session_id: int,
    title: str,
) -> bool:
    """重命名会话"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return False
    session.title = title
    await db.commit()
    return True


async def delete_session(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> bool:
    """删除会话（级联删除所有消息）"""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return False
    await db.delete(session)
    await db.commit()
    return True
