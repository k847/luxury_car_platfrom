# =============================================================
# 段功能：ORM 模型定义（M1 建表依据，对应《数据库设计文档》29 张表）
# 说明：本文件用 SQLAlchemy 2.x 声明所有数据库表。
#       - 主表（品牌/车系/车型/线索/权限/系统…）继承 CommonColumns 复用审计字段
#       - 翻译表（*_i18n）继承 I18nColumns 复用翻译表公共字段，并使用 (实体id, lang) 联合主键
#       - model_dealer / role_permissions 为关联表，已补充 DDL 中声明但遗漏的 id 主键
#       列上的 comment= 与《数据库设计文档》DDL 注释一一对应，便于人工核对。
# =============================================================

from datetime import datetime

from decimal import Decimal  # Python 的 Decimal，用于 Mapped[Decimal] 类型标注
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)

from app.core.database import Base


# ---------- 公共字段 mixin ----------
class CommonColumns:
    """
    主表公共字段（22 张主表复用）。
    含义对齐数据库设计文档公共字段规范：
      created_at  创建时间（UTC）
      updated_at  更新时间（每次 UPDATE 自动刷新由 DB 触发器语义，应用层也维护）
      deleted_at  软删除时间（NULL 表示未删除）
      is_active   状态：1 激活 / 0 禁用
      created_by  创建人（admin_users.id，系统记录为 NULL）
      updated_by  修改人（admin_users.id）
    """

    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间（UTC）")
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
        comment="更新时间（UTC）",
    )
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间（NULL 未删除）")
    is_active = Column(SmallInteger, nullable=False, server_default="1", comment="状态：1 激活 / 0 禁用")
    created_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="创建人 admin_users.id")
    updated_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="修改人 admin_users.id")


class I18nColumns:
    """
    翻译表公共字段（7 张 *_i18n 表复用）。
    翻译表无独立 id、无 deleted_at，仅含激活/审计字段。
    """

    is_active = Column(SmallInteger, nullable=False, server_default="1", comment="状态：1 激活 / 0 禁用")
    created_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="创建人 admin_users.id")
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间（UTC）")
    updated_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="修改人 admin_users.id")
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
        comment="更新时间（UTC）",
    )


# 统一主键辅助：BIGINT UNSIGNED 自增
# （说明：各模型已在类内直接声明 id 列，此处不再提供公共辅助函数，
#   以免与 mixin 列产生命名歧义；保持显式声明更利于人工审核。）

# ===================== 1. 品牌 =====================
class Brand(Base, CommonColumns):
    """汽车品牌主数据（brands）。"""

    __tablename__ = "brands"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    brand_code = Column(String(32), nullable=False, unique=True, comment="品牌编码（唯一）")
    logo = Column(String(255), comment="品牌 Logo 图片 URL")
    country = Column(String(64), comment="国别（如 Germany / China）")
    sort = Column(Integer, server_default="0", comment="排序权重（越大越靠前）")


# ===================== 2. 车系 =====================
class Series(Base, CommonColumns):
    """品牌下的车系（series）。"""

    __tablename__ = "series"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    brand_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, comment="所属品牌")
    series_code = Column(String(32), nullable=False, unique=True, comment="车系编码（唯一）")
    segment = Column(String(32), comment="级别：sedan/SUV/MPV/coupe…")


# ===================== 3. 车型 =====================
class Model(Base, CommonColumns):
    """车系下的具体车型（models）。"""

    __tablename__ = "models"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    series_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("series.id", ondelete="RESTRICT"), nullable=False, comment="所属车系")
    model_code = Column(String(32), nullable=False, unique=True, comment="车型编码（唯一）")
    fuel_type = Column(String(20), comment="能源类型：gasoline/diesel/hybrid/ev/phev")
    body_length = Column(Integer, comment="车长 mm")
    body_width = Column(Integer, comment="车宽 mm")
    body_height = Column(Integer, comment="车高 mm")
    wheelbase = Column(Integer, comment="轴距 mm")
    trunk_volume = Column(Integer, comment="后备箱容积 L")
    guide_price = Column(Numeric(12, 2), comment="指导价（元）")
    is_recommended = Column(SmallInteger, server_default="0", comment="是否首页推荐：0 否 / 1 是")
    launch_date = Column(Date, comment="上市日期")
    status = Column(String(20), nullable=False, server_default="active", comment="状态：active 在售 / upcoming 未上市 / discontinued 停售")


