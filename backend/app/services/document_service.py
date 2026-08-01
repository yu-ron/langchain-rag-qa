"""
文档处理服务
处理文档上传、解析、向量化的完整流程
"""
import os
import shutil
import uuid
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Document, User
from app.rag.loader import load_document
from app.rag.splitter import split_documents
from app.rag.vector_store import add_documents, delete_document_chunks, get_collection_stats, get_all_documents
from app.rag.retriever import build_bm25_index
from app.core.config import UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS


def validate_upload(filename: str, file_size: int) -> Optional[str]:
    """
    验证上传文件是否合法
    返回错误信息，如果合法则返回 None
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"不支持的文件类型: {ext}，支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
    if file_size > MAX_UPLOAD_SIZE:
        return f"文件过大（{file_size / 1024 / 1024:.1f}MB），最大允许 {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
    return None


async def save_upload_file(filename: str, content: bytes) -> str:
    """
    把上传的文件保存到本地，返回存储路径
    文件名加随机 UUID 防止重名覆盖
    """
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path


async def process_document(
    doc_id: int,
    file_path: str,
    filename: str,
) -> None:
    """
    处理文档：加载 → 切分 → 向量化 → 存储
    这是一个耗时操作，放在后台执行

    自己创建独立的数据库会话，不依赖请求中的会话
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            # 1. 加载文档内容
            docs = await load_document(file_path, filename)
            if not docs or all(not d.page_content.strip() for d in docs):
                raise ValueError("文档内容为空，无法提取文字")

            # 2. 切分成小块
            chunks = split_documents(docs)
            if not chunks:
                raise ValueError("文档切分后无有效片段")

            # 3. 向量化并存入 ChromaDB
            add_documents(chunks)

            # 4. 重建 BM25 关键词索引
            all_docs = get_all_documents()
            build_bm25_index(all_docs)

            # 5. 更新数据库记录状态
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "completed"
                doc.chunk_count = len(chunks)
                await db.commit()

        except Exception as e:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                await db.commit()
            raise


async def create_document_record(
    db: AsyncSession,
    filename: str,
    file_type: str,
    file_size: int,
    file_path: str,
    uploaded_by: int,
) -> Document:
    """
    在数据库中创建文档记录，状态初始为 "processing"
    """
    doc = Document(
        filename=filename,
        file_type=file_type.replace(".", ""),  # 去掉点号，如 ".pdf" → "pdf"
        file_size=file_size,
        file_path=file_path,
        status="processing",
        uploaded_by=uploaded_by,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def list_documents(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
) -> dict:
    """
    分页获取文档列表
    支持按文件名搜索
    """
    query = select(Document)

    if search:
        query = query.where(Document.filename.contains(search))

    # 按创建时间倒序（最新上传的在前）
    query = query.order_by(desc(Document.created_at))

    # 计算总数
    count_query = select(Document)
    if search:
        count_query = count_query.where(Document.filename.contains(search))
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "error_message": d.error_message,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in documents
        ],
    }


async def delete_document(db: AsyncSession, doc_id: int) -> bool:
    """
    删除文档（数据库记录 + 向量片段 + 物理文件）
    返回 True 表示删除成功
    """
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        return False

    # 1. 删除向量库中的片段
    delete_document_chunks(doc.file_path)

    # 2. 删除物理文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # 3. 删除数据库记录
    await db.delete(doc)
    await db.commit()
    return True


async def get_knowledge_stats(db: AsyncSession) -> dict:
    """获取知识库整体统计"""
    # 数据库中的文档统计
    result = await db.execute(select(Document))
    all_docs = result.scalars().all()

    completed = sum(1 for d in all_docs if d.status == "completed")
    processing = sum(1 for d in all_docs if d.status == "processing")
    failed = sum(1 for d in all_docs if d.status == "failed")
    total_chunks = sum(d.chunk_count for d in all_docs if d.status == "completed")

    # 向量库统计
    vector_stats = get_collection_stats()

    return {
        "document_count": len(all_docs),
        "completed": completed,
        "processing": processing,
        "failed": failed,
        "total_chunks": total_chunks,
        "vector_chunks": vector_stats["total_chunks"],
        "total_size": sum(d.file_size for d in all_docs),
    }
