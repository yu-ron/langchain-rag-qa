"""
用户认证服务
处理注册、登录、密码修改等业务逻辑
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


async def create_user(
    db: AsyncSession, username: str, password: str, role: str = "user"
) -> User | None:
    """
    注册新用户
    返回创建的 User 对象，如果用户名已存在则返回 None
    """
    # 检查用户名是否已被占用
    result = await db.execute(select(User).where(User.username == username))
    existing = result.scalar_one_or_none()
    if existing:
        return None  # 用户名已存在

    # 创建新用户，密码用 bcrypt 加密后存储
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.flush()  # 立即写入以获取自动生成的 ID
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> dict | None:
    """
    用户登录验证
    验证成功返回 {"token": "jwt_token_string"}
    验证失败返回 None
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    # 用户不存在或密码错误
    if not user or not verify_password(password, user.password_hash):
        return None

    # 生成 JWT Token，里面存放用户名和角色
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "token": token,
        "username": user.username,
        "role": user.role,
        "user_id": user.id,
    }


async def change_user_password(
    db: AsyncSession, user_id: int, old_password: str, new_password: str
) -> bool:
    """
    修改密码
    需要先验证旧密码是否正确
    返回 True 表示修改成功，False 表示旧密码错误
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    # 验证旧密码
    if not verify_password(old_password, user.password_hash):
        return False

    # 更新为新密码
    user.password_hash = hash_password(new_password)
    await db.flush()
    return True


async def get_user_info(db: AsyncSession, user_id: int) -> dict | None:
    """获取用户基本信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
