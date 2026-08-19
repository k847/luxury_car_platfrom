# =============================================================
# 段功能：限流中间件（M1 基础设施）
# 说明：对登录等高频接口做基础限流，防止暴力破解 / 刷接口。
#       当前用进程内存令牌桶（按客户端 IP 计数），对应错误码 42900。
#       生产环境应替换为 Redis 集中式限流（《开发技术文档》附录 D 的 REDIS_URL）。
# =============================================================

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 限流配置：每个 IP 在 window 秒内容许 max_requests 次，超出返回 429
RATE_LIMIT_MAX = 60          # 时间窗内最大请求数
RATE_LIMIT_WINDOW = 60       # 时间窗（秒）
# 仅对以下路径做严格限流（登录是重点防护对象；留资再加手机号级 60s 一次限流，见 public.py）
PROTECTED_PATHS = {"/auth/login", "/api/v1/leads/test-drive", "/api/v1/leads/inquiry"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单令牌桶限流中间件（M1 演示实现，单进程内存）。
    """

    def __init__(self, app, max_requests: int = RATE_LIMIT_MAX, window: int = RATE_LIMIT_WINDOW):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        # hits: {ip: [(timestamp, count)...]}；这里用滑动窗口计数
        self.hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 仅对受保护路径限流
        if request.url.path in PROTECTED_PATHS:
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            # 清理窗口外的旧记录
            window_hits = [t for t in self.hits[ip] if now - t < self.window]
            self.hits[ip] = window_hits
            if len(window_hits) >= self.max_requests:
                # 触发限流，返回 429（对应错误码 42900）
                return Response(
                    content='{"code":42900,"message":"请求过于频繁，请稍后再试","data":null}',
                    status_code=429,
                    media_type="application/json",
                )
            self.hits[ip].append(now)

        return await call_next(request)