# ===================== 4. 配置版本 Trim =====================
class Trim(Base, CommonColumns):
    """车型下的配置版本（trims）。"""

    __tablename__ = "trims"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    model_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("models.id", ondelete="RESTRICT"), nullable=False, comment="所属车型")
    trim_name = Column(String(128), nullable=False, comment="配置版本名称")
    price = Column(Numeric(12, 2), comment="该版本价格（元）")
    power = Column(String(64), comment="动力/功率描述")
    transmission = Column(String(32), comment="变速箱：auto/manual")
    drive = Column(String(32), comment="驱动方式：fwd/rwd/awd")
    key_specs = Column(Text, comment="关键规格 JSON")


# ===================== 5. 配置器选项分组 =====================
class OptionGroup(Base, CommonColumns):
    """车型配置器选项分组（option_groups）。"""

    __tablename__ = "option_groups"
    __table_args__ = (UniqueConstraint("model_id", "group_code", name="uk_option_groups_model_group"),)

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    model_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("models.id", ondelete="RESTRICT"), nullable=False, comment="所属车型")
    group_code = Column(String(32), nullable=False, comment="分组编码：color/wheel/interior/package")
    is_required = Column(SmallInteger, server_default="0", comment="是否必选：0 否 / 1 是")
    max_select = Column(Integer, server_default="1", comment="最多可选数量")
    exclude_groups = Column(Text, comment="互斥分组 JSON")
    sort = Column(Integer, server_default="0", comment="排序")


# ===================== 6. 选项 =====================
class Option(Base, CommonColumns):
    """选项组下的具体选项（options）。"""

    __tablename__ = "options"
    __table_args__ = (UniqueConstraint("group_id", "option_code", name="uk_options_group_code"),)

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    group_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("option_groups.id", ondelete="RESTRICT"), nullable=False, comment="所属选项组")
    option_code = Column(String(32), nullable=False, comment="选项编码")
    swatch = Column(String(32), comment="色板/色值")
    price_delta = Column(Numeric(12, 2), server_default="0.00", comment="加价（元）")
    stock_status = Column(String(20), server_default="in_stock", comment="库存：in_stock 有货 / preorder 预订 / eol 停产")
    lead_time = Column(Integer, comment="交付周期（天）")
    is_default = Column(SmallInteger, server_default="0", comment="是否默认选中")
    sort = Column(Integer, server_default="0", comment="排序")


# ===================== 7. 经销商 =====================
class Dealer(Base, CommonColumns):
    """门店/经销商（dealers）。"""

    __tablename__ = "dealers"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    brand_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, comment="所属品牌")
    name = Column(String(128), nullable=False, comment="门店名称")
    city = Column(String(64), comment="城市")
    address = Column(String(255), comment="地址")
    lng = Column(Numeric(10, 7), comment="经度")
    lat = Column(Numeric(10, 7), comment="纬度")
    phone = Column(String(32), comment="电话")
    business_hours = Column(String(128), comment="营业时间")
    cover = Column(String(255), comment="封面图 URL")


# ===================== 8. 车型-经销商关联 =====================
class ModelDealer(Base):
    """
    车型与经销商多对在售关系（model_dealer）。
    说明：DDL 声明 PRIMARY KEY(id) 但遗漏了 id 列，这里补齐自增主键；
         并保留 (model_id, dealer_id) 唯一约束防止重复关联。
    """

    __tablename__ = "model_dealer"
    __table_args__ = (UniqueConstraint("model_id", "dealer_id", name="uk_model_dealer"),)

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键（补齐 DDL 遗漏）")
    model_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, comment="车型 ID")
    dealer_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("dealers.id", ondelete="CASCADE"), nullable=False, comment="经销商 ID")
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间（UTC）")
    is_active = Column(SmallInteger, nullable=False, server_default="1", comment="状态：1 激活 / 0 禁用")
    created_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="创建人 admin_users.id")
    updated_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="修改人 admin_users.id")
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow, comment="修改时间（UTC）")


