"""
会话管理 API
创建、查询、重命名、删除会话
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_user
from app.services import session_service, chat_service

router = APIRouter(prefix="/api/sessions", tags=["会话"])


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    title: str = Field(default="新对话", max_length=200, description="会话标题")


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    title: str = Field(..., min_length=1, max_length=200, description="新标题")


@router.post("", summary="创建会话")
async def create_session(
    req: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新会话"""
    session = await session_service.create_session(db, current_user.id, req.title)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@router.get("", summary="会话列表")
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的会话列表"""
    return await session_service.get_user_sessions(db, current_user.id, page, page_size)


@router.get("/{session_id}", summary="会话详情")
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话详情，包含消息历史"""
    detail = await session_service.get_session_detail(db, session_id, current_user.id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return detail


@router.put("/{session_id}", summary="重命名会话")
async def rename_session(
    session_id: int,
    req: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重命名会话"""
    success = await session_service.update_session_title(db, session_id, req.title)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return {"message": "重命名成功"}


@router.delete("/{session_id}", summary="删除会话")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除会话及其所有消息"""
    success = await session_service.delete_session(db, session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return {"message": "删除成功"}
