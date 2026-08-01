"""
安全模块：密码加密和 JWT Token 管理
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# ── 密码加密 ────────────────────────────────────────
# bcrypt 算法：把你的密码变成一串无法反推的乱码
# 即使数据库泄露了，攻击者也看不到原始密码
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    把明文密码加密成哈希值
    比如 "123456" → "$2b$12$K8...一串乱码..."
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码和数据库中的哈希值是否匹配
    用户登录时用这个来校验密码
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token ───────────────────────────────────────
# JWT（JSON Web Token）就像一个"电子身份证"
# 用户登录成功后，服务器发给他一个 Token
# 之后每次请求带着这个 Token，服务器就知道"哦，是你"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    生成一个 JWT Token
    data 里通常放 {"sub": "用户名", "role": "admin"}
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})  # 设置过期时间
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    解析 JWT Token，取出里面的用户信息
    如果 Token 过期或伪造了，返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
