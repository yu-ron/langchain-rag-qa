"""
数据库连接管理
使用 SQLAlchemy 操作 SQLite 数据库
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import DATABASE_URL, DATABASE_URL_SYNC

# 异步引擎 — 用于 FastAPI 异步接口
# aiosqlite 是 SQLite 的异步驱动
async_engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要此参数以允许多线程
    echo=False,  # 设为 True 可查看所有 SQL 语句（调试用）
)

# 同步引擎 — 用于数据库初始化和脚本操作
sync_engine = create_engine(
    DATABASE_URL_SYNC,
    connect_args={"check_same_thread": False},
    echo=False,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 同步会话工厂 (sessionmaker 创建的是一个工厂，不是实例)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


# 所有 ORM 模型的基类
class Base(DeclarativeBase):
    pass


# 启用 SQLite 外键约束（默认是关闭的）
@event.listens_for(sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """连接 SQLite 时自动开启外键约束"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def get_db() -> AsyncSession:
    """
    获取数据库会话（异步）
    用法：在 FastAPI 路由中通过 Depends(get_db) 注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_db():
    """获取同步数据库会话，用于脚本和初始化操作"""
    return SyncSessionLocal()