# ===================== 9. 产品分类 =====================
class Category(Base, CommonColumns):
    """产品分类（支持层级，categories）。"""

    __tablename__ = "categories"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    parent_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, comment="上级分类（自引用，顶级为 NULL）")
    category_name = Column(String(64), nullable=False, comment="分类名称（如 轿车/SUV/跑车/MPV）")
    sort = Column(Integer, server_default="0", comment="排序权重")


# ===================== 10. 精选产品 =====================
class Product(Base, CommonColumns):
    """精选产品 / 车型营销展示（products）。"""

    __tablename__ = "products"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    product_code = Column(String(32), nullable=False, unique=True, comment="产品编号（唯一）")
    series_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("series.id", ondelete="RESTRICT"), nullable=False, comment="所属系列")
    model_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("models.id", ondelete="SET NULL"), nullable=True, comment="关联具体车型（可选）")
    category_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, comment="所属产品分类")
    specs = Column(Text, comment="规格参数 JSON")
    cover_url = Column(String(255), comment="封面图片 URL")
    gallery_urls = Column(Text, comment="其它图片 URL（JSON 数组）")
    status = Column(String(20), nullable=False, server_default="draft", comment="发布状态：on_sale 上架 / off_shelf 下架 / draft 草稿")
    is_top = Column(SmallInteger, server_default="0", comment="是否置顶：0 否 / 1 是")
    sort = Column(Integer, server_default="0", comment="排序值")


# ===================== 11. 资讯/新闻 =====================
class Article(Base, CommonColumns):
    """新闻（企业新闻/行业资讯）/活动/行业资讯（articles）。"""

    __tablename__ = "articles"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    category = Column(String(20), nullable=False, comment="分类：company_news 企业新闻 / industry 行业资讯 / event 活动")
    cover_url = Column(String(255), comment="封面图 URL")
    author = Column(String(64), comment="作者")
    source = Column(String(128), comment="来源（转载标注）")
    published_at = Column(DateTime, comment="发布时间")
    expired_at = Column(DateTime, comment="截止 / 下线时间（可空）")
    status = Column(String(20), nullable=False, server_default="draft", comment="状态：draft 草稿 / published 已发布 / archived 归档")
    is_top = Column(SmallInteger, server_default="0", comment="是否置顶：0 否 / 1 是")
    is_recommended = Column(SmallInteger, server_default="0", comment="是否推荐：0 否 / 1 是")


# ===================== 12. Banner =====================
class Banner(Base, CommonColumns):
    """首页轮播/Banner 区块（banners）。"""

    __tablename__ = "banners"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    position = Column(String(32), nullable=False, comment="位置：home_hero 等")
    image = Column(String(255), nullable=False, comment="图片 URL")
    link = Column(String(512), comment="跳转链接")
    start_at = Column(DateTime, comment="生效开始")
    end_at = Column(DateTime, comment="生效结束")
    sort = Column(Integer, server_default="0", comment="排序")


# ===================== 13. 试驾留资 =====================
class TestDriveLead(Base, CommonColumns):
    """C 端预约试驾留资（test_drive_leads）。"""

    __tablename__ = "test_drive_leads"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(64), nullable=False, comment="客户姓名")
    phone = Column(String(32), nullable=False, comment="客户电话")
    city = Column(String(64), comment="城市")
    brand_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, comment="意向品牌")
    model_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("models.id", ondelete="SET NULL"), nullable=True, comment="意向车型")
    config_summary = Column(Text, comment="配置摘要 JSON")
    preferred_dealer_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("dealers.id", ondelete="SET NULL"), nullable=True, comment="意向经销商")
    preferred_time = Column(DateTime, comment="期望时间")
    remark = Column(String(512), comment="备注")
    source = Column(String(32), comment="来源渠道")
    status = Column(String(20), nullable=False, server_default="pending", comment="状态机：pending 待跟进 / contacted 已联系 / arrived 已到店 / deal 成交 / invalid 失效（对齐 §8.4）")
    owner_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, comment="跟进账号")


