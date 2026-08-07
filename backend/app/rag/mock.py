"""
Mock 模块 — 压测用
当环境变量 MOCK_LLM=true 时，用假实现替代真实的百炼 API 调用

目的：
- 压测时不花钱调 API
- 避免触发百炼的速率限制
- 测的是系统本身的承载能力，不是外部 API 的速度
"""
import random
from typing import List
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun


class MockEmbeddings(Embeddings):
    """
    假嵌入模型
    返回随机 1024 维向量，速度极快（微秒级）
    """

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量把文本转成"假向量"——1024 个随机小数"""
        return [[random.random() * 2 - 1 for _ in range(1024)] for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        """单个查询转成假向量"""
        return [random.random() * 2 - 1 for _ in range(1024)]


class MockLLM(BaseChatModel):
    """
    假大模型
    不管问什么都返回一句固定回答，速度极快（毫秒级）

    为什么要继承 BaseChatModel？
    因为 LangChain 的 StrOutputParser 需要 ChatModel 的接口。
    继承 BaseChatModel 后，LangChain 的链式调用就能直接用。
    """

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult:
        """生成假回答"""
        answer = (
            "根据知识库内容，该商品具备良好的性能和品质。"
            "具体参数和价格请参考商品详情页。 [来源1]"
        )
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=answer))]
        )

    @property
    def _llm_type(self) -> str:
        return "mock-llm"
