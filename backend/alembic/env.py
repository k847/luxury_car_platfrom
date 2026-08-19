# =============================================================
# 段功能：Alembic 运行环境（M1 迁移）
# 说明：负责把 SQLAlchemy 的 Base.metadata 暴露给 Alembic，
#       并读取 settings 中的数据库地址。后续里程碑新增表时，
#       用 `alembic revision --autogenerate` 生成增量迁移即可。
# =============================================================

import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# 将 backend 目录加入 sys.path，确保能 import app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
import app.models  # noqa: E402,F401   # 关键：导入模型模块，注册全部表到 metadata

# Alembic 配置对象
config = context.config
# 用 settings 中的真实连接串覆盖 ini 中的占位
config.set_main_option("sqlalchemy.url", settings.database_url)

# 目标元数据：所有表的集合（来自 models.py）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线迁移：仅生成 SQL 脚本，不连接数据库。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线迁移：连接数据库执行迁移。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
