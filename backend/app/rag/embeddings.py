"""
嵌入模型管理
使用阿里云百炼 text-embedding-v4 把文本转成向量

注意：langchain_openai 的 OpenAIEmbeddings 在百炼兼容接口上有兼容性 bug，
所以这里直接用 openai 原生 SDK，外层包装成 LangChain 兼容的接口。
"""
from typing import List
from openai import OpenAI

from langchain_core.embeddings import Embeddings

from app.core.config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    EMBEDDING_MODEL,
)


class BailianEmbeddings(Embeddings):
    """
    百炼嵌入模型包装类
    实现 LangChain 的 Embeddings 接口，底层用 openai 原生 SDK 调用百炼

    通俗理解：
    - "这款手机续航很好" → [0.12, -0.34, 0.56, ...]（1024个数字）
    - "电池能用多久"     → [0.11, -0.32, 0.58, ...]（相似的数字串）
    - 两个向量的"距离"越近，说明意思越接近
    """

    def __init__(self):
        self._client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL,
        )
        self._model = EMBEDDING_MODEL

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量把文档片段转成向量
        输入：["文本1", "文本2", ...]
        输出：[[0.12, -0.34, ...], [0.11, -0.32, ...], ...]
        """
        if not texts:
            return []

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [[] for _ in texts]

        response = self._client.embeddings.create(
            model=self._model,
            input=valid_texts,
        )
        # 按原始顺序返回
        embeddings = [None] * len(valid_texts)
        for i, item in enumerate(response.data):
            embeddings[i] = item.embedding
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        把单个查询文本转成向量
        输入："这款手机怎么样"
        输出：[0.12, -0.34, ...]
        """
        response = self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding


def get_embeddings() -> Embeddings:
    """获取嵌入模型实例（支持 Mock 模式用于压测）"""
    import os
    if os.getenv("MOCK_LLM", "").lower() == "true":
        from app.rag.mock import MockEmbeddings
        return MockEmbeddings()
    return BailianEmbeddings()
