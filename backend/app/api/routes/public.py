# =============================================================
# 段功能：M2 公共端路由（C 端公开接口，无需鉴权）
# 说明：实现《开发技术文档》§7.1(品牌) / §7.2(车型列表) / §7.3(车型详情) / §7.9(资讯+Banner)。
#   统一响应信封 {code,message,data}；列表接口分页 {list,total,page,page_size}；
#   i18n 读取回退中文(zh)；公开数据走进程内缓存(60s)。
#   路由前缀 /api/v1 与 §7 / §8 契约保持一致。
# =============================================================

import json
import re
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.cache import make_key, cache_get, cache_set
from app.core.i18n_query import load_i18n, pick, normalize_lang
from app.schemas import ResponseEnvelope
from app.schemas_public import (
    BrandOut,
    ModelListItem,
    ModelListData,
    ModelDetail,
    TrimBrief,
    ColorOption,
    DealerBrief,
    ModelBody,
    ArticleListItem,
    ArticleListData,
    ArticleDetail,
    BannerOut,
    ConfiguratorData,
    OptionGroupOut,
    OptionBrief,
    QuoteRequest,
    QuoteResult,
    QuoteDelta,
    CompareItem,
    FinanceParamOut,
    TestDriveLeadRequest,
    InquiryLeadRequest,
    LeadResponse,
)
from app.models import (
    Brand,
    Series,
    Model,
    Trim,
    OptionGroup,
    Option,
    Article,
    Banner,
    Product,
    Dealer,
    ModelDealer,
    BrandI18n,
    SeriesI18n,
    ModelI18n,
    OptionI18n,
    OptionGroupI18n,
    ArticleI18n,
    TestDriveLead,
    InquiryLead,
    FinanceParam,
)

# 路由前缀对齐契约 §7：/api/v1
router = APIRouter(prefix="/api/v1", tags=["public"])

# 对比路由独立挂载（先于 public_router 注册），避免 /models/{model_id} 抢占 /models/compare
compare_router = APIRouter(prefix="/api/v1", tags=["public"])


# ---------- 小工具：类型安全转换 ----------
def _parse_json_list(raw) -> list:
    """把数据库存储的 JSON 数组字符串解析为 list；解析失败返回空列表。"""
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except Exception:
        return []


def _float(v) -> Optional[float]:
    """Numeric/Decimal 安全转 float；空值返回 None。"""
    return float(v) if v is not None else None


def _iso(v) -> Optional[str]:
    """datetime 安全转 ISO 字符串；空值返回 None。"""
    return v.isoformat() if isinstance(v, datetime) else None


# ========== §7.1 品牌 ==========
@router.get("/brands")
def list_brands(lang: str = Query(None), db: Session = Depends(get_db)):
    """
    品牌列表：返回全部启用品牌。
    每个品牌同时给出 name_zh / name_en，便于前端语言切换而无需二次请求。
    """
    # 缓存键：品牌接口仅受语言影响
    key = make_key("brands", lang=normalize_lang(lang))
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)

    # 仅查启用且未软删的品牌，按 sort 倒序（越大越靠前）
    brands = (
        db.query(Brand)
        .filter(Brand.is_active == 1, Brand.deleted_at.is_(None))
        .order_by(Brand.sort.desc(), Brand.id)
        .all()
    )
    ids = [b.id for b in brands]
    # 批量加载品牌翻译（zh/en）
    i18n = load_i18n(db, BrandI18n, BrandI18n.brand_id, ids)

    data = [
        BrandOut(
            id=b.id,
            brand_code=b.brand_code,
            logo=b.logo,
            country=b.country,
            name_zh=pick(i18n, b.id, "name", "zh"),
            name_en=pick(i18n, b.id, "name", "en"),
            sort=b.sort,
        )
        for b in brands
    ]
    env = ResponseEnvelope(data=[d.model_dump() for d in data])
    cache_set(key, env.model_dump())
    return env


