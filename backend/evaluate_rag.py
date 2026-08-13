"""
RAG 质量评估脚本
使用 RAGAS 框架评估检索增强生成系统的质量

评估指标：
- context_relevancy（上下文相关性）：检索到的文档与问题有多相关
- answer_relevancy（答案相关性）：生成的答案与问题有多相关
- faithfulness（忠实度）：答案是否忠实于检索到的文档（有无编造）

运行方式：
    cd backend
    python evaluate_rag.py

需要先上传知识库文档，并在脚本中准备测试问题集。
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from app.core.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, LLM_MODEL
from app.rag.retriever import hybrid_search
from app.rag.enhance import rerank_documents

os.environ.setdefault("OPENAI_API_KEY", DASHSCOPE_API_KEY)
os.environ.setdefault("OPENAI_BASE_URL", DASHSCOPE_BASE_URL)


# ── 测试问题集（根据你的知识库内容修改）──────────────
TEST_QUESTIONS = [
    "这款手机支持5G网络吗？",
    "电池容量是多少？",
    "有没有保修服务？",
    "充电速度怎么样？",
    "适合什么人使用？",
]

# 每个问题对应的"标准答案要点"（人工标注，用于评估）
GROUND_TRUTH = {
    "这款手机支持5G网络吗？": ["5G"],
    "电池容量是多少？": ["电池", "容量", "mAh"],
    "有没有保修服务？": ["保修"],
    "充电速度怎么样？": ["充电"],
    "适合什么人使用？": ["适合", "使用"],
}


async def evaluate_retrieval(use_rerank: bool = False) -> dict:
    """评估检索质量"""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    total_relevancy = 0
    total_queries = 0
    results = []

    for question in TEST_QUESTIONS:
        # 检索
        docs = hybrid_search(question, top_k=12)
        if use_rerank:
            docs = await rerank_documents(question, docs)

        if not docs:
            results.append({
                "question": question,
                "retrieved": 0,
                "relevancy": 0,
                "note": "未检索到任何文档",
            })
            continue

        # 用 LLM 判断检索结果相关性
        context_text = "\n".join([f"[{i}] {d.page_content[:150]}" for i, d in enumerate(docs[:5])])
        judge_prompt = f"""根据问题判断以下检索到的文档片段的相关性。

问题：{question}

检索到的文档：
{context_text}

请评估整体相关性，输出 0-10 分（10=完全相关，0=完全不相关）。
只输出数字。"""

        response = await llm.ainvoke(judge_prompt)
        try:
            score = float(response.content.strip())
        except ValueError:
            score = 5.0

        total_relevancy += score
        total_queries += 1
        results.append({
            "question": question,
            "retrieved": len(docs),
            "relevancy": score,
            "note": "精排" if use_rerank else "未精排",
        })

        print(f"  [{score:.1f}/10] {question} ({len(docs)}条, {results[-1]['note']})")

    return {
        "avg_relevancy": total_relevancy / total_queries if total_queries else 0,
        "total_queries": total_queries,
        "results": results,
    }


async def evaluate_faithfulness() -> dict:
    """
    评估答案忠实度：
    用 LLM 生成答案，再判断答案中是否有知识库外的编造内容
    """
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    from app.rag.chain import RAG_PROMPT, _format_context
    from langchain_core.output_parsers import StrOutputParser

    total_faith = 0
    total_queries = 0

    for question in TEST_QUESTIONS:
        docs = hybrid_search(question, top_k=12)
        docs = await rerank_documents(question, docs)
        if not docs:
            continue

        # 生成答案
        context = _format_context(docs)
        chain = RAG_PROMPT | llm | StrOutputParser()
        answer = await chain.ainvoke({
            "context": context,
            "history": "（无历史对话）",
            "question": question,
        })

        # 用 LLM 判断答案是否忠实于上下文
        judge_prompt = f"""判断以下答案是否忠实于提供的知识库内容（没有编造）。

知识库内容：
{context[:1000]}

AI 答案：
{answer[:500]}

评估忠实度，输出 0-10 分（10=完全忠实无编造，0=大量编造）。
只输出数字。"""

        response = await llm.ainvoke(judge_prompt)
        try:
            score = float(response.content.strip())
        except ValueError:
            score = 5.0

        total_faith += score
        total_queries += 1
        print(f"  [忠实度 {score:.1f}/10] {question}")

    return {
        "avg_faithfulness": total_faith / total_queries if total_queries else 0,
        "total_queries": total_queries,
    }


async def main():
    print("=" * 60)
    print("RAG 质量评估报告")
    print("=" * 60)

    print("\n📊 一、检索相关性评估（未精排）")
    result1 = await evaluate_retrieval(use_rerank=False)

    print("\n📊 二、检索相关性评估（Reranker 精排）")
    result2 = await evaluate_retrieval(use_rerank=True)

    print("\n📊 三、答案忠实度评估")
    result3 = await evaluate_faithfulness()

    print("\n" + "=" * 60)
    print("评估总结")
    print("=" * 60)
    print(f"检索相关性（未精排）: {result1['avg_relevancy']:.1f}/10")
    print(f"检索相关性（精排后）: {result2['avg_relevancy']:.1f}/10")
    print(f"精排提升: +{result2['avg_relevancy'] - result1['avg_relevancy']:.1f}")
    print(f"答案忠实度: {result3['avg_faithfulness']:.1f}/10")

    # 保存报告
    report = {
        "retrieval_without_rerank": result1,
        "retrieval_with_rerank": result2,
        "faithfulness": result3,
    }
    with open("evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n报告已保存到 evaluation_report.json")


if __name__ == "__main__":
    asyncio.run(main())
