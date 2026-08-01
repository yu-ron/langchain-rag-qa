"""
FastAPI 依赖注入工具
提供认证校验、权限检查等可复用的依赖函数
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
) -> User:
    """
    从请求头解析 JWT Token，获取当前登录的用户对象
    如果 Token 缺失或无效，返回 401 错误

    用法：在路由中注入 user: User = Depends(get_current_user)
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Authorization 头的格式是 "Bearer <token>"
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证格式错误，请使用 Bearer Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 解析 Token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
        )

    # 从数据库查用户
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return user


async def get_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    仅允许管理员访问
    如果当前用户不是 admin 角色，返回 403 错误

    用法：user: User = Depends(get_admin_user)
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问此功能",
        )
    return user