# ===================== 14. 询价留资 =====================
class InquiryLead(Base, CommonColumns):
    """C 端在线询价留资（inquiry_leads）。"""

    __tablename__ = "inquiry_leads"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(64), nullable=False, comment="客户姓名")
    phone = Column(String(32), nullable=False, comment="客户电话")
    city = Column(String(64), comment="城市")
    brand_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, comment="意向品牌")
    model_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("models.id", ondelete="SET NULL"), nullable=True, comment="意向车型")
    intent = Column(String(255), comment="意向说明")
    remark = Column(String(512), comment="备注")
    status = Column(String(20), nullable=False, server_default="new", comment="状态机：new 新建 / contacted 已联系 / completed 已完成 / cancelled 已取消")
    owner_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, comment="跟进账号")


# ===================== 15. 部门 =====================
class Department(Base, CommonColumns):
    """组织架构部门（支持层级，departments）。"""

    __tablename__ = "departments"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    dept_name = Column(String(64), nullable=False, comment="部门名称")
    parent_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, comment="上级部门（自引用，顶级为 NULL）")
    sort = Column(Integer, server_default="0", comment="排序权重")


# ===================== 16. 后台账号 =====================
class AdminUser(Base, CommonColumns):
    """B 端后台账号（admin_users）。"""

    __tablename__ = "admin_users"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    username = Column(String(64), nullable=False, unique=True, comment="用户名 / 登录名（唯一）")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(64), comment="姓名")
    nickname = Column(String(64), comment="昵称")
    phone = Column(String(20), comment="手机号")
    email = Column(String(128), comment="邮箱")
    gender = Column(String(8), comment="性别：male / female / unknown")
    position = Column(String(64), comment="岗位")
    department_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, comment="部门编号")
    role_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, comment="角色编号")
    last_login_at = Column(DateTime, comment="最近登录时间")


# ===================== 17. 角色 =====================
class Role(Base, CommonColumns):
    """RBAC 角色（roles）。"""

    __tablename__ = "roles"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(64), nullable=False, comment="角色名称")
    code = Column(String(64), nullable=False, unique=True, comment="角色编码（唯一）")
    remark = Column(String(255), comment="备注")


# ===================== 18. 权限点 =====================
class Permission(Base, CommonColumns):
    """RBAC 权限点（permissions）。"""

    __tablename__ = "permissions"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    code = Column(String(64), nullable=False, unique=True, comment="权限编码：模块:操作 如 model:create")
    name = Column(String(128), nullable=False, comment="权限名称")
    module = Column(String(32), comment="所属模块")


# ===================== 19. 角色-权限关联 =====================
class RolePermission(Base):
    """
    角色与权限多对多（role_permissions）。
    说明：同 model_dealer，DDL 声明 PRIMARY KEY(id) 但遗漏 id 列，这里补齐；
         并保留 (role_id, permission_id) 唯一约束。
    """

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uk_role_permissions"),)

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键（补齐 DDL 遗漏）")
    role_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色 ID")
    permission_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限 ID")
    is_active = Column(SmallInteger, nullable=False, server_default="1", comment="状态：1 激活 / 0 禁用")
    created_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="创建人 admin_users.id")
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间（UTC）")
    updated_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="修改人 admin_users.id")
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow, comment="修改时间（UTC）")


# ===================== 20. 审计日志 =====================
class AuditLog(Base):
    """操作审计日志（audit_logs）。"""

    __tablename__ = "audit_logs"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    admin_user_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, comment="操作人")
    action = Column(String(64), nullable=False, comment="动作")
    module = Column(String(32), comment="模块")
    target = Column(String(128), comment="目标对象")
    detail = Column(Text, comment="明细 JSON")
    ip = Column(String(64), comment="来源 IP")
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间（UTC）")
    is_active = Column(SmallInteger, nullable=False, server_default="1", comment="状态：1 激活 / 0 禁用")
    created_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="创建人 admin_users.id")
    updated_by = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), nullable=True, comment="修改人 admin_users.id")
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow, comment="修改时间（UTC）")


