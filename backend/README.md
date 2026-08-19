# 后端服务（FastAPI）· M1 基础框架

> 本目录为豪华车聚合选车平台后端，技术栈：FastAPI + SQLAlchemy 2.x + MySQL 8 + PyJWT + Alembic。

## 已完成（M1）
- 配置中心 `app/core/config.py`（环境变量读取）
- 数据库引擎与会话 `app/core/database.py`
- 安全工具 `app/core/security.py`（密码哈希 + JWT 签发/校验）
- 鉴权依赖 `app/core/deps.py`（`get_current_user` + RBAC `require_permission`）
- ORM 模型 `app/models.py`（29 张表，对应《数据库设计文档》）
- 校验层 `app/schemas.py`（统一响应信封 + 鉴权结构）
- 接口 `app/api/routes/auth.py`：`POST /auth/login`、`POST /auth/refresh`、`GET /auth/me`
- 中间件：审计 `app/middleware/audit.py`、限流 `app/middleware/rate_limit.py`
- 应用入口 `app/main.py`（CORS + 中间件装配 + 健康检查 `/health`）
- 迁移：`alembic`（初始迁移建全部表）+ `seed.py`（开发种子账号）

## 本地运行
```bash
# 1. 建虚拟环境并安装依赖
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env   # 然后按本机修改数据库连接等

# 3. 建表（二选一）
#   方式 A：Alembic 迁移（推荐，可演进）
alembic revision --autogenerate -m "init"   # 后续增量；首次已带 0001_initial
alembic upgrade head
#   方式 B：直接 seed（create_all）
python seed.py

# 4. 写入开发账号（admin / admin123）
python seed.py

# 5. 启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问 http://localhost:8000/docs 查看 Swagger 接口文档。
健康检查：http://localhost:8000/health

## 说明
- 限流中间件当前为进程内存实现，生产需换 Redis（见 `app/middleware/rate_limit.py` 注释）。
- `seed.py` 默认口令 `admin / admin123` 仅用于本地联调，生产必须修改。
- `model_dealer` / `role_permissions` 两表在 ORM 中补齐了 DDL 遗漏的 `id` 主键（见 `app/models.py` 注释）。
