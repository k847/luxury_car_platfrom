# =============================================================
# 段功能：本地演示启动器（单端口可交互版，无需 MySQL）
# 说明：用 SQLite 文件库替代 MySQL（开发/演示用），灌入演示数据，
#       自装配演示 app（不沿用 main.py 的 API 欢迎首页，避免抢占前端首页）：
#         - include 全部 API 路由（auth/compare/public/admin + healthz）
#         - 静态托管 frontend/dist（/assets + 首页 / 返回 index.html）
#         - SPA 回退：非 API 路径一律返回 index.html（支持前端路由刷新）
#       浏览器访问 http://127.0.0.1:8000/ 即可完整交互（前台+后台）。
# 用法：python run_demo.py  （生产请用 docker-compose + MySQL + Nginx）
# =============================================================

import os
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy import text as sql_text
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, get_db
from app.core.config import settings
import app.models  # 注册全部 ORM 模型到 Base.metadata（create_all 前必须）


def build_app():
    """组装演示 app：API 路由 + healthz + 静态托管 + SPA 回退。"""
    from app.api.routes.auth import router as auth_router
    from app.api.routes.public import router as public_router
    from app.api.routes.public import compare_router as compare_router
    from app.api.routes.admin import router as admin_router

    demo_app = FastAPI(title="豪华车聚合选车平台 · 本地演示", version="demo")

    # CORS（同源访问其实不需要，保险加上）
    demo_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载全部 API 路由（顺序与 main.py 一致：compare 先于 public，避免路径抢占）
    demo_app.include_router(auth_router)
    demo_app.include_router(compare_router)
    demo_app.include_router(public_router)
    demo_app.include_router(admin_router)

    # 健康检查（与 §13.3 一致）
    @demo_app.get("/api/v1/healthz", tags=["system"])
    def healthz(db: Session = Depends(get_db)):
        checks = {"db": "up", "redis": "skip"}
        ok = True
        try:
            db.execute(sql_text("SELECT 1"))
        except Exception:
            checks["db"] = "down"
            ok = False
        return JSONResponse(status_code=200 if ok else 503,
                            content={"status": "ok" if ok else "degraded", "checks": checks})

    # 静态托管前端构建产物
    dist = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    index = os.path.join(dist, "index.html")
    assets_dir = os.path.join(dist, "assets")
    if os.path.isdir(assets_dir):
        demo_app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    else:
        print(f"警告：未找到前端构建产物 {dist}，请先 cd frontend && npm run build")

    # 首页（返回前端 index.html，替代 main.py 的 API 欢迎 JSON）
    @demo_app.get("/", include_in_schema=False)
    def home():
        return FileResponse(index) if os.path.isfile(index) else {"detail": "index.html 不存在"}

    # SPA 回退：非 /api 路径一律返回 index.html（支持前端路由刷新）
    @demo_app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"code": 40400, "message": "资源不存在", "data": None})
        return FileResponse(index) if os.path.isfile(index) else {"detail": "index.html 不存在"}

    return demo_app, dist


def main():
    # 1) 绑定 SQLite 文件库（演示用；生产走 MySQL）
    db_path = os.path.join(os.path.dirname(__file__), "luxury_car_demo.db")
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    SessionLocal.configure(bind=eng)

    # 2) 灌入账号/权限 + 双语演示数据（幂等；传入 SQLite 会话，避免走全局 MySQL 引擎）
    import seed
    with SessionLocal() as db:
        seed.seed(db=db)            # 超级管理员 admin / admin123
    with SessionLocal() as db:
        seed.seed_demo_data(db=db)  # 品牌/车系/车型/配置器/资讯/经销商/金融参数/线索

    # 3) 组装演示 app 并启动
    demo_app, dist = build_app()
    print("=" * 50)
    print("本地演示服务：http://127.0.0.1:8000/")
    print("  前台（首页/车型/配置器/留资）与后台（/admin，admin/admin123）均可交互")
    print(f"  前端构建产物：{dist}")
    print("=" * 50)
    uvicorn.run(demo_app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
