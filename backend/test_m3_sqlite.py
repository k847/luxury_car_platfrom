# 段功能：M3 选车深化接口端到端冒烟测试（SQLite 内存库，不依赖外部 MySQL）
# 说明：验证 §7.4 配置器 / §7.5 算价 / §7.6 对比 / 金融参数 / §7.7 留资 六个接口的真实可用性：
#   建表 -> 灌入样例数据 -> TestClient 实际发起请求 -> 断言 code/data/算价规则/i18n/限流/校验。
# 仅开发期使用，验证通过后可删除。

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, SessionLocal
from app.models import (
    Brand, Series, Model, Trim, OptionGroup, Option,
    BrandI18n, SeriesI18n, ModelI18n, OptionI18n, OptionGroupI18n,
    FinanceParam, TestDriveLead, InquiryLead,
)
from app.main import app
from fastapi.testclient import TestClient


def seed(db):
    """灌入 M3 验证所需最小数据集：车型101 含完整配置器、车型102 用于对比、金融参数、翻译。"""
    # 品牌 + 车系（Model 依赖 Series，Series 依赖 Brand）
    db.add(Brand(id=1, brand_code="bmw", country="德国", is_active=1))
    db.add(BrandI18n(brand_id=1, lang="zh", name="宝马", is_active=1))
    db.add(BrandI18n(brand_id=1, lang="en", name="BMW", is_active=1))
    db.add(Series(id=1, brand_id=1, series_code="7series", segment="sedan", is_active=1))
    db.add(SeriesI18n(series_id=1, lang="zh", name="7系", is_active=1))
    db.add(SeriesI18n(series_id=1, lang="en", name="7 Series", is_active=1))

    # 车型 101（配置器主体）
    db.add(Model(id=101, series_id=1, model_code="i7", fuel_type="ev", guide_price=899000,
                 status="active", body_length=5391, body_width=1950, body_height=1548,
                 wheelbase=3215, trunk_volume=500, is_active=1))
    db.add(ModelI18n(model_id=101, lang="zh", name="i7", is_active=1))
    db.add(ModelI18n(model_id=101, lang="en", name="i7", is_active=1))
    db.add(Trim(id=1, model_id=101, trim_name="xDrive60", price=899000, power="400kW", drive="awd", is_active=1))

    # 车型 102（对比用）
    db.add(Model(id=102, series_id=1, model_code="i5", fuel_type="ev", guide_price=499000,
                 status="active", body_length=5060, body_width=1900, body_height=1505,
                 wheelbase=3105, trunk_volume=450, is_active=1))
    db.add(ModelI18n(model_id=102, lang="zh", name="i5", is_active=1))
    db.add(ModelI18n(model_id=102, lang="en", name="i5", is_active=1))

    # 配置器分组 + i18n
    groups = [
        (1, "color", 1, 1, "外观颜色", "Exterior Color"),
        (2, "wheel", 1, 1, "轮毂", "Wheels"),
        (3, "interior", 1, 1, "内饰", "Interior"),
        (4, "package", 0, 3, "选装包", "Packages"),
    ]
    for gid, code, req, mx, zh, en in groups:
        db.add(OptionGroup(id=gid, model_id=101, group_code=code, is_required=req, max_select=mx, sort=gid, is_active=1))
        db.add(OptionGroupI18n(group_id=gid, lang="zh", name=zh, is_active=1))
        db.add(OptionGroupI18n(group_id=gid, lang="en", name=en, is_active=1))

    # 选项 + i18n：color(1,2) wheel(3,4) interior(5,6) package(7,8)
    options = [
        # id, group_id, code, swatch, delta, stock, lead, default, zh, en
        (1, 1, "black", "#0E0E10", 0, "in_stock", None, 1, "曜石黑", "Obsidian Black"),
        (2, 1, "gold", "#C2A36B", 18000, "preorder", 30, 0, "香槟金", "Champagne Gold"),
        (3, 2, "w19", None, 0, "in_stock", None, 1, '19" 标准', '19" Standard'),
        (4, 2, "w21", None, 15000, "in_stock", None, 0, '21" 运动', '21" Sport'),
        (5, 3, "black-leather", None, 0, "in_stock", None, 1, "黑色真皮", "Black Leather"),
        (6, 3, "ivory", None, 10000, "in_stock", None, 0, "象牙白", "Ivory White"),
        (7, 4, "adpack", None, 38000, "in_stock", None, 0, "智能驾驶包", "Driving Assist"),
        (8, 4, "comfort", None, 26000, "in_stock", None, 0, "尊享舒适包", "Comfort Pack"),
    ]
    for oid, gid, code, sw, delta, stock, lead, dft, zh, en in options:
        db.add(Option(id=oid, group_id=gid, option_code=code, swatch=sw, price_delta=delta,
                      stock_status=stock, lead_time=lead, is_default=dft, sort=oid, is_active=1))
        db.add(OptionI18n(option_id=oid, lang="zh", name=zh, is_active=1))
        db.add(OptionI18n(option_id=oid, lang="en", name=en, is_active=1))

    # 金融参数（金融计算器数据源）
    db.add(FinanceParam(id=1, term_months=12, annual_rate=0.049, product_name="标准贷"))
    db.add(FinanceParam(id=2, term_months=24, annual_rate=0.051, product_name="尊享贷"))
    db.add(FinanceParam(id=3, term_months=36, annual_rate=0.053, product_name="长轴贷"))
    db.commit()