# ========== §7.2 车型列表（多维筛选/排序/分页） ==========
@router.get("/models")
def list_models(
    brand: str = Query(None, description="品牌编码，如 bmw"),
    segment: str = Query(None, description="级别：sedan/suv/coupe/mpv/sport"),
    fuel_type: str = Query(None, description="能源：gasoline/hybrid/ev/phev"),
    price_min: float = Query(None, description="指导价下限（元）"),
    price_max: float = Query(None, description="指导价上限（元）"),
    country: str = Query(None, description="国别，如 德国"),
    seats: int = Query(None, description="座位数（当前数据模型无该字段，参数预留）"),
    sort: str = Query("default", description="排序：price/heat/launch/default"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    lang: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    车型列表：支持品牌/级别/能源/价格区间/国别筛选与排序、分页。
    响应字段 brand_name/series_name/model_name/segment 均按语言本地化。
    """
    lang = normalize_lang(lang)
    # 缓存键包含所有筛选与分页参数，保证不同查询互不串缓存
    key = make_key(
        "models", brand=brand, segment=segment, fuel_type=fuel_type,
        price_min=price_min, price_max=price_max, country=country,
        seats=seats, sort=sort, page=page, page_size=page_size, lang=lang,
    )
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)

    # 基础查询：车型 JOIN 车系 JOIN 品牌（便于取名称与按品牌/国别/级别筛选）
    q = (
        db.query(Model)
        .join(Series, Series.id == Model.series_id)
        .join(Brand, Brand.id == Series.brand_id)
    )
    # 仅查启用且未删除的车型，关联主数据同样要求启用
    q = q.filter(
        Model.is_active == 1, Model.deleted_at.is_(None),
        Series.is_active == 1, Series.deleted_at.is_(None),
        Brand.is_active == 1, Brand.deleted_at.is_(None),
    )
    # 多维筛选
    if brand:
        q = q.filter(Brand.brand_code == brand)
    if segment:
        q = q.filter(Series.segment == segment)
    if fuel_type:
        q = q.filter(Model.fuel_type == fuel_type)
    if price_min is not None:
        q = q.filter(Model.guide_price >= price_min)
    if price_max is not None:
        q = q.filter(Model.guide_price <= price_max)
    if country:
        q = q.filter(Brand.country == country)
    # seats：当前数据模型无对应字段，参数保留但暂不参与过滤（预留扩展）

    # 排序
    if sort == "price":
        q = q.order_by(Model.guide_price.asc())          # 价格升序
    elif sort == "launch":
        q = q.order_by(Model.launch_date.desc())         # 上市日期倒序
    elif sort == "heat":
        q = q.order_by(Model.is_recommended.desc(), Model.id.desc())  # 推荐优先
    else:
        q = q.order_by(Model.id.desc())                  # 默认按 id 倒序（新车型在前）

    total = q.count()
    models = q.offset((page - 1) * page_size).limit(page_size).all()

    # 准备名称翻译所需的实体 id 集合
    series_ids = [m.series_id for m in models]
    brand_ids = []
    series_map = {s.id: s for s in db.query(Series).filter(Series.id.in_(series_ids)).all()} if series_ids else {}
    for s in series_map.values():
        brand_ids.append(s.brand_id)
    brand_map = {b.id: b for b in db.query(Brand).filter(Brand.id.in_(brand_ids)).all()} if brand_ids else {}
    model_ids = [m.id for m in models]

    i18n_brand = load_i18n(db, BrandI18n, BrandI18n.brand_id, brand_ids)
    i18n_series = load_i18n(db, SeriesI18n, SeriesI18n.series_id, series_ids)
    i18n_model = load_i18n(db, ModelI18n, ModelI18n.model_id, model_ids)

    # 封面图来自关联产品（products.cover_url），无则 None
    prods = db.query(Product).filter(Product.model_id.in_(model_ids)).all() if model_ids else []
    cover_map = {p.model_id: p.cover_url for p in prods}

    data = [
        ModelListItem(
            id=m.id,
            brand_name=pick(i18n_brand, series_map[m.series_id].brand_id, "name", lang) if m.series_id in series_map else None,
            series_name=pick(i18n_series, m.series_id, "name", lang),
            model_name=pick(i18n_model, m.id, "name", lang),
            cover_image=cover_map.get(m.id),
            guide_price=_float(m.guide_price),
            fuel_type=m.fuel_type,
            segment=series_map[m.series_id].segment if m.series_id in series_map else None,
            is_recommended=m.is_recommended,
        )
        for m in models
    ]
    env = ResponseEnvelope(data=ModelListData(list=data, total=total, page=page, page_size=page_size))
    cache_set(key, env.model_dump())
    return env


# ========== §7.3 车型详情 ==========
@router.get("/models/{model_id}")
def get_model(model_id: int, lang: str = Query(None), db: Session = Depends(get_db)):
    """车型详情：基础信息 + 图库 + 配置版本 + 颜色 + 在售经销商 + 金融入口标记。"""
    lang = normalize_lang(lang)
    key = make_key("model_detail", model_id=model_id, lang=lang)
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)

    m = db.query(Model).filter(Model.id == model_id, Model.is_active == 1, Model.deleted_at.is_(None)).first()
    if not m:
        # 资源不存在，对应附录 B 错误码 40400
        return ResponseEnvelope(code=40400, message="资源不存在", data=None)

    # 车型名称翻译
    i18n_model = load_i18n(db, ModelI18n, ModelI18n.model_id, [m.id])
    model_name = pick(i18n_model, m.id, "name", lang)

    # 封面 / 图库：来自关联产品表（products）
    prod = db.query(Product).filter(Product.model_id == m.id).first()
    cover_image = prod.cover_url if prod else None
    gallery = _parse_json_list(prod.gallery_urls) if prod else []

    # 配置版本 trims
    trims = (
        db.query(Trim)
        .filter(Trim.model_id == m.id, Trim.is_active == 1, Trim.deleted_at.is_(None))
        .order_by(Trim.id)
        .all()
    )
    trims_out = [
        TrimBrief(trim_name=t.trim_name, price=_float(t.price), power=t.power,
                  transmission=t.transmission, drive=t.drive)
        for t in trims
    ]

    # 颜色（来自配置器 color 分组）
    color_group = (
        db.query(OptionGroup)
        .filter(OptionGroup.model_id == m.id, OptionGroup.group_code == "color",
                OptionGroup.is_active == 1, OptionGroup.deleted_at.is_(None))
        .first()
    )
    colors_out = []
    if color_group:
        opts = (
            db.query(Option)
            .filter(Option.group_id == color_group.id, Option.is_active == 1, Option.deleted_at.is_(None))
            .order_by(Option.sort)
            .all()
        )
        opt_ids = [o.id for o in opts]
        i18n_opt = load_i18n(db, OptionI18n, OptionI18n.option_id, opt_ids)
        colors_out = [
            ColorOption(name=pick(i18n_opt, o.id, "name", lang), swatch=o.swatch,
                        price_delta=_float(o.price_delta))
            for o in opts
        ]

    # 在售经销商概要（经 model_dealer 关联）
    md = db.query(ModelDealer).filter(ModelDealer.model_id == m.id, ModelDealer.is_active == 1).all()
    dealer_ids = [x.dealer_id for x in md]
    dealers = db.query(Dealer).filter(Dealer.id.in_(dealer_ids), Dealer.is_active == 1).all() if dealer_ids else []
    dealers_out = [DealerBrief(id=d.id, name=d.name, city=d.city) for d in dealers]

    detail = ModelDetail(
        id=m.id,
        model_name=model_name,
        guide_price=_float(m.guide_price),
        body=ModelBody(length=m.body_length, width=m.body_width, height=m.body_height,
                       wheelbase=m.wheelbase, trunk=m.trunk_volume),
        cover_image=cover_image,
        gallery=gallery,
        trims=trims_out,
        colors=colors_out,
        dealers=dealers_out,
        finance_available=True,  # M2 阶段金融计算器入口恒开，M3 接入具体方案
    )
    env = ResponseEnvelope(data=detail.model_dump())
    cache_set(key, env.model_dump())
    return env


# ========== §7.9 资讯列表 ==========
@router.get("/articles")
def list_articles(
    category: str = Query(None, description="company_news/industry/event"),
    brand: str = Query(None, description="预留：按品牌筛选（当前未使用）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    lang: str = Query(None),
    db: Session = Depends(get_db),
):
    """资讯列表：仅返回已发布(status=published)且启用的资讯，置顶优先、按发布时间倒序。"""
    lang = normalize_lang(lang)
    key = make_key("articles", category=category, brand=brand, page=page, page_size=page_size, lang=lang)
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)

    q = db.query(Article).filter(Article.is_active == 1, Article.deleted_at.is_(None), Article.status == "published")
    if category:
        q = q.filter(Article.category == category)

    total = q.count()
    arts = (
        q.order_by(Article.is_top.desc(), Article.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    ids = [a.id for a in arts]
    i18n = load_i18n(db, ArticleI18n, ArticleI18n.article_id, ids)

    data = [
        ArticleListItem(
            id=a.id,
            category=a.category,
            cover_url=a.cover_url,
            title=pick(i18n, a.id, "title", lang),
            summary=pick(i18n, a.id, "summary", lang),
            published_at=_iso(a.published_at),
            is_top=a.is_top,
            is_recommended=a.is_recommended,
            author=a.author,
            source=a.source,
        )
        for a in arts
    ]
    env = ResponseEnvelope(data=ArticleListData(list=data, total=total, page=page, page_size=page_size))
    cache_set(key, env.model_dump())
    return env


# ========== §7.9 资讯详情 ==========
@router.get("/articles/{article_id}")
def get_article(article_id: int, lang: str = Query(None), db: Session = Depends(get_db)):
    """资讯详情：标题/摘要/正文按语言本地化；仅已发布资讯可访问。"""
    lang = normalize_lang(lang)
    key = make_key("article_detail", article_id=article_id, lang=lang)
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)

    a = db.query(Article).filter(
        Article.id == article_id, Article.is_active == 1,
        Article.deleted_at.is_(None), Article.status == "published",
    ).first()
    if not a:
        return ResponseEnvelope(code=40400, message="资源不存在", data=None)

    i18n = load_i18n(db, ArticleI18n, ArticleI18n.article_id, [a.id])
    detail = ArticleDetail(
        id=a.id,
        category=a.category,
        cover_url=a.cover_url,
        title=pick(i18n, a.id, "title", lang),
        summary=pick(i18n, a.id, "summary", lang),
        body=pick(i18n, a.id, "body", lang),
        published_at=_iso(a.published_at),
        author=a.author,
        source=a.source,
    )
    env = ResponseEnvelope(data=detail.model_dump())
    cache_set(key, env.model_dump())
    return env


# ========== §7.9 Banner ==========
@router.get("/banners")
def list_banners(position: str = Query(None, description="位置：home_hero 等"), db: Session = Depends(get_db)):
    """Banner 轮播：返回启用且在生效时间窗口内的 Banner；可按 position 过滤。"""
    key = make_key("banners", position=position)
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)

    now = datetime.utcnow()
    q = db.query(Banner).filter(Banner.is_active == 1, Banner.deleted_at.is_(None))
    if position:
        q = q.filter(Banner.position == position)
    banners = q.order_by(Banner.sort.desc(), Banner.id).all()

    # 生效时间窗口：未设置开始/结束视为长期有效
    data = [
        BannerOut(id=b.id, position=b.position, image=b.image, link=b.link, sort=b.sort).model_dump()
        for b in banners
        if (b.start_at is None or b.start_at <= now) and (b.end_at is None or b.end_at >= now)
    ]
    env = ResponseEnvelope(data=data)
    cache_set(key, env.model_dump())
    return env


# =============================================================
# 段功能：M3 选车深化（§7.4 配置器 / §7.5 算价 / §7.6 对比 / 金融参数 / §7.7 留资）
# 说明：配置器/对比/金融参数走缓存 + i18n；算价为写无关纯计算；留资做手机号格式校验与限流。
# =============================================================

# 留资手机号级限流：同手机号 60s 仅允许一次（对应 §7.7 "同手机号 60s 一次"）
LEAD_PHONE_WINDOW = 60  # 秒
_lead_phone_hits: dict[str, float] = {}


def _lead_phone_throttled(phone: str) -> bool:
    """
    手机号级限流判定。
    返回 True 表示命中限流（60s 内重复提交）；否则记录本次时间戳并返回 False。
    """
    now = time.time()
    last = _lead_phone_hits.get(phone)
    if last is not None and now - last < LEAD_PHONE_WINDOW:
        return True
    _lead_phone_hits[phone] = now
    return False


def _parse_dt(s) -> Optional[datetime]:
    """ISO 时间字符串安全转 datetime；空值或格式错误返回 None。"""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


# ========== §7.4 配置器数据 ==========
@router.get("/models/{model_id}/configurator")
def get_configurator(model_id: int, lang: str = Query(None), db: Session = Depends(get_db)):
    """
    配置器数据：返回车型基础价 + 全部选项分组与选项。
    选项名称按语言本地化；缺失翻译回退中文(zh)。
    """
    lang = normalize_lang(lang)
    key = make_key("configurator", model_id=model_id, lang=lang)
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)

    m = db.query(Model).filter(Model.id == model_id, Model.is_active == 1, Model.deleted_at.is_(None)).first()
    if not m:
        return ResponseEnvelope(code=40400, message="资源不存在", data=None)

    base_price = _float(m.guide_price)
    groups = (
        db.query(OptionGroup)
        .filter(OptionGroup.model_id == model_id, OptionGroup.is_active == 1, OptionGroup.deleted_at.is_(None))
        .order_by(OptionGroup.sort)
        .all()
    )
    group_ids = [g.id for g in groups]
    i18n_group = load_i18n(db, OptionGroupI18n, OptionGroupI18n.group_id, group_ids)
    opts = (
        db.query(Option)
        .filter(Option.group_id.in_(group_ids), Option.is_active == 1, Option.deleted_at.is_(None))
        .order_by(Option.sort)
        .all()
    ) if group_ids else []
    opt_ids = [o.id for o in opts]
    i18n_opt = load_i18n(db, OptionI18n, OptionI18n.option_id, opt_ids)

    # 选项按 group_id 归类，便于逐组拼装
    by_group: dict[int, list] = {}
    for o in opts:
        by_group.setdefault(o.group_id, []).append(o)

    groups_out = [
        OptionGroupOut(
            group_code=g.group_code,
            name=pick(i18n_group, g.id, "name", lang),
            is_required=g.is_required,
            max_select=g.max_select,
            options=[
                OptionBrief(
                    id=o.id,
                    name=pick(i18n_opt, o.id, "name", lang),
                    swatch=o.swatch,
                    price_delta=_float(o.price_delta),
                    stock_status=o.stock_status,
                    lead_time=o.lead_time,
                    is_default=o.is_default,
                )
                for o in by_group.get(g.id, [])
            ],
        )
        for g in groups
    ]
    data = ConfiguratorData(base_price=base_price, groups=groups_out)
    env = ResponseEnvelope(data=data.model_dump())
    cache_set(key, env.model_dump())
    return env


# ========== §7.5 配置算价 ==========
@router.post("/configurator/quote")
def quote(body: QuoteRequest, db: Session = Depends(get_db)):
    """
    配置算价：total = 基础价 + Σ加价；库存取选项最差状态；交付取最大 lead_time。
    后端校验：必选项是否选择、max_select 上限、互斥分组 exclude_groups。
    """
    # 车型必须存在且在售
    m = db.query(Model).filter(Model.id == body.model_id, Model.is_active == 1, Model.deleted_at.is_(None)).first()
    if not m:
        return ResponseEnvelope(code=40400, message="资源不存在", data=None)
    base = float(m.guide_price or 0)

    # 把请求选型按 group_code 归类（packages 为多选，归属 package 分组）
    sel = body.selections
    selected_by_group: dict[str, list[int]] = {}
    if sel.color is not None:
        selected_by_group.setdefault("color", []).append(sel.color)
    if sel.wheel is not None:
        selected_by_group.setdefault("wheel", []).append(sel.wheel)
    if sel.interior is not None:
        selected_by_group.setdefault("interior", []).append(sel.interior)
    if sel.packages:
        selected_by_group.setdefault("package", []).extend(sel.packages)

    # 加载该车型全部选项分组，用于校验 is_required / max_select / exclude_groups
    groups = (
        db.query(OptionGroup)
        .filter(OptionGroup.model_id == m.id, OptionGroup.is_active == 1, OptionGroup.deleted_at.is_(None))
        .all()
    )
    group_map = {g.group_code: g for g in groups}
    group_id_to_code = {g.id: g.group_code for g in groups}

    # 校验：必选、max_select、互斥
    for gcode, g in group_map.items():
        picked = selected_by_group.get(gcode, [])
        if g.is_required and len(picked) == 0:
            return ResponseEnvelope(code=40000, message=f"必选项未选择：{gcode}", data=None)
        if len(picked) > (g.max_select or 1):
            return ResponseEnvelope(code=40000, message=f"超过最大可选数量：{gcode}", data=None)
        if g.exclude_groups:
            for ex in _parse_json_list(g.exclude_groups):  # ex 为互斥的 group_code
                if ex in selected_by_group and selected_by_group[ex]:
                    return ResponseEnvelope(code=40000, message=f"互斥分组不可同时选择：{gcode}/{ex}", data=None)

    # 汇总去重所有选中选项 id，加载并校验归属该车型
    all_ids: list[int] = []
    for ids in selected_by_group.values():
        all_ids.extend(ids)
    seen = set()
    uniq = []
    for oid in all_ids:
        if oid not in seen:
            seen.add(oid)
            uniq.append(oid)
    opts = {o.id: o for o in db.query(Option).filter(Option.id.in_(uniq)).all()} if uniq else {}
    for oid in uniq:
        o = opts.get(oid)
        if o is None:
            return ResponseEnvelope(code=40000, message="选项不存在", data=None)
        gcode = group_id_to_code.get(o.group_id)
        if gcode is None or gcode not in group_map or group_map[gcode].model_id != m.id:
            return ResponseEnvelope(code=40000, message="选项不属于该车型", data=None)

    # 算价：total = base + Σ price_delta；库存取最差；交付取最大周期
    deltas = []
    total = base
    worst_rank = {"in_stock": 0, "preorder": 1, "eol": 2}
    stock_status = "in_stock"
    max_lead = 0
    for oid in uniq:
        o = opts[oid]
        gcode = group_id_to_code.get(o.group_id, "")
        delta = _float(o.price_delta) or 0.0
        deltas.append(QuoteDelta(group=gcode, option=o.option_code or str(o.id), price_delta=delta))
        total += delta
        if worst_rank.get(o.stock_status or "in_stock", 0) > worst_rank.get(stock_status, 0):
            stock_status = o.stock_status or "in_stock"
        if o.lead_time and o.lead_time > max_lead:
            max_lead = o.lead_time

    result = QuoteResult(
        base_price=base,
        deltas=deltas,
        total=round(total, 2),
        stock_status=stock_status,
        max_lead_time=max_lead,
    )
    return ResponseEnvelope(data=result.model_dump())


# ========== §7.6 车型对比 ==========
@compare_router.get("/models/compare")
def compare_models(
    ids: str = Query(..., description="逗号分隔车型 id，如 101,102,103"),
    lang: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    车型对比：按传入 id 顺序返回对比项；缺失项返回占位（前端显示"—"）。
    最多对比 5 个，防止参数滥用。
    """
    lang = normalize_lang(lang)
    try:
        id_list = [int(x) for x in ids.split(",") if x.strip()]
    except ValueError:
        return ResponseEnvelope(code=40000, message="ids 格式错误", data=None)
    # 去重并限制数量
    id_list = list(dict.fromkeys(id_list))[:5]
    if not id_list:
        return ResponseEnvelope(code=40000, message="ids 不能为空", data=None)

    models = db.query(Model).filter(Model.id.in_(id_list), Model.is_active == 1, Model.deleted_at.is_(None)).all()
    model_map = {mm.id: mm for mm in models}
    series_ids = [mm.series_id for mm in models]
    series_map = {s.id: s for s in db.query(Series).filter(Series.id.in_(series_ids)).all()} if series_ids else {}
    i18n_model = load_i18n(db, ModelI18n, ModelI18n.model_id, id_list)

    items = []
    for mid in id_list:
        mm = model_map.get(mid)
        if not mm:
            # 缺失项占位，前端以 "—" 展示
            items.append(CompareItem(id=mid))
            continue
        trims = (
            db.query(Trim)
            .filter(Trim.model_id == mid, Trim.is_active == 1, Trim.deleted_at.is_(None))
            .all()
        )
        seg = series_map[mm.series_id].segment if mm.series_id in series_map else None
        items.append(
            CompareItem(
                id=mid,
                model_name=pick(i18n_model, mid, "name", lang),
                guide_price=_float(mm.guide_price),
                fuel_type=mm.fuel_type,
                segment=seg,
                body=ModelBody(
                    length=mm.body_length, width=mm.body_width,
                    height=mm.body_height, wheelbase=mm.wheelbase, trunk=mm.trunk_volume,
                ),
                power=trims[0].power if trims else None,
                trims_count=len(trims),
            )
        )
    return ResponseEnvelope(data=[it.model_dump() for it in items])


# ========== 金融参数（金融计算器数据来源） ==========
@router.get("/finance/params")
def finance_params(db: Session = Depends(get_db)):
    """金融方案参数列表：供前台金融计算器按月供估算使用（只读，走缓存）。"""
    key = make_key("finance_params")
    hit = cache_get(key)
    if hit is not None:
        return ResponseEnvelope(**hit)
    params = db.query(FinanceParam).order_by(FinanceParam.term_months).all()
    data = [
        FinanceParamOut(term_months=p.term_months, annual_rate=_float(p.annual_rate), product_name=p.product_name).model_dump()
        for p in params
    ]
    env = ResponseEnvelope(data=data)
    cache_set(key, env.model_dump())
    return env


# ========== §7.7 留资：试驾 / 询价 ==========
PHONE_RE = re.compile(r"^1[3-9]\d{9}$")  # 中国大陆手机号


@router.post("/leads/test-drive")
def create_test_drive(body: TestDriveLeadRequest, db: Session = Depends(get_db)):
    """试驾留资：手机号格式校验 + 同手机号 60s 限流；写入默认初始状态后返回 lead_id。"""
    if not PHONE_RE.match(body.phone or ""):
        return ResponseEnvelope(code=40012, message="手机号格式不正确", data=None)
    if _lead_phone_throttled(body.phone):
        return ResponseEnvelope(code=42900, message="请求过于频繁，请稍后再试", data=None)

    lead = TestDriveLead(
        name=body.name,
        phone=body.phone,
        city=body.city,
        brand_id=body.brand_id,
        model_id=body.model_id,
        config_summary=json.dumps(body.config_summary, ensure_ascii=False) if body.config_summary is not None else None,
        preferred_dealer_id=body.preferred_dealer_id,
        preferred_time=_parse_dt(body.preferred_time),
        remark=body.remark,
        source="web",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return ResponseEnvelope(data=LeadResponse(lead_id=lead.id, message="已收到，顾问将联系您").model_dump())


@router.post("/leads/inquiry")
def create_inquiry(body: InquiryLeadRequest, db: Session = Depends(get_db)):
    """询价留资：在试驾校验基础上额外要求 intent 必填之一 trade_in/finance/stock。"""
    if not PHONE_RE.match(body.phone or ""):
        return ResponseEnvelope(code=40012, message="手机号格式不正确", data=None)
    if _lead_phone_throttled(body.phone):
        return ResponseEnvelope(code=42900, message="请求过于频繁，请稍后再试", data=None)
    if body.intent not in ("trade_in", "finance", "stock"):
        return ResponseEnvelope(code=40000, message="intent 不合法（应为 trade_in/finance/stock）", data=None)

    lead = InquiryLead(
        name=body.name,
        phone=body.phone,
        city=body.city,
        brand_id=body.brand_id,
        model_id=body.model_id,
        intent=body.intent,
        remark=body.remark,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return ResponseEnvelope(data=LeadResponse(lead_id=lead.id, message="已收到，顾问将联系您").model_dump())
