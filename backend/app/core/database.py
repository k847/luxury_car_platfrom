# =============================================================
# 段功能：数据库引擎与会话（M1 基础设施）
# 说明：创建 SQLAlchemy 2.x 引擎、会话工厂与声明基类；
#       提供 get_db 依赖，供路由层获取数据库会话。
#       使用 PyMySQL 驱动连接 MySQL 8（utf8mb4）。
# =============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """
    声明基类：所有 ORM 模型均继承此类。
    它承载 SQLAlchemy 的元数据和表映射能力。
    """


# 创建数据库引擎
#   echo=False：生产关闭 SQL 日志；pool_pre_ping：每次取出连接前做健康检查，避免失效连接
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

# 会话工厂：每次请求创建一个 Session，提交/关闭由依赖函数管理
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """
    数据库会话依赖（FastAPI Depends 使用）。
    功能：
      1. 打开一个新会话 db
      2. yield 给路由使用
      3. 请求结束后关闭会话，释放连接
    这样保证每个请求都有独立的、正确关闭的数据库会话。
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
