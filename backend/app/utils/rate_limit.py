"""
API 限流中间件
防止恶意请求耗尽 API 额度
使用简单的内存计数（单机部署够用）
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    """
    滑动窗口限流器

    通俗理解：
    就像地铁站闸机——每分钟只能通过一定人数
    超出的请求会被拒绝，防止一个人占满所有资源
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        参数：
        - max_requests: 窗口内最大请求数
        - window_seconds: 时间窗口（秒）
        默认：每分钟最多 60 次请求
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list] = defaultdict(list)

    def _clean_old(self, key: str) -> None:
        """清理窗口外的旧记录"""
        now = time.time()
        cutoff = now - self.window_seconds
        self.requests[key] = [
            t for t in self.requests[key] if t > cutoff
        ]

    def is_allowed(self, key: str) -> bool:
        """检查请求是否被允许"""
        self._clean_old(key)
        return len(self.requests[key]) < self.max_requests

    def record(self, key: str) -> None:
        """记录一次请求"""
        self.requests[key].append(time.time())


# 全局限流器实例
limiter = RateLimiter(max_requests=120, window_seconds=60)  # 每分钟120次


async def rate_limit_middleware(request: Request):
    """
    FastAPI 中间件：对 API 请求进行限流
    使用客户端 IP 作为限流标识
    """
    # 只对 /api/ 路径限流，静态资源不限
    if not request.url.path.startswith("/api/"):
        return

    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{request.url.path}"

    if not limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求太频繁，请稍后再试",
        )

    limiter.record(key)
