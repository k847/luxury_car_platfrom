# =============================================================
# 段功能：M4 后台端请求/响应模型（§8 鉴权与后台端）
# 说明：定义后台 CRUD 与系统接口的 Pydantic 结构，字段对齐《开发技术文档》§8。
#   统一响应信封在 app.schemas.ResponseEnvelope；分页字段用 list 需避开字段名遮蔽。
#   所有写操作由 AuditMiddleware 自动落库 audit_logs。
# =============================================================

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- 通用分页包装 ----------
class PageData(BaseModel):
    """通用分页包装：{list, total, page, page_size}。"""

    list: List = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# ---------- §8.2 品牌 / 系列 / 车型 / 配置器 CRUD ----------
class BrandUpsert(BaseModel):
    """品牌创建/更新请求：双语名称同时写入 brands + brand_i18n（事务）。"""

    brand_code: str = Field(..., min_length=1)
    logo: Optional[str] = None
    country: Optional[str] = None
    sort: int = 0
    is_active: int = 1
    name_zh: str
    name_en: str


class SeriesUpsert(BaseModel):
    """车系创建/更新请求。"""

    brand_id: int
    series_code: str = Field(..., min_length=1)
    segment: Optional[str] = None
    sort: int = 0
    is_active: int = 1
    name_zh: str
    name_en: str


class ModelUpsert(BaseModel):
    """车型创建/更新请求。"""

    series_id: int
    model_code: str = Field(..., min_length=1)
    fuel_type: Optional[str] = None
    guide_price: Optional[float] = None
    is_recommended: int = 0
    status: str = "active"
    is_active: int = 1
    name_zh: str
    name_en: str


class TrimUpsert(BaseModel):
    """配置版本创建/更新请求。"""

    trim_name: str
    price: Optional[float] = None
    power: Optional[str] = None
    transmission: Optional[str] = None
    drive: Optional[str] = None
    is_active: int = 1


class OptionGroupUpsert(BaseModel):
    """配置器选项分组创建/更新请求。"""

    model_id: int
    group_code: str
    is_required: int = 0
    max_select: int = 1
    exclude_groups: Optional[str] = None
    sort: int = 0
    is_active: int = 1
    name_zh: str
    name_en: str


class OptionUpsert(BaseModel):
    """配置器选项创建/更新请求。"""

    group_id: int
    option_code: str = Field(..., min_length=1)
    swatch: Optional[str] = None
    price_delta: Optional[float] = 0
    stock_status: str = "in_stock"
    lead_time: Optional[int] = None
    is_default: int = 0
    sort: int = 0
    is_active: int = 1
    name_zh: str
    name_en: str


# ---------- §8.3 内容 / Banner CRUD ----------
class ArticleUpsert(BaseModel):
    """资讯创建/更新请求：双语写入 article_i18n。"""

    category: str = "company_news"
    cover_url: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    status: str = "draft"
    is_top: int = 0
    is_recommended: int = 0
    is_active: int = 1
    title_zh: str
    summary_zh: Optional[str] = None
    body_zh: Optional[str] = None
    title_en: Optional[str] = None
    summary_en: Optional[str] = None
    body_en: Optional[str] = None


class BannerUpsert(BaseModel):
    """Banner 创建/更新请求。"""

    position: str
    image: str
    link: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    sort: int = 0
    is_active: int = 1


# ---------- §8.4 线索管理 ----------
class LeadAssign(BaseModel):
    """线索分配请求。"""

    owner_id: Optional[int] = None


class LeadAdvance(BaseModel):
    """线索状态机推进请求。"""

    to_status: str


# ---------- §8.5 经销商 ----------
class DealerUpsert(BaseModel):
    """经销商创建/更新请求。"""

    brand_id: int
    name: str = Field(..., min_length=1)
    city: Optional[str] = None
    address: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    phone: Optional[str] = None
    business_hours: Optional[str] = None
    cover: Optional[str] = None
    is_active: int = 1


# ---------- §8.6 系统 / RBAC ----------
class RoleUpsert(BaseModel):
    """角色创建/更新请求。"""

    name: str
    code: str = Field(..., min_length=1)
    remark: Optional[str] = None
    permission_ids: List[int] = []
    is_active: int = 1


class SystemConfigUpsert(BaseModel):
    """系统配置更新请求（key-value）。"""

    values: dict = {}


class SeoUpsert(BaseModel):
    """SEO 配置更新请求。"""

    title: Optional[str] = None
    keywords: Optional[str] = None
    description: Optional[str] = None
    og_image: Optional[str] = None


# ---------- 看板 ----------
class DashboardOut(BaseModel):
    """看板聚合输出：KPI + 趋势 + 品牌/城市分布 + 转化漏斗。"""

    kpis: dict = {}
    trend: List[dict] = []
    by_brand: List[dict] = []
    by_city: List[dict] = []
    funnel: List[dict] = []