# ===================== 21. 系统配置 =====================
class SystemConfig(Base, CommonColumns):
    """站点/SEO 等配置键值（system_configs）。"""

    __tablename__ = "system_configs"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    key = Column(String(64), nullable=False, unique=True, comment="配置键（唯一）")
    value = Column(Text, comment="配置值")
    comment = Column(String(255), comment="说明")


# ===================== 22. 金融参数 =====================
class FinanceParam(Base, CommonColumns):
    """金融方案/利率参数（finance_params），供金融计算器使用。"""

    __tablename__ = "finance_params"

    id = Column("id", BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键")
    term_months = Column(Integer, nullable=False, comment="期数（月）")
    annual_rate = Column(Numeric(6, 4), nullable=False, comment="年利率")
    product_name = Column(String(64), comment="金融产品名")


# ===================== 23-29. 翻译表（*_i18n） =====================
class BrandI18n(Base, I18nColumns):
    """品牌多语言文本（brand_i18n）。"""

    __tablename__ = "brand_i18n"
    brand_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, primary_key=True, comment="品牌 ID")
    lang = Column(String(8), nullable=False, primary_key=True, comment="语言：zh / en")
    name = Column(String(128), nullable=False, comment="品牌名称")


class SeriesI18n(Base, I18nColumns):
    """车系多语言文本（series_i18n）。"""

    __tablename__ = "series_i18n"
    series_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("series.id", ondelete="CASCADE"), nullable=False, primary_key=True, comment="车系 ID")
    lang = Column(String(8), nullable=False, primary_key=True, comment="语言：zh / en")
    name = Column(String(128), nullable=False, comment="车系名称")


class ModelI18n(Base, I18nColumns):
    """车型多语言文本（model_i18n）。"""

    __tablename__ = "model_i18n"
    model_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, primary_key=True, comment="车型 ID")
    lang = Column(String(8), nullable=False, primary_key=True, comment="语言：zh / en")
    name = Column(String(128), nullable=False, comment="车型名称")
    summary = Column(String(512), comment="车型简介")


class OptionGroupI18n(Base, I18nColumns):
    """选项组多语言文本（option_group_i18n）。"""

    __tablename__ = "option_group_i18n"
    group_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("option_groups.id", ondelete="CASCADE"), nullable=False, primary_key=True, comment="选项组 ID")
    lang = Column(String(8), nullable=False, primary_key=True, comment="语言：zh / en")
    name = Column(String(64), nullable=False, comment="选项组名称")


class OptionI18n(Base, I18nColumns):
    """选项多语言文本（option_i18n）。"""

    __tablename__ = "option_i18n"
    option_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("options.id", ondelete="CASCADE"), nullable=False, primary_key=True, comment="选项 ID")
    lang = Column(String(8), nullable=False, primary_key=True, comment="语言：zh / en")
    name = Column(String(128), nullable=False, comment="选项名称")


class ArticleI18n(Base, I18nColumns):
    """资讯多语言文本（article_i18n）。"""

    __tablename__ = "article_i18n"
    article_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, primary_key=True, comment="资讯 ID")
    lang = Column(String(8), nullable=False, primary_key=True, comment="语言：zh / en")
    title = Column(String(255), nullable=False, comment="标题")
    summary = Column(String(512), comment="摘要")
    body = Column(Text, comment="正文（富文本）")


class ProductI18n(Base, I18nColumns):
    """产品多语言文本（product_i18n）。"""

    __tablename__ = "product_i18n"
    product_id = Column(BigInteger().with_variant(BigInteger, "mysql").with_variant(Integer, "sqlite"), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, primary_key=True, comment="产品 ID")
    lang = Column(String(8), nullable=False, primary_key=True, comment="语言：zh / en")
    name = Column(String(128), nullable=False, comment="产品名称/标题")
    description = Column(Text, comment="产品描述（富文本）")
