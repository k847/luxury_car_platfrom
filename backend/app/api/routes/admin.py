# =============================================================
# 段功能：M4 后台管理路由（§8 鉴权与后台端）
# 说明：实现《开发技术文档》§8 全部后台接口，统一挂在 /api/v1/admin 前缀：
#   - §8.2 车型/配置器 CRUD（brands/series/models/trims/option-groups/options，双语事务）
#   - §8.3 内容/Banner CRUD（articles/banners）
#   - §8.4 线索管理（test-drive/inquiry 列表+assign+advance 状态机）
#   - §8.5 经销商 CRUD
#   - §8.6 系统/RBAC/审计/看板（roles/permissions/audit-logs/dashboard/system-config/seo）
# 所有接口 require_permission 门控（支持通配符前缀匹配，见 core/deps.py）；
# 写操作由 AuditMiddleware 自动落库 audit_logs。统一响应信封 {code,message,data}。
# =============================================================

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.schemas import ResponseEnvelope
from app.schemas_admin import (
    BrandUpsert, SeriesUpsert, ModelUpsert, TrimUpsert,
    OptionGroupUpsert, OptionUpsert, ArticleUpsert, BannerUpsert,
    LeadAssign, LeadAdvance, DealerUpsert,
    RoleUpsert, SystemConfigUpsert, SeoUpsert,
)
from app.models import (
    Brand, Series, Model, Trim, OptionGroup, Option, Article, Banner,
    TestDriveLead, InquiryLead, Dealer, AdminUser, Role, Permission,
    RolePermission, AuditLog, SystemConfig, FinanceParam,
    BrandI18n, SeriesI18n, ModelI18n, OptionGroupI18n, OptionI18n,
    ArticleI18n,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ---------- 小工具：类型安全转换 ----------
def _float(v):
    return float(v) if v is not None else None


def _iso(v):
    return v.isoformat() if isinstance(v, datetime) else None


def _set_i18n(db, I18nModel, fk, eid, lang, **vals):
    """写入/更新一条翻译（事务内调用，由调用方 commit）。"""
    row = db.query(I18nModel).filter(I18nModel.__table__.c[fk] == eid, I18nModel.lang == lang).first()
    if row:
        for k, v in vals.items():
            setattr(row, k, v)
    else:
        db.add(I18nModel(**{fk: eid, "lang": lang, **vals, "is_active": 1}))


# =============================================================
# §8.2 车型 / 配置器 CRUD
# =============================================================

# ---------- 品牌 ----------
@router.get("/brands", dependencies=[Depends(require_permission("brand:view"))])
def admin_list_brands(db: Session = Depends(get_db)):
    """后台品牌列表：含双语名称。"""
    brands = db.query(Brand).filter(Brand.deleted_at.is_(None)).order_by(Brand.sort.desc()).all()
    data = [{
        "id": b.id, "brand_code": b.brand_code, "logo": b.logo, "country": b.country,
        "sort": b.sort, "is_active": b.is_active,
        "name_zh": b.name_zh if hasattr(b, "name_zh") else None, "name_en": None,
    } for b in brands]
    # 名称从 brand_i18n 取（后台统一展示双语）
    out = []
    for b in brands:
        zh = db.query(BrandI18n).filter(BrandI18n.brand_id == b.id, BrandI18n.lang == "zh").first()
        en = db.query(BrandI18n).filter(BrandI18n.brand_id == b.id, BrandI18n.lang == "en").first()
        out.append({
            "id": b.id, "brand_code": b.brand_code, "logo": b.logo, "country": b.country,
            "sort": b.sort, "is_active": b.is_active,
            "name_zh": zh.name if zh else None, "name_en": en.name if en else None,
        })
    return ResponseEnvelope(data=out)


@router.post("/brands", dependencies=[Depends(require_permission("brand:create"))])
def admin_create_brand(body: BrandUpsert, db: Session = Depends(get_db)):
    """后台创建品牌：事务内同时写 brands + brand_i18n 双语。"""
    b = Brand(brand_code=body.brand_code, logo=body.logo, country=body.country,
              sort=body.sort, is_active=body.is_active)
    db.add(b)
    db.flush()
    _set_i18n(db, BrandI18n, "brand_id", b.id, "zh", name=body.name_zh)
    _set_i18n(db, BrandI18n, "brand_id", b.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": b.id})


@router.put("/brands/{brand_id}", dependencies=[Depends(require_permission("brand:update"))])
def admin_update_brand(brand_id: int, body: BrandUpsert, db: Session = Depends(get_db)):
    """后台更新品牌：更新主表 + 双语翻译。"""
    b = db.get(Brand, brand_id)
    if not b or b.deleted_at:
        return ResponseEnvelope(code=40400, message="品牌不存在", data=None)
    b.brand_code = body.brand_code
    b.logo = body.logo
    b.country = body.country
    b.sort = body.sort
    b.is_active = body.is_active
    _set_i18n(db, BrandI18n, "brand_id", b.id, "zh", name=body.name_zh)
    _set_i18n(db, BrandI18n, "brand_id", b.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": b.id})


@router.delete("/brands/{brand_id}", dependencies=[Depends(require_permission("brand:delete"))])
def admin_delete_brand(brand_id: int, db: Session = Depends(get_db)):
    """后台删除品牌：软删除。"""
    b = db.get(Brand, brand_id)
    if not b or b.deleted_at:
        return ResponseEnvelope(code=40400, message="品牌不存在", data=None)
    b.deleted_at = datetime.utcnow()
    b.is_active = 0
    db.commit()
    return ResponseEnvelope(data=None)


# ---------- 车系 ----------
@router.get("/series", dependencies=[Depends(require_permission("series:view"))])
def admin_list_series(brand_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """后台车系列表：按品牌筛选，含双语名称。"""
    q = db.query(Series).filter(Series.deleted_at.is_(None))
    if brand_id:
        q = q.filter(Series.brand_id == brand_id)
    out = []
    for s in q.all():
        zh = db.query(SeriesI18n).filter(SeriesI18n.series_id == s.id, SeriesI18n.lang == "zh").first()
        en = db.query(SeriesI18n).filter(SeriesI18n.series_id == s.id, SeriesI18n.lang == "en").first()
        out.append({"id": s.id, "brand_id": s.brand_id, "series_code": s.series_code,
                    "segment": s.segment, "sort": s.sort, "is_active": s.is_active,
                    "name_zh": zh.name if zh else None, "name_en": en.name if en else None})
    return ResponseEnvelope(data=out)


@router.post("/series", dependencies=[Depends(require_permission("series:create"))])
def admin_create_series(body: SeriesUpsert, db: Session = Depends(get_db)):
    s = Series(brand_id=body.brand_id, series_code=body.series_code, segment=body.segment,
               sort=body.sort, is_active=body.is_active)
    db.add(s)
    db.flush()
    _set_i18n(db, SeriesI18n, "series_id", s.id, "zh", name=body.name_zh)
    _set_i18n(db, SeriesI18n, "series_id", s.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": s.id})


@router.put("/series/{series_id}", dependencies=[Depends(require_permission("series:update"))])
def admin_update_series(series_id: int, body: SeriesUpsert, db: Session = Depends(get_db)):
    s = db.get(Series, series_id)
    if not s or s.deleted_at:
        return ResponseEnvelope(code=40400, message="车系不存在", data=None)
    s.brand_id = body.brand_id
    s.series_code = body.series_code
    s.segment = body.segment
    s.sort = body.sort
    s.is_active = body.is_active
    _set_i18n(db, SeriesI18n, "series_id", s.id, "zh", name=body.name_zh)
    _set_i18n(db, SeriesI18n, "series_id", s.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": s.id})


@router.delete("/series/{series_id}", dependencies=[Depends(require_permission("series:delete"))])
def admin_delete_series(series_id: int, db: Session = Depends(get_db)):
    s = db.get(Series, series_id)
    if not s or s.deleted_at:
        return ResponseEnvelope(code=40400, message="车系不存在", data=None)
    s.deleted_at = datetime.utcnow()
    s.is_active = 0
    db.commit()
    return ResponseEnvelope(data=None)


# ---------- 车型 ----------
@router.get("/models", dependencies=[Depends(require_permission("model:view"))])
def admin_list_models(
    brand: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """后台车型列表：支持品牌/级别筛选 + 分页 + 双语名称。"""
    q = db.query(Model).join(Series, Series.id == Model.series_id).join(Brand, Brand.id == Series.brand_id)
    q = q.filter(Model.deleted_at.is_(None), Series.deleted_at.is_(None), Brand.deleted_at.is_(None))
    if brand:
        q = q.filter(Brand.brand_code == brand)
    if segment:
        q = q.filter(Series.segment == segment)
    total = q.count()
    rows = q.order_by(Model.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    out = []
    for m in rows:
        zh = db.query(ModelI18n).filter(ModelI18n.model_id == m.id, ModelI18n.lang == "zh").first()
        en = db.query(ModelI18n).filter(ModelI18n.model_id == m.id, ModelI18n.lang == "en").first()
        out.append({"id": m.id, "series_id": m.series_id, "model_code": m.model_code,
                    "fuel_type": m.fuel_type, "guide_price": _float(m.guide_price),
                    "is_recommended": m.is_recommended, "status": m.status, "is_active": m.is_active,
                    "name_zh": zh.name if zh else None, "name_en": en.name if en else None})
    return ResponseEnvelope(data={"list": out, "total": total, "page": page, "page_size": page_size})


@router.post("/models", dependencies=[Depends(require_permission("model:create"))])
def admin_create_model(body: ModelUpsert, db: Session = Depends(get_db)):
    m = Model(series_id=body.series_id, model_code=body.model_code, fuel_type=body.fuel_type,
              guide_price=body.guide_price, is_recommended=body.is_recommended,
              status=body.status, is_active=body.is_active)
    db.add(m)
    db.flush()
    _set_i18n(db, ModelI18n, "model_id", m.id, "zh", name=body.name_zh)
    _set_i18n(db, ModelI18n, "model_id", m.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": m.id})


@router.put("/models/{model_id}", dependencies=[Depends(require_permission("model:update"))])
def admin_update_model(model_id: int, body: ModelUpsert, db: Session = Depends(get_db)):
    m = db.get(Model, model_id)
    if not m or m.deleted_at:
        return ResponseEnvelope(code=40400, message="车型不存在", data=None)
    m.series_id = body.series_id
    m.model_code = body.model_code
    m.fuel_type = body.fuel_type
    m.guide_price = body.guide_price
    m.is_recommended = body.is_recommended
    m.status = body.status
    m.is_active = body.is_active
    _set_i18n(db, ModelI18n, "model_id", m.id, "zh", name=body.name_zh)
    _set_i18n(db, ModelI18n, "model_id", m.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": m.id})


@router.delete("/models/{model_id}", dependencies=[Depends(require_permission("model:delete"))])
def admin_delete_model(model_id: int, db: Session = Depends(get_db)):
    m = db.get(Model, model_id)
    if not m or m.deleted_at:
        return ResponseEnvelope(code=40400, message="车型不存在", data=None)
    m.deleted_at = datetime.utcnow()
    m.is_active = 0
    db.commit()
    return ResponseEnvelope(data=None)


# ---------- 配置版本（trims） ----------
@router.get("/models/{model_id}/trims", dependencies=[Depends(require_permission("model:view"))])
def admin_list_trims(model_id: int, db: Session = Depends(get_db)):
    trims = db.query(Trim).filter(Trim.model_id == model_id, Trim.deleted_at.is_(None)).all()
    return ResponseEnvelope(data=[{
        "id": t.id, "trim_name": t.trim_name, "price": _float(t.price), "power": t.power,
        "transmission": t.transmission, "drive": t.drive, "is_active": t.is_active,
    } for t in trims])


@router.post("/models/{model_id}/trims", dependencies=[Depends(require_permission("model:create"))])
def admin_create_trim(model_id: int, body: TrimUpsert, db: Session = Depends(get_db)):
    t = Trim(model_id=model_id, trim_name=body.trim_name, price=body.price, power=body.power,
             transmission=body.transmission, drive=body.drive, is_active=body.is_active)
    db.add(t)
    db.commit()
    return ResponseEnvelope(data={"id": t.id})


# ---------- 配置器：选项分组 / 选项 ----------
@router.get("/option-groups", dependencies=[Depends(require_permission("config:view"))])
def admin_list_option_groups(model_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(OptionGroup).filter(OptionGroup.deleted_at.is_(None))
    if model_id:
        q = q.filter(OptionGroup.model_id == model_id)
    out = []
    for g in q.all():
        zh = db.query(OptionGroupI18n).filter(OptionGroupI18n.group_id == g.id, OptionGroupI18n.lang == "zh").first()
        en = db.query(OptionGroupI18n).filter(OptionGroupI18n.group_id == g.id, OptionGroupI18n.lang == "en").first()
        out.append({"id": g.id, "model_id": g.model_id, "group_code": g.group_code,
                    "is_required": g.is_required, "max_select": g.max_select,
                    "exclude_groups": g.exclude_groups, "sort": g.sort, "is_active": g.is_active,
                    "name_zh": zh.name if zh else None, "name_en": en.name if en else None})
    return ResponseEnvelope(data=out)


@router.post("/option-groups", dependencies=[Depends(require_permission("config:create"))])
def admin_create_option_group(body: OptionGroupUpsert, db: Session = Depends(get_db)):
    g = OptionGroup(model_id=body.model_id,
                    group_code=body.group_code, is_required=body.is_required,
                    max_select=body.max_select, exclude_groups=body.exclude_groups,
                    sort=body.sort, is_active=body.is_active)
    db.add(g)
    db.flush()
    _set_i18n(db, OptionGroupI18n, "group_id", g.id, "zh", name=body.name_zh)
    _set_i18n(db, OptionGroupI18n, "group_id", g.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": g.id})


@router.get("/options", dependencies=[Depends(require_permission("config:view"))])
def admin_list_options(group_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(Option).filter(Option.deleted_at.is_(None))
    if group_id:
        q = q.filter(Option.group_id == group_id)
    out = []
    for o in q.all():
        zh = db.query(OptionI18n).filter(OptionI18n.option_id == o.id, OptionI18n.lang == "zh").first()
        en = db.query(OptionI18n).filter(OptionI18n.option_id == o.id, OptionI18n.lang == "en").first()
        out.append({"id": o.id, "group_id": o.group_id, "option_code": o.option_code,
                    "swatch": o.swatch, "price_delta": _float(o.price_delta),
                    "stock_status": o.stock_status, "lead_time": o.lead_time,
                    "is_default": o.is_default, "sort": o.sort, "is_active": o.is_active,
                    "name_zh": zh.name if zh else None, "name_en": en.name if en else None})
    return ResponseEnvelope(data=out)


@router.post("/options", dependencies=[Depends(require_permission("config:create"))])
def admin_create_option(body: OptionUpsert, db: Session = Depends(get_db)):
    o = Option(group_id=body.group_id, option_code=body.option_code, swatch=body.swatch,
               price_delta=body.price_delta, stock_status=body.stock_status,
               lead_time=body.lead_time, is_default=body.is_default, sort=body.sort,
               is_active=body.is_active)
    db.add(o)
    db.flush()
    _set_i18n(db, OptionI18n, "option_id", o.id, "zh", name=body.name_zh)
    _set_i18n(db, OptionI18n, "option_id", o.id, "en", name=body.name_en)
    db.commit()
    return ResponseEnvelope(data={"id": o.id})


# =============================================================
# §8.3 内容 / Banner CRUD
# =============================================================
@router.get("/articles", dependencies=[Depends(require_permission("content:view"))])
def admin_list_articles(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """后台资讯列表：含双语标题/摘要/正文。"""
    q = db.query(Article).filter(Article.deleted_at.is_(None))
    if category:
        q = q.filter(Article.category == category)
    if status:
        q = q.filter(Article.status == status)
    total = q.count()
    rows = q.order_by(Article.is_top.desc(), Article.published_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()
    out = []
    for a in rows:
        zh = db.query(ArticleI18n).filter(ArticleI18n.article_id == a.id, ArticleI18n.lang == "zh").first()
        en = db.query(ArticleI18n).filter(ArticleI18n.article_id == a.id, ArticleI18n.lang == "en").first()
        out.append({"id": a.id, "category": a.category, "cover_url": a.cover_url,
                    "author": a.author, "source": a.source, "status": a.status,
                    "is_top": a.is_top, "is_recommended": a.is_recommended,
                    "published_at": _iso(a.published_at), "is_active": a.is_active,
                    "title_zh": zh.title if zh else None, "summary_zh": zh.summary if zh else None,
                    "title_en": en.title if en else None, "summary_en": en.summary if en else None})
    return ResponseEnvelope(data={"list": out, "total": total, "page": page, "page_size": page_size})


@router.post("/articles", dependencies=[Depends(require_permission("content:create"))])
def admin_create_article(body: ArticleUpsert, db: Session = Depends(get_db)):
    a = Article(category=body.category, cover_url=body.cover_url, author=body.author,
                source=body.source, status=body.status, is_top=body.is_top,
                is_recommended=body.is_recommended, is_active=body.is_active,
                published_at=datetime.utcnow() if body.status == "published" else None)
    db.add(a)
    db.flush()
    _set_i18n(db, ArticleI18n, "article_id", a.id, "zh", title=body.title_zh,
              summary=body.summary_zh, body=body.body_zh)
    if body.title_en:
        _set_i18n(db, ArticleI18n, "article_id", a.id, "en", title=body.title_en,
                  summary=body.summary_en, body=body.body_en)
    db.commit()
    return ResponseEnvelope(data={"id": a.id})


@router.put("/articles/{article_id}", dependencies=[Depends(require_permission("content:update"))])
def admin_update_article(article_id: int, body: ArticleUpsert, db: Session = Depends(get_db)):
    a = db.get(Article, article_id)
    if not a or a.deleted_at:
        return ResponseEnvelope(code=40400, message="资讯不存在", data=None)
    a.category = body.category
    a.cover_url = body.cover_url
    a.author = body.author
    a.source = body.source
    a.status = body.status
    a.is_top = body.is_top
    a.is_recommended = body.is_recommended
    a.is_active = body.is_active
    if body.status == "published" and a.published_at is None:
        a.published_at = datetime.utcnow()
    _set_i18n(db, ArticleI18n, "article_id", a.id, "zh", title=body.title_zh,
              summary=body.summary_zh, body=body.body_zh)
    if body.title_en:
        _set_i18n(db, ArticleI18n, "article_id", a.id, "en", title=body.title_en,
                  summary=body.summary_en, body=body.body_en)
    db.commit()
    return ResponseEnvelope(data={"id": a.id})


@router.delete("/articles/{article_id}", dependencies=[Depends(require_permission("content:delete"))])
def admin_delete_article(article_id: int, db: Session = Depends(get_db)):
    a = db.get(Article, article_id)
    if not a or a.deleted_at:
        return ResponseEnvelope(code=40400, message="资讯不存在", data=None)
    a.deleted_at = datetime.utcnow()
    a.is_active = 0
    db.commit()
    return ResponseEnvelope(data=None)


@router.get("/banners", dependencies=[Depends(require_permission("banner:view"))])
def admin_list_banners(position: Optional[str] = Query(None), db: Session = Depends(get_db)):
    q = db.query(Banner).filter(Banner.deleted_at.is_(None))
    if position:
        q = q.filter(Banner.position == position)
    return ResponseEnvelope(data=[{
        "id": b.id, "position": b.position, "image": b.image, "link": b.link,
        "start_at": _iso(b.start_at), "end_at": _iso(b.end_at), "sort": b.sort,
        "is_active": b.is_active,
    } for b in q.order_by(Banner.sort.desc()).all()])


@router.post("/banners", dependencies=[Depends(require_permission("banner:create"))])
def admin_create_banner(body: BannerUpsert, db: Session = Depends(get_db)):
    b = Banner(position=body.position, image=body.image, link=body.link,
               start_at=body.start_at, end_at=body.end_at, sort=body.sort, is_active=body.is_active)
    db.add(b)
    db.commit()
    return ResponseEnvelope(data={"id": b.id})


@router.put("/banners/{banner_id}", dependencies=[Depends(require_permission("banner:update"))])
def admin_update_banner(banner_id: int, body: BannerUpsert, db: Session = Depends(get_db)):
    b = db.get(Banner, banner_id)
    if not b or b.deleted_at:
        return ResponseEnvelope(code=40400, message="Banner 不存在", data=None)
    b.position = body.position
    b.image = body.image
    b.link = body.link
    b.start_at = body.start_at
    b.end_at = body.end_at
    b.sort = body.sort
    b.is_active = body.is_active
    db.commit()
    return ResponseEnvelope(data={"id": b.id})


@router.delete("/banners/{banner_id}", dependencies=[Depends(require_permission("banner:delete"))])
def admin_delete_banner(banner_id: int, db: Session = Depends(get_db)):
    b = db.get(Banner, banner_id)
    if not b or b.deleted_at:
        return ResponseEnvelope(code=40400, message="Banner 不存在", data=None)
    b.deleted_at = datetime.utcnow()
    b.is_active = 0
    db.commit()
    return ResponseEnvelope(data=None)


# =============================================================
# §8.4 线索管理（状态机 + 分配）
# =============================================================
# 试驾状态机：pending → contacted → arrived → deal / invalid
TEST_DRIVE_FLOW = {
    "pending": {"contacted", "invalid"},
    "contacted": {"arrived", "invalid"},
    "arrived": {"deal", "invalid"},
}
# 询价状态机：new → processing → quoted → deal / invalid
INQUIRY_FLOW = {
    "new": {"processing", "invalid"},
    "processing": {"quoted", "invalid"},
    "quoted": {"deal", "invalid"},
}


def _advance_lead(db, lead, to_status, flow, perm):
    """通用状态机推进：仅允许相邻或到终态；越级抛 40022。"""
    if to_status not in flow.get(lead.status, set()):
        return ResponseEnvelope(code=40022, message="状态流转不合法（仅允许相邻或到终态）", data=None)
    lead.status = to_status
    db.commit()
    return ResponseEnvelope(data={"id": lead.id, "status": to_status})


@router.get("/leads/test-drive", dependencies=[Depends(require_permission("lead.test_drive:view"))])
def admin_list_test_drive(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """试驾线索列表：支持状态/城市/跟进人筛选 + 分页。"""
    q = db.query(TestDriveLead)
    if status:
        q = q.filter(TestDriveLead.status == status)
    if city:
        q = q.filter(TestDriveLead.city == city)
    if owner_id:
        q = q.filter(TestDriveLead.owner_id == owner_id)
    total = q.count()
    rows = q.order_by(TestDriveLead.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseEnvelope(data={"list": [{
        "id": l.id, "name": l.name, "phone": l.phone, "city": l.city,
        "brand_id": l.brand_id, "model_id": l.model_id, "status": l.status,
        "owner_id": l.owner_id, "created_at": _iso(l.created_at),
        "preferred_dealer_id": l.preferred_dealer_id, "preferred_time": _iso(l.preferred_time),
        "remark": l.remark, "source": l.source,
    } for l in rows], "total": total, "page": page, "page_size": page_size})


@router.post("/leads/test-drive/{lead_id}/assign", dependencies=[Depends(require_permission("lead.test_drive:assign"))])
def admin_assign_test_drive(lead_id: int, body: LeadAssign, db: Session = Depends(get_db)):
    l = db.get(TestDriveLead, lead_id)
    if not l:
        return ResponseEnvelope(code=40400, message="线索不存在", data=None)
    l.owner_id = body.owner_id
    db.commit()
    return ResponseEnvelope(data={"id": l.id, "owner_id": body.owner_id})


@router.post("/leads/test-drive/{lead_id}/advance", dependencies=[Depends(require_permission("lead.test_drive:advance"))])
def admin_advance_test_drive(lead_id: int, body: LeadAdvance, db: Session = Depends(get_db)):
    l = db.get(TestDriveLead, lead_id)
    if not l:
        return ResponseEnvelope(code=40400, message="线索不存在", data=None)
    return _advance_lead(db, l, body.to_status, TEST_DRIVE_FLOW, "lead.test_drive:advance")


@router.get("/leads/inquiry", dependencies=[Depends(require_permission("lead.inquiry:view"))])
def admin_list_inquiry(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """询价线索列表。"""
    q = db.query(InquiryLead)
    if status:
        q = q.filter(InquiryLead.status == status)
    if city:
        q = q.filter(InquiryLead.city == city)
    if owner_id:
        q = q.filter(InquiryLead.owner_id == owner_id)
    total = q.count()
    rows = q.order_by(InquiryLead.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseEnvelope(data={"list": [{
        "id": l.id, "name": l.name, "phone": l.phone, "city": l.city,
        "brand_id": l.brand_id, "model_id": l.model_id, "intent": l.intent,
        "status": l.status, "owner_id": l.owner_id, "created_at": _iso(l.created_at),
        "remark": l.remark,
    } for l in rows], "total": total, "page": page, "page_size": page_size})


@router.post("/leads/inquiry/{lead_id}/assign", dependencies=[Depends(require_permission("lead.inquiry:assign"))])
def admin_assign_inquiry(lead_id: int, body: LeadAssign, db: Session = Depends(get_db)):
    l = db.get(InquiryLead, lead_id)
    if not l:
        return ResponseEnvelope(code=40400, message="线索不存在", data=None)
    l.owner_id = body.owner_id
    db.commit()
    return ResponseEnvelope(data={"id": l.id, "owner_id": body.owner_id})


@router.post("/leads/inquiry/{lead_id}/advance", dependencies=[Depends(require_permission("lead.inquiry:advance"))])
def admin_advance_inquiry(lead_id: int, body: LeadAdvance, db: Session = Depends(get_db)):
    l = db.get(InquiryLead, lead_id)
    if not l:
        return ResponseEnvelope(code=40400, message="线索不存在", data=None)
    return _advance_lead(db, l, body.to_status, INQUIRY_FLOW, "lead.inquiry:advance")


# =============================================================
# §8.5 经销商 CRUD
# =============================================================
@router.get("/dealers", dependencies=[Depends(require_permission("dealer:view"))])
def admin_list_dealers(brand_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(Dealer).filter(Dealer.deleted_at.is_(None))
    if brand_id:
        q = q.filter(Dealer.brand_id == brand_id)
    return ResponseEnvelope(data=[{
        "id": d.id, "brand_id": d.brand_id, "name": d.name, "city": d.city,
        "address": d.address, "lng": _float(d.lng), "lat": _float(d.lat),
        "phone": d.phone, "business_hours": d.business_hours, "cover": d.cover,
        "is_active": d.is_active,
    } for d in q.order_by(Dealer.id).all()])


@router.post("/dealers", dependencies=[Depends(require_permission("dealer:create"))])
def admin_create_dealer(body: DealerUpsert, db: Session = Depends(get_db)):
    d = Dealer(brand_id=body.brand_id, name=body.name, city=body.city, address=body.address,
               lng=body.lng, lat=body.lat, phone=body.phone, business_hours=body.business_hours,
               cover=body.cover, is_active=body.is_active)
    db.add(d)
    db.commit()
    return ResponseEnvelope(data={"id": d.id})


@router.put("/dealers/{dealer_id}", dependencies=[Depends(require_permission("dealer:update"))])
def admin_update_dealer(dealer_id: int, body: DealerUpsert, db: Session = Depends(get_db)):
    d = db.get(Dealer, dealer_id)
    if not d or d.deleted_at:
        return ResponseEnvelope(code=40400, message="经销商不存在", data=None)
    d.brand_id = body.brand_id
    d.name = body.name
    d.city = body.city
    d.address = body.address
    d.lng = body.lng
    d.lat = body.lat
    d.phone = body.phone
    d.business_hours = body.business_hours
    d.cover = body.cover
    d.is_active = body.is_active
    db.commit()
    return ResponseEnvelope(data={"id": d.id})


@router.delete("/dealers/{dealer_id}", dependencies=[Depends(require_permission("dealer:delete"))])
def admin_delete_dealer(dealer_id: int, db: Session = Depends(get_db)):
    d = db.get(Dealer, dealer_id)
    if not d or d.deleted_at:
        return ResponseEnvelope(code=40400, message="经销商不存在", data=None)
    d.deleted_at = datetime.utcnow()
    d.is_active = 0
    db.commit()
    return ResponseEnvelope(data=None)


# =============================================================
# §8.6 系统 / RBAC / 审计 / 看板
# =============================================================
@router.get("/permissions", dependencies=[Depends(get_current_user)])
def admin_list_permissions(db: Session = Depends(get_db)):
    """权限点列表（任意登录可访问）。"""
    return ResponseEnvelope(data=[{"id": p.id, "code": p.code, "name": p.name,
                                   "module": p.module} for p in db.query(Permission).filter(Permission.is_active == 1).all()])


@router.get("/roles", dependencies=[Depends(require_permission("role:view"))])
def admin_list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).filter(Role.deleted_at.is_(None)).all()
    return ResponseEnvelope(data=[{
        "id": r.id, "name": r.name, "code": r.code, "remark": r.remark, "is_active": r.is_active,
        "permission_ids": [rp.permission_id for rp in db.query(RolePermission).filter(RolePermission.role_id == r.id, RolePermission.is_active == 1).all()],
    } for r in roles])


@router.post("/roles", dependencies=[Depends(require_permission("role:create"))])
def admin_create_role(body: RoleUpsert, db: Session = Depends(get_db)):
    r = Role(name=body.name, code=body.code, remark=body.remark, is_active=body.is_active)
    db.add(r)
    db.flush()
    for pid in body.permission_ids:
        db.add(RolePermission(role_id=r.id, permission_id=pid))
    db.commit()
    return ResponseEnvelope(data={"id": r.id})


@router.get("/audit-logs", dependencies=[Depends(require_permission("audit"))])
def admin_list_audit_logs(
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """审计日志列表（super 权限）。"""
    q = db.query(AuditLog)
    if module:
        q = q.filter(AuditLog.module == module)
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    total = q.count()
    rows = q.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ResponseEnvelope(data={"list": [{
        "id": a.id, "admin_user_id": a.admin_user_id, "action": a.action,
        "module": a.module, "target": a.target, "detail": a.detail,
        "ip": a.ip, "created_at": _iso(a.created_at),
    } for a in rows], "total": total, "page": page, "page_size": page_size})


@router.get("/dashboard", dependencies=[Depends(require_permission("dashboard:view"))])
def admin_dashboard(range_days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)):
    """看板聚合：KPI + 趋势 + 品牌/城市分布 + 转化漏斗（由线索表聚合）。"""
    since = datetime.utcnow() - timedelta(days=range_days)
    td = db.query(TestDriveLead).filter(TestDriveLead.created_at >= since).count()
    iq = db.query(InquiryLead).filter(InquiryLead.created_at >= since).count()
    leads_total = td + iq
    deal_count = (
        db.query(TestDriveLead).filter(TestDriveLead.created_at >= since, TestDriveLead.status == "deal").count()
        + db.query(InquiryLead).filter(InquiryLead.created_at >= since, InquiryLead.status == "deal").count()
    )
    kpis = {"leads_total": leads_total, "test_drive": td, "inquiry": iq,
            "deal_rate": round(deal_count / leads_total, 2) if leads_total else 0}
    # 趋势（按天聚合）
    trend = []
    for i in range(range_days, 0, -1):
        day = (datetime.utcnow() - timedelta(days=i - 1)).date()
        n = db.query(TestDriveLead).filter(TestDriveLead.created_at >= datetime(day.year, day.month, day.day),
                                           TestDriveLead.created_at < datetime(day.year, day.month, day.day) + timedelta(days=1)).count()
        trend.append({"date": day.isoformat(), "leads": n})
    # 城市分布
    city_rows = db.query(TestDriveLead.city, TestDriveLead.id).all()
    by_city = {}
    for c, _ in city_rows:
        key = c or "未知"
        by_city[key] = by_city.get(key, 0) + 1
    # 品牌分布（经 model/brand 关联简化：按 model_id 计数）
    model_ids = [l.model_id for l in db.query(TestDriveLead).filter(TestDriveLead.model_id.isnot(None)).all()]
    by_brand = {}
    if model_ids:
        for m in db.query(Model).filter(Model.id.in_(model_ids)).all():
            by_brand[str(m.model_code)] = by_brand.get(str(m.model_code), 0) + 1
    # 转化漏斗（试驾状态机阶段）
    funnel = [
        {"stage": "pending", "count": db.query(TestDriveLead).filter(TestDriveLead.status == "pending").count()},
        {"stage": "contacted", "count": db.query(TestDriveLead).filter(TestDriveLead.status == "contacted").count()},
        {"stage": "arrived", "count": db.query(TestDriveLead).filter(TestDriveLead.status == "arrived").count()},
        {"stage": "deal", "count": db.query(TestDriveLead).filter(TestDriveLead.status == "deal").count()},
    ]
    return ResponseEnvelope(data={
        "kpis": kpis, "trend": trend,
        "by_brand": [{"brand": k, "count": v} for k, v in by_brand.items()],
        "by_city": [{"city": k, "count": v} for k, v in by_city.items()],
        "funnel": funnel,
    })


@router.get("/system-config", dependencies=[Depends(require_permission("system"))])
def admin_get_system_config(db: Session = Depends(get_db)):
    rows = db.query(SystemConfig).all()
    return ResponseEnvelope(data={r.key: r.value for r in rows})


@router.put("/system-config", dependencies=[Depends(require_permission("system"))])
def admin_update_system_config(body: SystemConfigUpsert, db: Session = Depends(get_db)):
    for k, v in body.values.items():
        row = db.query(SystemConfig).filter(SystemConfig.key == k).first()
        if row:
            row.value = v
        else:
            db.add(SystemConfig(key=k, value=v))
    db.commit()
    return ResponseEnvelope(data=None)


@router.get("/seo", dependencies=[Depends(require_permission("system"))])
def admin_get_seo(db: Session = Depends(get_db)):
    rows = db.query(SystemConfig).filter(SystemConfig.key.like("seo.%")).all()
    return ResponseEnvelope(data={r.key.split("seo.")[-1]: r.value for r in rows})


@router.put("/seo", dependencies=[Depends(require_permission("system"))])
def admin_update_seo(body: SeoUpsert, db: Session = Depends(get_db)):
    for k, v in {"title": body.title, "keywords": body.keywords,
                 "description": body.description, "og_image": body.og_image}.items():
        if v is None:
            continue
        row = db.query(SystemConfig).filter(SystemConfig.key == f"seo.{k}").first()
        if row:
            row.value = v
        else:
            db.add(SystemConfig(key=f"seo.{k}", value=v))
    db.commit()
    return ResponseEnvelope(data=None)


@router.get("/finance/params", dependencies=[Depends(require_permission("system"))])
def admin_list_finance_params(db: Session = Depends(get_db)):
    """金融参数列表（后台维护）。"""
    return ResponseEnvelope(data=[{
        "id": f.id, "term_months": f.term_months, "annual_rate": _float(f.annual_rate),
        "product_name": f.product_name,
    } for f in db.query(FinanceParam).all()])
