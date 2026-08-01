"""
认证模块 API 路由
处理用户注册、登录、密码修改、用户信息查询
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services import auth_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ── 请求/响应模型（Pydantic 自动校验数据格式） ─────
# FastAPI 会根据这些模型自动生成 API 文档（Swagger）


class RegisterRequest(BaseModel):
    """注册请求体"""
    username: str = Field(
        ..., min_length=3, max_length=50, description="用户名，3-50个字符"
    )
    password: str = Field(
        ..., min_length=6, max_length=100, description="密码，最少6个字符"
    )


class LoginRequest(BaseModel):
    """登录请求体"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class ChangePasswordRequest(BaseModel):
    """修改密码请求体"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(
        ..., min_length=6, max_length=100, description="新密码，最少6个字符"
    )


# ── 路由 ────────────────────────────────────────────


@router.post("/register", summary="用户注册")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    注册新用户。
    所有通过此接口注册的用户角色均为"user"（普通用户），
    管理员只能通过数据库初始化脚本创建。
    """
    user = await auth_service.create_user(db, req.username, req.password, role="user")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被占用",
        )
    return {
        "message": "注册成功",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.post("/login", summary="用户登录")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录，返回 JWT Token。
    前端拿到 Token 后保存到 localStorage，后续请求携带在 Authorization 头中。
    Token 默认 24 小时有效。
    """
    result = await auth_service.authenticate_user(db, req.username, req.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    return result


@router.post("/change-password", summary="修改密码")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    修改当前登录用户的密码。
    需要提供旧密码进行验证，新密码最少6个字符。

    需要登录（携带 Token）。
    """
    success = await auth_service.change_user_password(
        db, current_user.id, req.old_password, req.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )
    return {"message": "密码修改成功"}


@router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的详细信息。
    需要登录（携带 Token）。
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
