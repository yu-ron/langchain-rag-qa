"""
聊天 API
流式问答接口
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_user
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["问答"])


class ChatRequest(BaseModel):
    """问答请求"""
    session_id: int = Field(..., description="会话ID")
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")


class FeedbackRequest(BaseModel):
    """反馈请求"""
    message_id: int = Field(..., description="消息ID")
    feedback: str = Field(..., pattern="^(like|dislike)$", description="like 或 dislike")


@router.post("/ask", summary="发送问题（流式返回）")
async def ask_question(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    向知识库提问，流式返回回答。

    使用 Server-Sent Events (SSE) 协议，前端用 EventSource 或 fetch 读取流式数据。

    响应格式（每行一个 JSON）：
    {"type": "content", "data": "回答片段"}
    {"type": "citations", "data": [{"index": 1, "content": "...", "metadata": {...}}]}
    {"type": "done", "data": null}
    """

    async def generate():
        try:
            async for chunk in chat_service.rag_chat_stream(
                db, req.session_id, current_user.id, req.question
            ):
                # SSE 格式：data: {json}\n\n
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': None})}\n\n"
        except Exception as e:
            error_data = {"type": "error", "data": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


@router.post("/feedback", summary="消息反馈")
async def set_feedback(
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """对 AI 回答点赞或点踩"""
    success = await chat_service.set_message_feedback(db, req.message_id, req.feedback)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    return {"message": "反馈成功"}
