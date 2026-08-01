"""
向量存储操作
使用 ChromaDB 存储和检索知识库片段的向量
"""
import os
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.rag.embeddings import get_embeddings
from app.core.config import CHROMA_PERSIST_DIR, RETRIEVAL_TOP_K


# 全局向量存储实例（懒加载）
_vector_store: Optional[Chroma] = None


def _get_vector_store() -> Chroma:
    """
    获取 ChromaDB 向量存储实例
    数据持久化到本地文件夹，重启后仍然存在
    """
    global _vector_store
    if _vector_store is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _vector_store = Chroma(
            collection_name="knowledge_base",
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_PERSIST_DIR,
        )
    return _vector_store


def add_documents(chunks: List[Document]) -> None:
    """
    把文档片段添加到向量库

    过程：
    1. 每个 chunk 的内容 → 调用嵌入模型 → 1024维向量
    2. 向量 + 原文 + 元数据 → 存入 ChromaDB
    """
    # 过滤掉空内容或纯空白的片段，避免 Embedding API 报错
    valid_chunks = [
        chunk for chunk in chunks
        if chunk.page_content and chunk.page_content.strip()
    ]
    if not valid_chunks:
        return

    store = _get_vector_store()
    # 给每个 chunk 生成唯一 ID（防止重复添加）
    ids = [f"chunk_{chunk.metadata.get('source', 'unknown')}_{chunk.metadata.get('chunk_index', i)}"
           for i, chunk in enumerate(valid_chunks)]
    store.add_documents(valid_chunks, ids=ids)


def search_similar(query: str, top_k: int = RETRIEVAL_TOP_K) -> List[Document]:
    """
    语义检索：根据用户问题，找到最相关的知识库片段

    比如用户问 "这个手机电池能用多久"
    → 系统找到包含"电池容量 5000mAh"、"续航约2天"等片段
    """
    store = _get_vector_store()
    return store.similarity_search(query, k=top_k)


def delete_document_chunks(source_path: str) -> int:
    """
    删除指定文档的所有片段
    返回删除的片段数量
    """
    store = _get_vector_store()
    collection = store._collection
    # 查找所有属于该文档的片段 ID
    results = collection.get(where={"source": source_path})
    if results and results["ids"]:
        collection.delete(ids=results["ids"])
        return len(results["ids"])
    return 0


def get_all_documents() -> List[Document]:
    """获取向量库中的所有文档片段（用于重建 BM25 索引）"""
    store = _get_vector_store()
    collection = store._collection
    results = collection.get()
    docs = []
    if results and results["documents"]:
        for i, content in enumerate(results["documents"]):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            docs.append(Document(page_content=content, metadata=metadata))
    return docs


def get_collection_stats() -> dict:
    """获取知识库统计信息"""
    store = _get_vector_store()
    collection = store._collection
    return {
        "total_chunks": collection.count(),
    }
