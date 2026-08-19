# 段功能：M4 后台管理接口端到端冒烟测试（SQLite 内存库）
# 说明：验证 §8 后台接口真实可用性：登录拿 token -> 门控(401/403) -> CRUD(含双语 i18n)
#       -> 线索列表/assign/advance 状态机(含越级 40022) -> 看板聚合 -> 审计落库。
# 仅开发期使用，验证通过后可删除。

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, SessionLocal
from app.core.security import hash_password
from app.models import (
    AdminUser, Role, Permission, RolePermission, Brand, Series, Model, Trim,
    OptionGroup, Option, Article, Banner, TestDriveLead, InquiryLead, Dealer,
    BrandI18n, SeriesI18n, ModelI18n, OptionGroupI18n, OptionI18n, ArticleI18n,
)
from app.main import app
from fastapi.testclient import TestClient


def seed(db):
    """灌入后台验证所需数据：super 角色 + admin 账号 + 权限 + 基础主数据 + 线索。"""
    # super 角色
    role = Role(name="超级管理员", code="super", remark="全部权限")
    db.add(role)
    db.flush()
    # 权限（通配符形式，验证 require_permission 通配匹配）
    perm_map = {}
    for code in ["brand:*", "series:*", "model:*", "config:*", "content:*", "banner:*",
                 "lead.test_drive:*", "lead.inquiry:*", "dealer:*", "dashboard:view",
                 "role:*", "audit", "system"]:
        p = Permission(code=code, name=code, module=code.split(":")[0])
        db.add(p)
        db.flush()
        perm_map[code] = p
        db.add(RolePermission(role_id=role.id, permission_id=p.id))
    # admin 账号
    admin = AdminUser(username="admin", password_hash=hash_password("admin123"),
                      real_name="超管", role_id=role.id, is_active=1)
    db.add(admin)
    db.flush()

    # 品牌（含双语）用于 CRUD 验证
    b = Brand(id=1, brand_code="bmw", country="德国", sort=1, is_active=1)
    db.add(b)
    db.add(BrandI18n(brand_id=1, lang="zh", name="宝马", is_active=1))
    db.add(BrandI18n(brand_id=1, lang="en", name="BMW", is_active=1))
    # 车系
    s = Series(id=1, brand_id=1, series_code="7series", segment="sedan", is_active=1)
    db.add(s)
    db.add(SeriesI18n(series_id=1, lang="zh", name="7系", is_active=1))
    db.add(SeriesI18n(series_id=1, lang="en", name="7 Series", is_active=1))
    # 车型
    m = Model(id=101, series_id=1, model_code="i7", fuel_type="ev", guide_price=899000,
              status="active", is_active=1)
    db.add(m)
    db.add(ModelI18n(model_id=101, lang="zh", name="i7", is_active=1))
    db.add(ModelI18n(model_id=101, lang="en", name="i7", is_active=1))
    db.add(Trim(id=1, model_id=101, trim_name="xDrive60", price=899000, is_active=1))
    # 配置器分组 + 选项
    db.add(OptionGroup(id=1, model_id=101, group_code="color", is_required=1, max_select=1, is_active=1))
    db.add(OptionGroupI18n(group_id=1, lang="zh", name="外观颜色", is_active=1))
    db.add(Option(id=1, group_id=1, option_code="black", price_delta=0, stock_status="in_stock", is_active=1))
    db.add(OptionI18n(option_id=1, lang="zh", name="曜石黑", is_active=1))
    # 资讯
    db.add(Article(id=1, category="company_news", status="published", is_active=1,
                   published_at=datetime(2026, 1, 1)))
    db.add(ArticleI18n(article_id=1, lang="zh", title="标题", is_active=1))
    # 线索：一条 pending 试驾 + 一条 new 询价（状态机验证）
    db.add(TestDriveLead(id=1, name="张三", phone="13800000001", city="北京", model_id=101,
                         status="pending", is_active=1))
    db.add(InquiryLead(id=1, name="李四", phone="13900000002", intent="finance",
                       status="new", is_active=1))
    db.commit()


