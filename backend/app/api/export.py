"""
对话导出 API
支持导出为 Markdown 格式
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_user
from app.services import session_service

router = APIRouter(prefix="/api/export", tags=["导出"])


@router.get("/session/{session_id}", summary="导出对话为 Markdown")
async def export_session_markdown(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    把某个会话的所有消息导出为 Markdown 格式文本。
    可以直接保存为 .md 文件查看。
    """
    detail = await session_service.get_session_detail(db, session_id, current_user.id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    lines = []
    lines.append(f"# {detail['title']}")
    lines.append(f"")
    lines.append(f"创建时间: {detail['created_at']}")
    lines.append(f"更新时间: {detail['updated_at']}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    for msg in detail.get("messages", []):
        if msg["role"] == "user":
            lines.append(f"### 🙋 用户")
        else:
            lines.append(f"### 🤖 AI 助手")

        lines.append(f"")
        lines.append(msg["content"])
        lines.append(f"")

        if msg.get("citations"):
            lines.append(f"> **引用来源：**")
            for cite in msg["citations"]:
                snippet = cite["content"][:150] + "..." if len(cite["content"]) > 150 else cite["content"]
                lines.append(f"> - [来源{cite['index']}] {snippet}")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    markdown_content = "\n".join(lines)

    return PlainTextResponse(
        content=markdown_content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=chat_{session_id}.md"
        },
    )