def main():
    # SQLite 内存库 + StaticPool，复用单连接，避免 :memory: 每连接丢表
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    SessionLocal.configure(bind=eng)

    with SessionLocal() as db:
        seed(db)

    client = TestClient(app)
    fails = []

    # §7.4 配置器数据
    r = client.get("/api/v1/models/101/configurator")
    j = r.json()
    groups = j["data"]["groups"]
    if (j["code"] != 0 or j["data"]["base_price"] != 899000 or len(groups) != 4
            or groups[0]["name"] != "外观颜色" or len(groups[0]["options"]) != 2
            or groups[0]["options"][0]["name"] != "曜石黑"):
        fails.append(("configurator", j))
    print("configurator: base=", j["data"]["base_price"], "groups=", len(groups), "color=", groups[0]["options"][0]["name"])

    # §7.5 算价：选 香槟金(+18000,preorder,30) + 21运动(+15000) + 象牙白(+10000) + 两个选装包(+38000+26000)
    body = {"model_id": 101, "selections": {"color": 2, "wheel": 4, "interior": 6, "packages": [7, 8]}}
    r = client.post("/api/v1/configurator/quote", json=body)
    j = r.json()
    q = j["data"]
    if (j["code"] != 0 or q["total"] != 1006000.0 or q["stock_status"] != "preorder" or q["max_lead_time"] != 30
            or q["base_price"] != 899000):
        fails.append(("quote", j))
    print("quote: total=", q["total"], "stock=", q["stock_status"], "max_lead=", q["max_lead_time"])

    # §7.5 算价校验：必选项未选（空 selections）
    r = client.post("/api/v1/configurator/quote", json={"model_id": 101, "selections": {}})
    if r.json()["code"] != 40000:
        fails.append(("quote-required", r.json()))
    print("quote(empty)->code:", r.json()["code"])

    # §7.6 对比
    r = client.get("/api/v1/models/compare?ids=101,102")
    j = r.json()
    if j["code"] != 0 or len(j["data"]) != 2 or j["data"][0]["model_name"] != "i7" or j["data"][1]["guide_price"] != 499000:
        fails.append(("compare", j))
    print("compare: count=", len(j["data"]), "first=", j["data"][0]["model_name"])

    # 金融参数
    r = client.get("/api/v1/finance/params")
    j = r.json()
    if j["code"] != 0 or len(j["data"]) != 3 or j["data"][0]["term_months"] != 12:
        fails.append(("finance-params", j))
    print("finance-params: count=", len(j["data"]))

    # §7.7 试驾留资：合法提交
    phone = "13800000001"
    r = client.post("/api/v1/leads/test-drive", json={
        "name": "张三", "phone": phone, "city": "北京", "model_id": 101,
        "config_summary": {"color": "香槟金", "total": 1006000},
    })
    j = r.json()
    if j["code"] != 0 or "lead_id" not in j["data"] or j["data"]["lead_id"] <= 0:
        fails.append(("lead-test-drive", j))
    print("lead-test-drive: lead_id=", j["data"].get("lead_id"), "msg=", j["data"].get("message"))

    # §7.7 试驾留资：同手机号 60s 内重复提交应被限流
    r = client.post("/api/v1/leads/test-drive", json={"name": "张三", "phone": phone, "city": "北京"})
    if r.json()["code"] != 42900:
        fails.append(("lead-throttle", r.json()))
    print("lead-test-drive(2nd)->code:", r.json()["code"])

    # §7.7 试驾留资：手机号格式错误
    r = client.post("/api/v1/leads/test-drive", json={"name": "李四", "phone": "123", "city": "上海"})
    if r.json()["code"] != 40012:
        fails.append(("lead-phone-format", r.json()))
    print("lead-test-drive(bad-phone)->code:", r.json()["code"])

    # §7.7 询价留资：合法（intent=finance）
    r = client.post("/api/v1/leads/inquiry", json={
        "name": "王五", "phone": "13900000002", "city": "广州", "model_id": 102, "intent": "finance",
    })
    j = r.json()
    if j["code"] != 0 or "lead_id" not in j["data"]:
        fails.append(("lead-inquiry", j))
    print("lead-inquiry: lead_id=", j["data"].get("lead_id"))

    # §7.7 询价留资：intent 非法
    r = client.post("/api/v1/leads/inquiry", json={"name": "王五", "phone": "13900000003", "intent": "xxx"})
    if r.json()["code"] != 40000:
        fails.append(("lead-inquiry-intent", r.json()))
    print("lead-inquiry(bad-intent)->code:", r.json()["code"])

    if fails:
        print("\n❌ 失败用例:", [f[0] for f in fails])
        for name, payload in fails:
            print(name, payload)
        raise SystemExit(1)
    print("\n✅ 全部 M3 选车深化接口冒烟通过（配置器 / 算价 / 对比 / 金融参数 / 留资 + 限流 + 校验）")


if __name__ == "__main__":
    main()
