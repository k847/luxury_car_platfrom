from __future__ import annotations

from typing import List

# =============================================================
# 段功能：M2 公开端响应模型（Pydantic）
# 说明：定义品牌 / 车型 / 资讯 / Banner 的响应结构，字段严格对齐
#       《开发技术文档》§7.1 / §7.2 / §7.3 / §7.9。
#       统一响应信封 {code,message,data} 在 app.schemas.ResponseEnvelope。
#       所有模型允许 from_attributes，便于未来直接从 ORM 构造；
#       当前路由手工组装（保证 i18n 合并逻辑清晰、可审计）。
# =============================================================

from pydantic import BaseModel


# ---------- §7.1 品牌 ----------
class BrandOut(BaseModel):
    """品牌列表项：同时给出中英文名称，供前端语言切换。"""

    id: int
    brand_code: str | None = None
    logo: str | None = None
    country: str | None = None
    name_zh: str | None = None
    name_en: str | None = None
    sort: int | None = None

    model_config = {"from_attributes": True}


# ---------- §7.2 车型列表项 ----------
class ModelListItem(BaseModel):
    """车型列表项：名称均为按语言本地化后的结果。"""

    id: int
    brand_name: str | None = None
    series_name: str | None = None
    model_name: str | None = None
    cover_image: str | None = None
    guide_price: float | None = None
    fuel_type: str | None = None
    segment: str | None = None
    is_recommended: int | None = None

    model_config = {"from_attributes": True}


class ModelListData(BaseModel):
    """车型列表分页包装：{list, total, page, page_size}。"""

    list: List[ModelListItem] = []
    total: int = 0
    page: int = 1
    page_size: int = 12


# ---------- §7.3 车型详情 ----------
class TrimBrief(BaseModel):
    """配置版本概要。"""

    trim_name: str | None = None
    price: float | None = None
    power: str | None = None
    transmission: str | None = None
    drive: str | None = None

    model_config = {"from_attributes": True}


class ColorOption(BaseModel):
    """颜色选项（来自配置器 color 分组）。"""

    name: str | None = None
    swatch: str | None = None
    price_delta: float | None = None


class DealerBrief(BaseModel):
    """在售经销商概要。"""

    id: int
    name: str | None = None
    city: str | None = None

    model_config = {"from_attributes": True}


class ModelBody(BaseModel):
    """车身尺寸。"""

    length: int | None = None
    width: int | None = None
    height: int | None = None
    wheelbase: int | None = None
    trunk: int | None = None


class ModelDetail(BaseModel):
    """车型详情：基础信息 + 图库 + 配置版本 + 颜色 + 在售经销商 + 金融入口标记。"""

    id: int
    model_name: str | None = None
    guide_price: float | None = None
    body: ModelBody | None = None
    cover_image: str | None = None
    gallery: list[str] = []
    trims: list[TrimBrief] = []
    colors: list[ColorOption] = []
    dealers: list[DealerBrief] = []
    finance_available: bool = True


# ---------- §7.9 资讯 ----------
class ArticleListItem(BaseModel):
    """资讯列表项。"""

    id: int
    category: str | None = None
    cover_url: str | None = None
    title: str | None = None
    summary: str | None = None
    published_at: str | None = None
    is_top: int | None = None
    is_recommended: int | None = None
    author: str | None = None
    source: str | None = None

    model_config = {"from_attributes": True}


class ArticleListData(BaseModel):
    """资讯列表分页包装。"""

    list: List[ArticleListItem] = []
    total: int = 0
    page: int = 1
    page_size: int = 12


class ArticleDetail(BaseModel):
    """资讯详情：标题/摘要/正文均为按语言本地化后的结果。"""

    id: int
    category: str | None = None
    cover_url: str | None = None
    title: str | None = None
    summary: str | None = None
    body: str | None = None
    published_at: str | None = None
    author: str | None = None
    source: str | None = None


# ---------- §7.9 Banner ----------
class BannerOut(BaseModel):
    """首页轮播/Banner 区块项。"""

    id: int
    position: str | None = None
    image: str | None = None
    link: str | None = None
    sort: int | None = None

    model_config = {"from_attributes": True}


# =============================================================
# 段功能：M3 选车深化响应/请求模型（§7.4 配置器 / §7.5 算价 / §7.6 对比 / §7.7 留资 / 金融参数）
# 说明：字段严格对齐《开发技术文档》对应契约与附录 B 错误码。
# =============================================================

# ---------- §7.4 配置器数据 ----------
class OptionBrief(BaseModel):
    """配置器单个选项（名称经 i18n 注入，其余字段直接来自 options 表）。"""

    id: int
    name: str | None = None
    swatch: str | None = None
    price_delta: float | None = None
    stock_status: str | None = None
    lead_time: int | None = None
    is_default: int | None = None


class OptionGroupOut(BaseModel):
    """配置器选项分组（含选项列表）。"""

    group_code: str
    name: str | None = None
    is_required: int | None = None
    max_select: int | None = None
    options: list[OptionBrief] = []


class ConfiguratorData(BaseModel):
    """配置器完整数据：基础价 + 分组与选项。"""

    base_price: float | None = None
    groups: list[OptionGroupOut] = []


# ---------- §7.5 配置算价 ----------
class QuoteSelection(BaseModel):
    """用户选型：单选项（color/wheel/interior）传选项 id，packages 为选项 id 数组。"""

    color: int | None = None
    wheel: int | None = None
    interior: int | None = None
    packages: list[int] = []


class QuoteRequest(BaseModel):
    """算价请求体：车型 id + 用户选型。"""

    model_id: int
    selections: QuoteSelection


class QuoteDelta(BaseModel):
    """算价明细：每组选中项的加价。"""

    group: str
    option: str
    price_delta: float


class QuoteResult(BaseModel):
    """算价结果：总价 = 基础价 + Σ加价；库存取最差状态；交付取最大周期。"""

    base_price: float
    deltas: list[QuoteDelta] = []
    total: float
    stock_status: str
    max_lead_time: int


# ---------- §7.6 车型对比 ----------
class CompareItem(BaseModel):
    """对比项：名称按语言本地化；缺失字段前端显示"—"。"""

    id: int
    model_name: str | None = None
    guide_price: float | None = None
    fuel_type: str | None = None
    segment: str | None = None
    body: ModelBody | None = None
    power: str | None = None
    trims_count: int = 0


# ---------- 金融参数（金融计算器数据来源） ----------
class FinanceParamOut(BaseModel):
    """金融方案参数：期数 + 年化利率 + 产品名。"""

    term_months: int
    annual_rate: float
    product_name: str | None = None

    model_config = {"from_attributes": True}


# ---------- §7.7 留资：试驾 / 询价 ----------
class LeadBase(BaseModel):
    """留资公共字段（试驾与询价共用）。"""

    name: str
    phone: str
    city: str | None = None
    brand_id: int | None = None
    model_id: int | None = None
    preferred_dealer_id: int | None = None
    preferred_time: str | None = None   # ISO 时间字符串，端点内解析为 datetime
    remark: str | None = None
    config_summary: object | None = None  # 配置摘要（dict/JSON）


class TestDriveLeadRequest(LeadBase):
    """试驾留资请求体。"""


class InquiryLeadRequest(LeadBase):
    """询价留资请求体：intent 必填之一 trade_in/finance/stock。"""

    intent: str


class LeadResponse(BaseModel):
    """留资提交成功响应。"""

    lead_id: int
    message: str
