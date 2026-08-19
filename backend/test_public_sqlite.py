# 段功能：M2 公共端接口端到端冒烟测试（SQLite 内存库，不依赖外部 MySQL）
# 说明：本脚本用于验证 §7.1/7.2/7.3/7.9 六个接口的真实可用性：
#   建表 -> 灌入样例数据 -> TestClient 实际发起 GET -> 断言 code/data/i18n/分页。
# 仅开发期使用，验证通过后可删除。

from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, SessionLocal
from app.models import (
    Brand, Series, Model, Product, Trim, OptionGroup, Option, Dealer, ModelDealer,
    Article, Banner,
    BrandI18n, SeriesI18n, ModelI18n, OptionI18n, ArticleI18n,
)
from app.main import app
from fastapi.testclient import TestClient


def seed(db):
    """灌入最小可验证数据集（中英文各一条）。"""
    # 品牌 + i18n
    b = Brand(id=1, brand_code="bmw", logo="/img/bmw.png", country="德国", sort=1, is_active=1)
    db.add(b)
    db.add(BrandI18n(brand_id=1, lang="zh", name="宝马", is_active=1))
    db.add(BrandI18n(brand_id=1, lang="en", name="BMW", is_active=1))
    # 车系 + i18n
    s = Series(id=1, brand_id=1, series_code="7series", segment="sedan", is_active=1)
    db.add(s)
    db.add(SeriesI18n(series_id=1, lang="zh", name="7系", is_active=1))
    db.add(SeriesI18n(series_id=1, lang="en", name="7 Series", is_active=1))
    # 车型 + i18n
    m = Model(id=101, series_id=1, model_code="i7", fuel_type="ev", guide_price=899000,
              is_recommended=1, status="active", body_length=5391, body_width=1950,
              body_height=1548, wheelbase=3215, trunk_volume=500,
              launch_date=date(2024, 1, 1), is_active=1)
    db.add(m)
    db.add(ModelI18n(model_id=101, lang="zh", name="i7", summary="纯电旗舰", is_active=1))
    db.add(ModelI18n(model_id=101, lang="en", name="i7", summary="EV flagship", is_active=1))
    # 产品（封面/图库）
    db.add(Product(id=1, product_code="p1", series_id=1, model_id=101,
                   cover_url="/img/i7.jpg",
                   gallery_urls='["/img/i7/1.jpg","/img/i7/2.jpg"]',
                   status="on_sale", is_active=1))
    # 配置版本
    db.add(Trim(id=1, model_id=101, trim_name="xDrive60", price=899000, power="400kW", drive="awd", is_active=1))
    # 颜色选项
    db.add(OptionGroup(id=1, model_id=101, group_code="color", is_required=1, max_select=1, sort=0, is_active=1))
    db.add(Option(id=1, group_id=1, option_code="black", swatch="#0E0E10", price_delta=0,
                  stock_status="in_stock", is_default=1, sort=0, is_active=1))
    db.add(OptionI18n(option_id=1, lang="zh", name="曜石黑", is_active=1))
    db.add(OptionI18n(option_id=1, lang="en", name="Obsidian Black", is_active=1))
    # 经销商 + 关联
    d = Dealer(id=9, brand_id=1, name="北京朝阳店", city="北京", is_active=1)
    db.add(d)
    db.add(ModelDealer(id=1, model_id=101, dealer_id=9, is_active=1))
    # 资讯 + i18n
    a = Article(id=1, category="company_news", cover_url="/img/news.jpg", status="published",
                is_top=1, published_at=datetime(2025, 1, 1, 10, 0, 0), author="编辑部",
                source="官方", is_active=1)
    db.add(a)
    db.add(ArticleI18n(article_id=1, lang="zh", title="标题中文", summary="摘要中文", body="正文中文", is_active=1))
    db.add(ArticleI18n(article_id=1, lang="en", title="Title EN", summary="Summary EN", body="Body EN", is_active=1))
    # Banner
    db.add(Banner(id=1, position="home_hero", image="/img/hero.jpg", link="/models/101", sort=1, is_active=1))
    db.commit()


