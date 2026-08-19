# =============================================================
# 段功能：初始迁移（M1 建表）
# 说明：以 models.py 的 Base.metadata 为唯一事实来源，
#       upgrade() 调用 create_all 一次性建立全部 29 张表；
#       downgrade() 调用 drop_all 回滚。
#       后续里程碑新增/修改表应使用 autogenerate 生成新修订文件，
#       不要在本次手动编写 29 条 CREATE TABLE。
# =============================================================

from alembic import op

from app.core.database import Base
import app.models  # noqa: F401  确保表已注册到 metadata


def upgrade() -> None:
    """
    升级：创建全部表。
    """
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """
    回滚：删除全部表（谨慎：会清空数据）。
    """
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
