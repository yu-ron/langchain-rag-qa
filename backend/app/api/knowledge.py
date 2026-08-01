"""
知识库管理 API
仅管理员可操作：上传、查看、删除文档
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status as http_status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.utils.dependencies import get_admin_user
from app.services import document_service

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.post("/upload", summary="上传文档")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    上传文档到知识库。
    文档会被自动解析、切分、向量化处理。

    支持的格式：PDF、TXT、CSV、Markdown、Word (.docx)
    """
    # 1. 读取文件内容
    content = await file.read()
    filename = file.filename or "unknown"

    # 2. 验证文件
    error = document_service.validate_upload(filename, len(content))
    if error:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=error)

    # 3. 保存文件
    file_path = await document_service.save_upload_file(filename, content)

    # 4. 创建数据库记录
    ext = os.path.splitext(filename)[1].lower()
    doc = await document_service.create_document_record(
        db=db,
        filename=filename,
        file_type=ext,
        file_size=len(content),
        file_path=file_path,
        uploaded_by=current_user.id,
    )
    await db.commit()

    # 5. 同步处理文档（等几秒，但保证可靠）
    doc_status = "completed"
    try:
        await document_service.process_document(doc.id, file_path, filename)
    except Exception as e:
        doc_status = "failed"
        # 更新失败状态
        from app.models.user import Document
        from sqlalchemy import select
        result = await db.execute(select(Document).where(Document.id == doc.id))
        doc_record = result.scalar_one_or_none()
        if doc_record:
            doc_record.status = "failed"
            doc_record.error_message = str(e)
            await db.commit()

    return {
        "message": "上传成功" if doc_status == "completed" else f"处理失败: {e}",
        "document_id": doc.id,
        "filename": filename,
        "status": doc_status,
    }


@router.get("/documents", summary="文档列表")
async def list_documents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    分页获取知识库文档列表，支持按文件名搜索。
    仅管理员可访问。
    """
    return await document_service.list_documents(db, page, page_size, search)


@router.delete("/documents/{doc_id}", summary="删除文档")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    删除指定文档及其关联的向量数据。
    仅管理员可操作。
    """
    success = await document_service.delete_document(db, doc_id)
    if not success:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )
    return {"message": "删除成功"}


@router.get("/stats", summary="知识库统计")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    获取知识库统计信息：文档数量、片段数、处理状态等。
    仅管理员可访问。
    """
    return await document_service.get_knowledge_stats(db)
