"""
FastAPI 主入口文件
开发模式：python main.py
生产模式：uvicorn main:app --host 0.0.0.0 --port 8000
"""
import os
import sys

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import DEBUG, SERVER_PORT, UPLOAD_DIR, ADMIN_USERNAME, ADMIN_PASSWORD
from app.core.database import async_engine, Base, sync_engine, SyncSessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理：
    - 启动时：创建目录、建表、初始化管理员账号
    - 关闭时：清理资源
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("chroma_data", exist_ok=True)

    # 用同步引擎创建数据库表（避免 greenlet 问题）
    Base.metadata.create_all(bind=sync_engine)

    # 初始化管理员账号
    from app.models.user import User
    from app.core.security import hash_password
    db = SyncSessionLocal()
    try:
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not existing:
            db.add(User(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
                role="admin",
            ))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    # 重建 BM25 关键词检索索引
    try:
        from app.rag.vector_store import get_all_documents
        from app.rag.retriever import build_bm25_index
        all_docs = get_all_documents()
        if all_docs:
            build_bm25_index(all_docs)
    except Exception:
        pass

    print(f"[OK] Service running on port {SERVER_PORT}")
    yield
    await async_engine.dispose()


# ── FastAPI 应用 ──────────────────────────────────────
app = FastAPI(
    title="LangChain RAG 知识库问答系统",
    description="基于 LangChain 框架的企业级 RAG 知识库问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS（生产环境添加 Render 域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境可以先放开
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 路由 ──────────────────────────────────────────
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


@app.get("/api/health", tags=["系统"])
async def health_check():
    return {"status": "ok"}


# ── 前端静态文件 ──────────────────────────────────────
# 生产模式下，FastAPI 直接托管前端页面（开发时用 npm run dev）
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(FRONTEND_DIR):
    # 挂载静态资源（JS、CSS、图片等）
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # SPA 回退：所有非 API 路径都返回 index.html，Vue Router 处理路由
    @app.get("/{full_path:path}", tags=["前端"])
    async def serve_frontend(full_path: str):
        """所有非 API 请求返回 Vue 前端页面"""
        # 已经是 API 路径的跳过
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # SPA 回退
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "前端文件不存在，请先构建：cd frontend && npm run build"}


# ── 直接运行入口 ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVER_PORT,
        reload=DEBUG,
    )