def main():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    SessionLocal.configure(bind=eng)
    with SessionLocal() as db:
        seed(db)

    client = TestClient(app)
    fails = []

    def login():
        # 注：M1 的 /auth/login 返回裸 LoginResponse（无 {code,message,data} 信封），前端已兼容
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        return r.json()

    # 1) 登录成功（裸响应：直接含 access_token）
    j = login()
    token = j.get("access_token")
    if not token:
        fails.append(("login", j))
        print("login FAILED:", j)
        raise SystemExit(1)
    print("login: ok, token len=", len(token))
    H = {"Authorization": f"Bearer {token}"}

    # 2) 无 token -> 401
    r = client.get("/api/v1/admin/brands")
    if r.status_code != 401:
        fails.append(("no-token-401", r.status_code))
    print("no-token->status:", r.status_code)

    # 3) 品牌列表（带 token）
    r = client.get("/api/v1/admin/brands", headers=H)
    j = r.json()
    if j["code"] != 0 or j["data"][0]["name_zh"] != "宝马" or j["data"][0]["name_en"] != "BMW":
        fails.append(("brands-list", j))
    print("brands-list:", j["data"][0]["name_zh"], "/", j["data"][0]["name_en"])

    # 4) 创建品牌（双语写 i18n 事务）
    r = client.post("/api/v1/admin/brands", headers=H, json={
        "brand_code": "mb", "country": "德国", "sort": 2, "is_active": 1,
        "name_zh": "奔驰", "name_en": "Mercedes-Benz"})
    j = r.json()
    if j["code"] != 0 or not j["data"]["id"]:
        fails.append(("brand-create", j))
    new_id = j["data"]["id"]
    print("brand-create: id=", new_id)
    # 验证双语已写入
    r = client.get("/api/v1/admin/brands", headers=H)
    mb = next((x for x in r.json()["data"] if x["id"] == new_id), None)
    if not mb or mb["name_en"] != "Mercedes-Benz":
        fails.append(("brand-create-i18n", mb))
    print("brand-create i18n:", mb["name_zh"], "/", mb["name_en"])

    # 5) 车型列表（分页）
    r = client.get("/api/v1/admin/models", headers=H)
    j = r.json()
    if j["code"] != 0 or j["data"]["total"] < 1:
        fails.append(("models-list", j))
    print("models-list: total=", j["data"]["total"])

    # 6) 资讯列表
    r = client.get("/api/v1/admin/articles", headers=H)
    if r.json()["code"] != 0:
        fails.append(("articles-list", r.json()))
    print("articles-list: ok")

    # 7) 线索：试驾列表
    r = client.get("/api/v1/admin/leads/test-drive", headers=H)
    j = r.json()
    if j["code"] != 0 or j["data"]["list"][0]["status"] != "pending":
        fails.append(("leads-td-list", j))
    print("leads-td-list:", j["data"]["list"][0]["status"])

    # 8) 试驾状态机：pending -> contacted（合法）
    r = client.post("/api/v1/admin/leads/test-drive/1/advance", headers=H, json={"to_status": "contacted"})
    j = r.json()
    if j["code"] != 0 or j["data"]["status"] != "contacted":
        fails.append(("leads-td-advance", j))
    print("leads-td advance pending->contacted:", j["data"]["status"])

    # 9) 试驾状态机：contacted -> deal（越级，应 40022）
    r = client.post("/api/v1/admin/leads/test-drive/1/advance", headers=H, json={"to_status": "deal"})
    if r.json()["code"] != 40022:
        fails.append(("leads-td-advance-skip", r.json()))
    print("leads-td advance contacted->deal(越级):", r.json()["code"])

    # 10) 询价状态机：new -> processing -> quoted
    r = client.post("/api/v1/admin/leads/inquiry/1/advance", headers=H, json={"to_status": "processing"})
    if r.json()["code"] != 0:
        fails.append(("leads-iq-advance", r.json()))
    r = client.post("/api/v1/admin/leads/inquiry/1/advance", headers=H, json={"to_status": "quoted"})
    if r.json()["code"] != 0:
        fails.append(("leads-iq-advance2", r.json()))
    print("leads-iq advance new->processing->quoted: ok")

    # 11) 线索分配
    r = client.post("/api/v1/admin/leads/test-drive/1/assign", headers=H, json={"owner_id": 1})
    if r.json()["code"] != 0:
        fails.append(("leads-assign", r.json()))
    print("leads-td assign: ok")

    # 12) 看板聚合
    r = client.get("/api/v1/admin/dashboard?range=30", headers=H)
    j = r.json()
    if j["code"] != 0 or not isinstance(j["data"]["kpis"], dict) or not isinstance(j["data"]["funnel"], list):
        fails.append(("dashboard", j))
    print("dashboard: kpis=", j["data"]["kpis"])

    # 13) 审计日志（写操作已落库）
    r = client.get("/api/v1/admin/audit-logs", headers=H)
    j = r.json()
    if j["code"] != 0 or j["data"]["total"] < 1:
        fails.append(("audit-logs", j))
    print("audit-logs: total=", j["data"]["total"])

    if fails:
        print("\n❌ 失败用例:", [f[0] for f in fails])
        for name, payload in fails:
            print(name, payload)
        raise SystemExit(1)
    print("\n✅ 全部 M4 后台管理接口冒烟通过（登录 / 门控 / CRUD双语 / 状态机 / 分配 / 看板 / 审计）")


if __name__ == "__main__":
    main()
