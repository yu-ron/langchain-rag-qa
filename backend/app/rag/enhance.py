"""
RAG 增强模块
包含三个企业级优化：
1. Query Rewriting 查询重写 — 结合历史对话，把模糊问题改写成独立完整的查询
2. Reranker 重排序精排 — LLM 对候选文档逐条打分，取最相关的
3. （配合 RAGAS 评估脚本使用）
"""
import json
import re
from typing import List
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from app.rag.chain import _get_llm


# ── 1. Query Rewriting 查询重写 ─────────────────────

QUERY_REWRITE_PROMPT = """你是一个查询改写助手。用户在对话中提出的问题可能包含指代词（如"它"、"这个"、"那款"）或省略了上下文。

请根据对话历史，把用户当前的问题改写成一个**独立、完整、无需上下文就能理解**的查询。

规则：
1. 把指代词替换成具体内容（如"它的价格" → "iPhone 15 的价格"）
2. 补充省略的信息
3. 保持原意，不要添加用户没问的内容
4. 如果问题本身已经很完整，直接原样输出
5. 只输出改写后的查询，不要任何解释

## 对话历史
{history}

## 当前问题
{question}

## 改写结果："""


async def rewrite_query(question: str, history: List[dict]) -> str:
    """
    查询重写：结合历史对话改写模糊问题

    示例：
      历史：用户问"iPhone 15 的电池怎么样？"
      当前："那充电速度呢？"
      改写后："iPhone 15 的充电速度怎么样？"

    如果历史为空或问题已完整，直接返回原问题。
    """
    if not history:
        return question

    # 简单判断：问题很短（<15字）且可能包含指代词时才改写
    if len(question) >= 15:
        return question

    # 检查是否包含指代词
    has_reference = any(word in question for word in
                        ["它", "这个", "那个", "这款", "那款", "这", "那", "其", "该"])

    if not has_reference:
        return question

    try:
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}：{m['content'][:100]}"
            for m in history[-4:]
        ])

        llm = _get_llm(streaming=False)
        response = await llm.ainvoke([
            SystemMessage(content="你是查询改写助手，只输出改写后的查询文本。"),
            HumanMessage(content=QUERY_REWRITE_PROMPT.format(
                history=history_text,
                question=question,
            )),
        ])

        rewritten = response.content.strip()
        # 清理可能带上的引号、换行
        rewritten = rewritten.strip('"\'。.，, \n')
        if rewritten and len(rewritten) >= 3:
            return rewritten
    except Exception:
        pass

    return question


# ── 2. Reranker 重排序精排 ──────────────────────────

RERANK_PROMPT = """你是检索结果精排助手。根据用户查询，对以下候选文档片段按相关性打分（0-10分，10分最相关）。

评分标准：
- 10分：直接回答了查询的核心内容
- 7-9分：高度相关，包含查询关键信息
- 4-6分：部分相关，涉及相关主题但不是核心答案
- 1-3分：弱相关，只提到个别关键词
- 0分：完全无关

只输出 JSON 数组格式，例如：[8, 3, 9, 1]
不要输出其他任何内容。

## 用户查询
{query}

## 候选文档
{documents}

## 评分结果（JSON数组）："""


async def rerank_documents(query: str, documents: List[Document]) -> List[Document]:
    """
    Reranker 精排：用 LLM 对候选文档逐条打分，按分数重排序

    流程：
    1. 混合检索粗召回 Top-K（如 12 条）
    2. LLM 对 12 条逐条打相关性分数
    3. 按分数降序取 Top-N（如 5 条）送给生成模型
    """
    if len(documents) <= 3:
        # 候选太少不值得精排
        return documents

    try:
        # 构建候选文档列表
        doc_texts = []
        for i, doc in enumerate(documents):
            snippet = doc.page_content[:200].replace("\n", " ")
            doc_texts.append(f"[{i}] {snippet}")

        llm = _get_llm(streaming=False)
        response = await llm.ainvoke([
            SystemMessage(content="你是精排助手，只输出 JSON 数组。"),
            HumanMessage(content=RERANK_PROMPT.format(
                query=query,
                documents="\n".join(doc_texts),
            )),
        ])

        content = response.content.strip()
        # 提取 JSON 数组
        match = re.search(r'\[[\d,\s]+\]', content)
        if not match:
            return documents

        scores = json.loads(match.group())
        if len(scores) != len(documents):
            return documents

        # 按分数排序
        scored = list(zip(scores, documents))
        scored.sort(key=lambda x: x[0], reverse=True)

        # 过滤掉 0 分文档，取前 5 条
        reranked = [doc for score, doc in scored if score > 0][:5]
        if len(reranked) < 3:
            # 如果精排后太少，保留原始前 5 条
            return documents[:5]
        return reranked

    except Exception:
        return documents
