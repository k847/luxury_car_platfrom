# =============================================================
# 段功能：开发种子脚本（M1 可运行性支撑，属于 M5 种子数据的简化版）
# 说明：首次搭建时库内无任何账号，登录接口无法验证。
#       本脚本向空库写入一个超级管理员 + super 角色 + 全部权限点，
#       便于本地启动后直接登录联调。生产环境请勿使用默认口令。
#       追加 seed_demo_data（python seed.py demo）写入双语演示主数据。
# 用法：在 backend 目录下执行
#       python seed.py       # 写入账号与权限
#       python seed.py demo  # 写入双语演示数据
# 说明：脚本依赖 backend/ 在 sys.path，因此可直接 import app 包。

from datetime import datetime
# =============================================================

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    AdminUser, Permission, Role, RolePermission,
    Brand, Series, Model, Trim, OptionGroup, Option, Article, Banner,
    Dealer, FinanceParam, TestDriveLead,
    BrandI18n, SeriesI18n, ModelI18n, OptionGroupI18n, OptionI18n, ArticleI18n,
)


def seed(db=None):
    """
    写入初始超级管理员与权限数据。
    先建表（若尚未建），再幂等插入：已存在则跳过。
    可选参数 db：传入已绑定会话（如 SQLite 演示库）；默认使用全局 MySQL 引擎。
    """
    # 自建会话才负责建表与关闭；外部传入的会话（演示库）由调用方管理
    own = db is None
    if own:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
    try:
        # --- 权限点：覆盖《开发技术文档》附录 C 的角色→权限矩阵所需编码 ---
        perm_codes = [
            "brand:*", "series:*", "model:*", "config:*",
            "content:*", "banner:*",
            "lead.test_drive:*", "lead.inquiry:*", "dealer:*",
            "dashboard:view", "role:*", "audit", "system",
        ]
        perm_map = {}
        for code in perm_codes:
            name = code
            existing = db.query(Permission).filter(Permission.code == code).first()
            if existing:
                perm_map[code] = existing
                continue
            p = Permission(code=code, name=name, module=code.split(":")[0])
            db.add(p)
            db.flush()  # 拿到自增 id
            perm_map[code] = p

        # --- super 角色 ---
        role = db.query(Role).filter(Role.code == "super").first()
        if not role:
            role = Role(name="超级管理员", code="super", remark="拥有全部权限")
            db.add(role)
            db.flush()

        # --- 角色挂全部权限 ---
        for code, p in perm_map.items():
            rel = (
                db.query(RolePermission)
                .filter(RolePermission.role_id == role.id, RolePermission.permission_id == p.id)
                .first()
            )
            if not rel:
                db.add(RolePermission(role_id=role.id, permission_id=p.id))

        # --- 超级管理员账号（默认 admin / admin123，生产务必修改）---
        admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if not admin:
            admin = AdminUser(
                username="admin",
                password_hash=hash_password("admin123"),
                real_name="超级管理员",
                role_id=role.id,
                is_active=1,
            )
            db.add(admin)

        db.commit()
        print("种子数据写入完成：超级管理员 admin / admin123")
    finally:
        if own:
            db.close()


