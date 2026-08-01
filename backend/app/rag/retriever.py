"""
混合检索器
结合语义检索（向量）和关键词检索（BM25）提升搜索质量
"""
from typing import List
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.rag.vector_store import search_similar
from app.core.config import RETRIEVAL_TOP_K


# 全局变量：存储所有 chunk 用于 BM25 关键词检索
_bm25_corpus: List[str] = []
_bm25_index: BM25Okapi | None = None
_bm25_docs: List[Document] = []


def _tokenize(text: str) -> List[str]:
    """
    简单的中文分词
    对中文按字符切分，英文按空格切分
    """
    tokens = []
    current_word = ""
    for char in text:
        if char.isalpha() and ord(char) < 128:
            # 英文字母，累积
            current_word += char.lower()
        else:
            if current_word:
                tokens.append(current_word)
                current_word = ""
            if not char.isspace():
                tokens.append(char)
    if current_word:
        tokens.append(current_word)
    return tokens


def build_bm25_index(documents: List[Document]) -> None:
    """
    构建 BM25 关键词检索索引
    BM25 是经典的关键词匹配算法，类似搜索引擎的"精确匹配"
    """
    global _bm25_corpus, _bm25_index, _bm25_docs
    if not documents:
        return

    _bm25_docs = documents
    _bm25_corpus = [_tokenize(doc.page_content) for doc in documents]
    _bm25_index = BM25Okapi(_bm25_corpus)


def bm25_search(query: str, top_k: int = RETRIEVAL_TOP_K) -> List[Document]:
    """
    关键词检索：找到包含用户问题中关键词最多的片段
    例如用户搜 "iPhone 15 电池" → 找到所有提到这些词的片段
    """
    global _bm25_index, _bm25_docs
    if _bm25_index is None or not _bm25_docs:
        return []

    tokenized_query = _tokenize(query)
    scores = _bm25_index.get_scores(tokenized_query)

    # 按分数排序，取 top_k
    indexed_scores = list(enumerate(scores))
    indexed_scores.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in indexed_scores[:top_k]:
        if score > 0:
            doc = _bm25_docs[idx]
            results.append(Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "bm25_score": float(score)},
            ))
    return results


def hybrid_search(query: str, top_k: int = RETRIEVAL_TOP_K) -> List[Document]:
    """
    混合检索：融合语义检索和关键词检索的结果

    为什么要混合？
    - 语义检索：能理解 "拍照怎么样" ≈ "摄像头参数"，但可能漏掉精确的"iPhone 15"
    - 关键词检索：能精确匹配"iPhone 15"，但不懂"拍照"和"摄像头"的关系
    - 两者互补，融合后效果更好

    使用 RRF（倒数排名融合）算法合并：
    每个文档的最终分数 = 1/(k+向量排名) + 1/(k+关键词排名)
    """
    # 1. 语义检索
    vector_docs = search_similar(query, top_k)

    # 2. 关键词检索
    bm25_docs = bm25_search(query, top_k)

    # 3. 如果有任一种检索为空，直接返回另一种
    if not bm25_docs:
        return vector_docs
    if not vector_docs:
        return bm25_docs

    # 4. RRF 融合
    k = 60  # RRF 常数
    scores = {}

    # 向量检索排名
    for rank, doc in enumerate(vector_docs, start=1):
        content = doc.page_content
        scores[content] = scores.get(content, 0) + 1.0 / (k + rank)

    # 关键词检索排名
    for rank, doc in enumerate(bm25_docs, start=1):
        content = doc.page_content
        scores[content] = scores.get(content, 0) + 1.0 / (k + rank)

    # 按融合分数排序
    sorted_contents = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 5. 去重返回
    seen = set()
    results = []
    for content, _ in sorted_contents:
        if content not in seen:
            seen.add(content)
            results.append(Document(page_content=content))
            if len(results) >= top_k:
                break

    return results
