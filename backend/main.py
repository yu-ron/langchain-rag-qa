"""
FastAPI 主入口文件
启动命令：python main.py  或  uvicorn main:app --reload --port 8000
"""
import os
import sys

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import DEBUG, SERVER_PORT, UPLOAD_DIR
from app.core.database import async_engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理：
    - 启动时：自动创建数据库表、上传目录
    - 关闭时：清理资源
    """
    # 启动：确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # 启动：创建数据库表（如果不存在）
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 启动：重建 BM25 关键词检索索引
    try:
        from app.rag.vector_store import get_all_documents
        from app.rag.retriever import build_bm25_index
        all_docs = get_all_documents()
        if all_docs:
            build_bm25_index(all_docs)
    except Exception:
        pass  # 首次启动可能还没有文档，忽略错误

    print(f"[OK] Backend running: http://localhost:{SERVER_PORT}")
    print(f"[OK] API docs: http://localhost:{SERVER_PORT}/docs")
    print(f"[OK] Upload dir: {UPLOAD_DIR}")

    yield  # 应用运行期间

    # 关闭：清理数据库连接
    await async_engine.dispose()


# 创建 FastAPI 应用实例
app = FastAPI(
    title="LangChain RAG 知识库问答系统",
    description="基于 LangChain 框架的企业级 RAG 知识库问答系统，支持多用户、多会话、知识库管理",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS 跨域配置 ──────────────────────────────────
# 允许前端（Vue dev server on port 5173）访问后端 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vue 开发服务器
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # 备用端口
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)

# ── 注册路由 ────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.chat import router as chat_router
from app.api.session import router as session_router
from app.api.export import router as export_router

app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(export_router)


@app.get("/", summary="根路径", tags=["系统"])
async def root():
    """系统欢迎页，同时也用来健康检查"""
    return {
        "message": "LangChain RAG 知识库问答系统",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health", summary="健康检查", tags=["系统"])
async def health_check():
    """健康检查接口，确认服务运行正常"""
    return {"status": "ok"}


# ── 直接运行入口 ────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVER_PORT,
        reload=DEBUG,  # 开发模式自动重载
    )
