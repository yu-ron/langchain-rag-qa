"""
LangChain RAG 问答链
把检索和生成串成一个完整的问答流程
"""
import os
from typing import List, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
)
from app.rag.retriever import hybrid_search


# ── Prompt 模板 ─────────────────────────────────────
# 这是给大模型的"说明书"，告诉它怎么回答、怎么引用来源

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的电商客服助手，名字叫"小R"，由阿里云通义千问大模型驱动。

## 你需要区分两类问题

### A 类：商品相关问题（价格、参数、功能、对比、库存、使用方法、售后政策等）
回答时：
- **必须严格基于知识库内容**，不要编造商品信息
- 在句末用 [来源N] 标注引用的知识库内容
- 提取具体数据（价格、参数、规格等）
- 回答要结构化、清晰易读

### B 类：一般性问题（闲聊、自我介绍、打招呼等）
回答时：
- 直接自然地回答，**不需要引用知识库**
- 你是谁、你会什么、今天天气、讲个笑话、你好等——这些都算 B 类

### 知识库中有内容但与问题不匹配时
- 如果是 A 类问题：诚实告知用户该问题暂无相关信息，并建议联系人工客服
- 如果是 B 类问题：直接回答，不用管知识库

## 知识库内容：
{context}

## 对话历史：
{history}
"""),
    ("human", "{question}"),
])


def _get_llm(streaming: bool = False) -> ChatOpenAI:
    """获取 LLM 实例（支持 Mock 模式用于压测）"""
    if os.getenv("MOCK_LLM", "").lower() == "true":
        from app.rag.mock import MockLLM
        return MockLLM()

    os.environ.setdefault("OPENAI_API_KEY", DASHSCOPE_API_KEY)
    os.environ.setdefault("OPENAI_BASE_URL", DASHSCOPE_BASE_URL)

    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        streaming=streaming,
    )


def _format_context(docs: List[Document]) -> str:
    """
    把检索到的知识库片段格式化成 Prompt 用的文本
    格式：[来源1] 内容...\n[来源2] 内容...
    """
    if not docs:
        return "（知识库中暂无相关内容）"

    parts = []
    for i, doc in enumerate(docs, start=1):
        content = doc.page_content.strip()
        parts.append(f"[来源{i}] {content}")
    return "\n\n".join(parts)


def _format_history(history: List[dict]) -> str:
    """
    把对话历史格式化成文本
    格式：用户：xxx\n助手：xxx
    """
    if not history:
        return "（无历史对话）"

    parts = []
    for msg in history[-6:]:  # 只取最近6条，避免太长
        role = "用户" if msg["role"] == "user" else "助手"
        parts.append(f"{role}：{msg['content']}")
    return "\n".join(parts)


async def ask_stream(
    question: str,
    history: List[dict] | None = None,
) -> AsyncIterator[dict]:
    """
    流式问答：逐步输出回答内容

    流程：
    1. 从向量库检索相关片段
    2. 构建 Prompt（知识库 + 历史 + 问题）
    3. 调用大模型逐字生成回答
    4. 实时推送给前端

    Yields:
        {"type": "content", "data": "文字片段"}  # 回答内容
        {"type": "citations", "data": [...]}     # 引用来源
    """
    if history is None:
        history = []

    # 1. 混合检索（语义 + 关键词）
    retrieved_docs = hybrid_search(question)

    # 2. 构建上下文
    context = _format_context(retrieved_docs)
    history_text = _format_history(history)

    # 3. 流式调用 LLM
    llm = _get_llm(streaming=True)
    chain = RAG_PROMPT | llm | StrOutputParser()

    full_answer = ""
    async for chunk in chain.astream({
        "context": context,
        "history": history_text,
        "question": question,
    }):
        full_answer += chunk
        yield {"type": "content", "data": chunk}

    # 4. 返回引用来源
    citations = []
    for i, doc in enumerate(retrieved_docs, start=1):
        citations.append({
            "index": i,
            "content": doc.page_content,
            "metadata": doc.metadata,
        })

    yield {"type": "citations", "data": citations}
