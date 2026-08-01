"""
pytest 共享配置和 fixtures
使用内存数据库，不影响真实数据
"""
import os
import sys

# 在导入 app 之前设置测试环境变量
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"
os.environ["CHROMA_PERSIST_DIR"] = "./test_chroma_data"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.core.database import async_engine, sync_engine, Base
from app.core.security import hash_password
from app.models.user import User


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """测试套件启动前：建表 + 创建目录 + 创建管理员"""
    # 确保目录存在
    os.makedirs("./test_uploads", exist_ok=True)
    os.makedirs("./test_chroma_data", exist_ok=True)

    # 用同步引擎建表
    Base.metadata.create_all(bind=sync_engine)

    # 创建默认管理员
    from sqlalchemy.orm import Session
    with Session(sync_engine) as db:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            db.add(User(
                username="admin",
                password_hash=hash_password("123456"),
                role="admin",
            ))
            db.commit()

    yield
    Base.metadata.drop_all(bind=sync_engine)


@pytest_asyncio.fixture
async def client():
    """异步 HTTP 测试客户端"""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client):
    """获取管理员 Token"""
    response = await client.post("/api/auth/login", json={
        "username": "admin", "password": "123456"
    })
    return response.json()["token"]


@pytest_asyncio.fixture
async def user_token(client):
    """
    获取普通用户 Token
    每次都会重新创建用户，保证状态一致
    """
    # 先尝试直接登录（如果用户已存在且密码未改）
    resp = await client.post("/api/auth/login", json={
        "username": "testuser", "password": "test123456"
    })
    if resp.status_code == 200:
        return resp.json()["token"]

    # 登录失败则重新注册
    await client.post("/api/auth/register", json={
        "username": "testuser", "password": "test123456"
    })
    resp = await client.post("/api/auth/login", json={
        "username": "testuser", "password": "test123456"
    })
    return resp.json()["token"]
