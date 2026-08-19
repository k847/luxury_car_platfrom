# =============================================================
# 段功能：审计中间件（M1 基础设施）
# 说明：对后台写操作（/admin/* 且非 GET）做操作审计，写入 audit_logs 表。
#       记录：操作人（从 JWT 解析）、动作（METHOD+PATH）、模块、来源 IP。
#       采用 BaseHTTPMiddleware，在请求进入路由前解析 token 并挂到 request.state，
#       响应后落库。M1 阶段仅记录元数据，detail（变更前后）在 M4 各接口补充。
# =============================================================

import json
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计中间件：自动记录后台管理端的操作行为，满足合规留痕需求。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 仅审计后台写操作；读操作（GET）和公开接口不记
        # 后台路由前缀为 /api/v1/admin（对齐 §8），M2 起已从 /admin 迁移至此
        is_admin_write = request.url.path.startswith("/api/v1/admin") and request.method != "GET"

        # 尝试从 Bearer token 解析操作人（失败不影响主流程，记 NULL）
        operator_id = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                payload = decode_token(auth[len("Bearer "):])
                operator_id = int(payload.get("sub")) if payload.get("sub") else None
            except Exception:
                operator_id = None

        response = await call_next(request)

        # 异步写审计：用独立会话，避免占用请求会话
        if is_admin_write and response.status_code < 500:
            try:
                db: Session = SessionLocal()
                db.add(
                    AuditLog(
                        admin_user_id=operator_id,
                        action=f"{request.method} {request.url.path}",
                        module="admin",
                        target=request.url.path,
                        detail=json.dumps({"query": str(request.url.query)}, ensure_ascii=False),
                        ip=request.client.host if request.client else None,
                    )
                )
                db.commit()
                db.close()
            except Exception:
                # 审计失败不影响主业务
                pass

        return response