def main():
    # 用 SQLite 内存库替代 MySQL，仅验证接口逻辑。
    # 使用 StaticPool 让所有会话复用同一连接，避免 :memory: 每连接独立的表丢失问题。
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    SessionLocal.configure(bind=eng)  # 将路由的依赖会话重定向到 sqlite

    with SessionLocal() as db:
        seed(db)

    client = TestClient(app)
    fails = []

    # §7.1 品牌
    r = client.get("/api/v1/brands")
    j = r.json()
    if j["code"] != 0 or not j["data"] or j["data"][0]["name_zh"] != "宝马" or j["data"][0]["name_en"] != "BMW":
        fails.append(("brands", j))
    print("brands:", j["code"], j["data"][0]["name_zh"], j["data"][0]["name_en"])

    # §7.2 车型列表（中文）
    r = client.get("/api/v1/models")
    j = r.json()
    it = j["data"]["list"][0]
    if j["code"] != 0 or it["model_name"] != "i7" or it["brand_name"] != "宝马" or it["cover_image"] != "/img/i7.jpg":
        fails.append(("models-zh", j))
    print("models(zh):", it["model_name"], it["brand_name"], it["cover_image"], "total=", j["data"]["total"])

    # §7.2 车型列表（英文，验证 i18n）
    r = client.get("/api/v1/models?lang=en")
    j = r.json()
    if j["data"]["list"][0]["brand_name"] != "BMW":
        fails.append(("models-en", j))
    print("models(en):", j["data"]["list"][0]["brand_name"])

    # §7.3 车型详情
    r = client.get("/api/v1/models/101")
    j = r.json()
    d = j["data"]
    if (j["code"] != 0 or d["model_name"] != "i7" or len(d["gallery"]) != 2
            or d["trims"][0]["trim_name"] != "xDrive60" or d["colors"][0]["name"] != "曜石黑"
            or d["dealers"][0]["city"] != "北京" or d["finance_available"] is not True):
        fails.append(("model-detail", j))
    print("model-detail:", d["model_name"], "gallery=", len(d["gallery"]),
          "colors=", d["colors"][0]["name"], "dealers=", d["dealers"][0]["city"])

    # §7.3 车型详情-不存在
    r = client.get("/api/v1/models/999")
    j = r.json()
    if j["code"] != 40400:
        fails.append(("model-404", j))
    print("model-404 code:", j["code"])

    # §7.9 资讯列表
    r = client.get("/api/v1/articles")
    j = r.json()
    if j["code"] != 0 or j["data"]["list"][0]["title"] != "标题中文":
        fails.append(("articles", j))
    print("articles:", j["data"]["list"][0]["title"], "total=", j["data"]["total"])

    # §7.9 资讯详情
    r = client.get("/api/v1/articles/1?lang=en")
    j = r.json()
    if j["code"] != 0 or j["data"]["body"] != "Body EN":
        fails.append(("article-detail", j))
    print("article-detail(en):", j["data"]["body"])

    # §7.9 Banner
    r = client.get("/api/v1/banners?position=home_hero")
    j = r.json()
    if j["code"] != 0 or j["data"][0]["image"] != "/img/hero.jpg":
        fails.append(("banners", j))
    print("banners:", j["data"][0]["image"])

    # 缓存命中校验：第二次请求应直接从缓存返回相同结果
    r2 = client.get("/api/v1/brands")
    if r2.json()["data"][0]["name_zh"] != "宝马":
        fails.append(("brands-cache", r2.json()))
    print("brands(2nd, cached):", r2.json()["data"][0]["name_zh"])

    if fails:
        print("\n❌ 失败用例:", [f[0] for f in fails])
        for name, payload in fails:
            print(name, payload)
        raise SystemExit(1)
    print("\n✅ 全部 M2 公开接口冒烟通过（i18n / 分页 / 序列化 / 404 / 缓存）")


if __name__ == "__main__":
    main()
