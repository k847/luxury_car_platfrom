# =============================================================
# 段功能：FastAPI 应用入口（M1 应用装配）
# 说明：在此完成：
#   1. 创建 FastAPI 实例并配置标题/文档
#   2. 注册 CORS 中间件（允许前台域名跨域）
#   3. 注册审计中间件、限流中间件
#   4. 挂载鉴权路由 /auth
#   5. 提供健康检查 /health（供 M5 上线探针使用）
# 后续里程碑在此继续挂载 /brands /models /admin 等路由。
# =============================================================

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.public import router as public_router
from app.api.routes.public import compare_router as compare_router
from app.api.routes.admin import router as admin_router
from app.api.routes.map import router as map_router
from app.core.config import settings
from app.core.database import get_db
from app.middleware.audit import AuditMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# 创建应用实例
app = FastAPI(
    title="豪华车聚合选车平台 · 后台 API",
    description="冠驭名车 REGALIA MOTORS 聚合选车平台后端（M1 基础框架）",
    version="0.1.0",
)

# 1) CORS：允许配置中的前台域名访问接口（凭证模式需显式来源，不能用 *）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2) 审计中间件（记录后台写操作）
app.add_middleware(AuditMiddleware)

# 3) 限流中间件（重点保护 /auth/login）
app.add_middleware(RateLimitMiddleware)


# 健康检查：部署探针与负载均衡探活使用
@app.get("/health", tags=["system"])
def health():
    """
    健康检查接口（轻量存活探针）。
    返回简单 OK，供 Docker/K8s 探针判断服务存活。
    """
    return {"status": "ok"}


# 段功能：M5 健康检查（§13.3，依赖 MySQL/Redis 探活）
# 说明：/api/v1/healthz 供部署探活；MySQL 用轻量 SELECT 1，Redis 用 ping。
#       任一下游不可用则返回 503，探针据此摘除实例。
from fastapi.responses import JSONResponse
from sqlalchemy import text as sql_text

@app.get("/api/v1/healthz", tags=["system"])
def healthz(db: Session = Depends(get_db)):
    """完整健康检查：数据库探活；Redis 可用时探活。下游故障返回 503。"""
    checks: dict = {"db": "up", "redis": "skip"}
    ok = True
    try:
        db.execute(sql_text("SELECT 1"))
    except Exception:
        checks["db"] = "down"
        ok = False
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "up"
    except Exception:
        checks["redis"] = "down"  # Redis 未配置时视为 down（可据 ENV 调整）
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ok" if ok else "degraded", "checks": checks})


# 4) 挂载鉴权路由（前缀 /api/v1/auth，对齐 §8.1）
app.include_router(auth_router)

# 5) 挂载 M3 对比路由（先于 public_router，避免 /models/{id} 抢占 /models/compare）
app.include_router(compare_router)

# 6) 挂载 M2 公共端路由（前缀 /api/v1，对齐 §7.1/7.2/7.3/7.9）
app.include_router(public_router)

# 7) 挂载 M4 后台管理路由（前缀 /api/v1/admin，对齐 §8，require_permission 门控）
app.include_router(admin_router)

# 8) 挂载百度地图路由（前缀 /api/v1/map，经销商门店地图联动）
app.include_router(map_router)


@app.get("/", tags=["system"])
def root():
    """
    根路由：返回服务基本信息。
    """
    return {"service": "luxury-car-api", "version": "0.1.0", "docs": "/docs"}