def seed_demo_data(db=None):
    """
    段功能：M5 双语演示数据（供前台/后台联调）。
    说明：幂等插入 1 品牌 + 1 车系 + 1 车型（含配置器/配置版本）+ 1 资讯 + 1 Banner
          + 1 经销商 + 金融参数 + 1 条演示试驾线索，全部中英双语。
    用法：python seed.py demo（可传 db 复用外部会话，如 SQLite 演示库）
    """
    own = db is None
    if own:
        db = SessionLocal()
    try:
        if db.query(Brand).first():
            print("已存在主数据，跳过演示数据写入")
            return

        # 品牌 BMW（双语）
        b = Brand(brand_code="bmw", country="德国", sort=1, is_active=1)
        db.add(b); db.flush()
        db.add(BrandI18n(brand_id=b.id, lang="zh", name="宝马", is_active=1))
        db.add(BrandI18n(brand_id=b.id, lang="en", name="BMW", is_active=1))
        # 车系 7系
        s = Series(brand_id=b.id, series_code="7series", segment="sedan", is_active=1)
        db.add(s); db.flush()
        db.add(SeriesI18n(series_id=s.id, lang="zh", name="7系", is_active=1))
        db.add(SeriesI18n(series_id=s.id, lang="en", name="7 Series", is_active=1))
        # 车型 i7（纯电旗舰）
        m = Model(series_id=s.id, model_code="i7", fuel_type="ev", guide_price=899000,
                  is_recommended=1, status="active", body_length=5391, body_width=1950,
                  body_height=1548, wheelbase=3215, trunk_volume=500, is_active=1)
        db.add(m); db.flush()
        db.add(ModelI18n(model_id=m.id, lang="zh", name="i7", summary="纯电旗舰", is_active=1))
        db.add(ModelI18n(model_id=m.id, lang="en", name="i7", summary="EV flagship", is_active=1))
        # 配置版本
        db.add(Trim(model_id=m.id, trim_name="xDrive60", price=899000, power="400kW", drive="awd", is_active=1))
        # 配置器：颜色 / 轮毂 / 内饰 / 选装包（双语）
        for code, zh, en, req, mx in [("color", "外观颜色", "Exterior", 1, 1),
                                      ("wheel", "轮毂", "Wheels", 1, 1),
                                      ("interior", "内饰", "Interior", 1, 1),
                                      ("package", "选装包", "Packages", 0, 3)]:
            g = OptionGroup(model_id=m.id, group_code=code, is_required=req, max_select=mx, sort=mx, is_active=1)
            db.add(g); db.flush()
            db.add(OptionGroupI18n(group_id=g.id, lang="zh", name=zh, is_active=1))
            db.add(OptionGroupI18n(group_id=g.id, lang="en", name=en, is_active=1))
            if code == "color":
                o = Option(group_id=g.id, option_code="black", swatch="#0E0E10", price_delta=0,
                           stock_status="in_stock", is_default=1, sort=1, is_active=1)
                db.add(o); db.flush()
                db.add(OptionI18n(option_id=o.id, lang="zh", name="曜石黑", is_active=1))
                db.add(OptionI18n(option_id=o.id, lang="en", name="Obsidian Black", is_active=1))
                o2 = Option(group_id=g.id, option_code="gold", swatch="#C2A36B", price_delta=18000,
                            stock_status="preorder", lead_time=30, sort=2, is_active=1)
                db.add(o2); db.flush()
                db.add(OptionI18n(option_id=o2.id, lang="zh", name="香槟金", is_active=1))
                db.add(OptionI18n(option_id=o2.id, lang="en", name="Champagne Gold", is_active=1))
        # 经销商
        d = Dealer(brand_id=b.id, name="北京朝阳店", city="北京", address="朝阳区金港大道1号",
                   lng=116.48, lat=39.92, phone="010-88886666", business_hours="09:00-18:00", is_active=1)
        db.add(d)
        # 资讯（双语）
        a = Article(category="company_news", status="published", author="编辑部", source="官方",
                    is_top=1, published_at=datetime.utcnow(), is_active=1)
        db.add(a); db.flush()
        db.add(ArticleI18n(article_id=a.id, lang="zh", title="冠驭名车正式上线",
                           summary="聚合全球豪华品牌，开启一站式选车体验", body="<p>欢迎体验</p>", is_active=1))
        db.add(ArticleI18n(article_id=a.id, lang="en", title="REGALIA MOTORS Launched",
                           summary="Aggregated global luxury brands", body="<p>Welcome</p>", is_active=1))
        # Banner
        db.add(Banner(position="home_hero", image="/img/hero.jpg", link=f"/models/{m.id}", sort=1, is_active=1))
        # 金融参数
        db.add(FinanceParam(term_months=12, annual_rate=0.049, product_name="标准贷"))
        db.add(FinanceParam(term_months=24, annual_rate=0.051, product_name="尊享贷"))
        db.add(FinanceParam(term_months=36, annual_rate=0.053, product_name="长轴贷"))
        # 演示试驾线索
        db.add(TestDriveLead(name="演示客户", phone="13800000001", city="北京",
                             brand_id=b.id, model_id=m.id, status="pending", source="seed", is_active=1))
        db.commit()
        print("双语演示数据写入完成")
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        seed_demo_data()
    else:
        seed()
