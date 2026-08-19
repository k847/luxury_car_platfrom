# =============================================================
# 段功能：i18n 多语言读取工具（M2 公共端）
# 说明：前台公开接口需要根据 lang 返回对应语言文本，缺失时回退中文(zh)。
#   翻译表结构统一为 (实体id, lang) 联合主键 + 各语言字段，本模块提供
#   批量加载与取值的通用能力，避免每个接口重复写 join 逻辑。
# =============================================================

from sqlalchemy.orm import Session
from typing import Any

# 默认语言：中文（缺失翻译时回退）
DEFAULT_LANG = "zh"
# 当前支持的语言集合
SUPPORTED_LANGS = ("zh", "en")


def normalize_lang(lang: str | None) -> str:
    """
    规范化语言参数。
    仅接受 zh / en，其它值（含 None）一律回退为 zh，保证接口行为稳定。
    """
    if lang in SUPPORTED_LANGS:
        return lang
    return DEFAULT_LANG


def load_i18n(session: Session, I18nModel, fk_col, ids: list):
    """
    批量加载翻译行：对每个实体 id，同时取出 zh 与 en 两行。
    返回结构：{实体id: {"zh": 行对象|None, "en": 行对象|None}}

    参数：
      I18nModel  翻译表 ORM 类（如 BrandI18n）
      fk_col     翻译表指向主表的联合主键列（如 BrandI18n.brand_id）
      ids        需要翻译的实体 id 列表
    """
    # 预先为每个实体初始化空槽位，避免后续取值时 KeyError
    out = {i: {"zh": None, "en": None} for i in ids}
    if not ids:
        return out

    # 一次性查出目标实体在 zh/en 两种语言下的所有翻译行
    rows = (
        session.query(I18nModel)
        .filter(fk_col.in_(ids), I18nModel.lang.in_(SUPPORTED_LANGS))
        .all()
    )
    for r in rows:
        eid = getattr(r, fk_col.key)  # 取出该翻译行对应的实体 id 值
        # 仅当语言键存在于槽位时才写入（理论上都是 zh/en）
        if r.lang in out.get(eid, {}):
            out[eid][r.lang] = r
    return out


def pick(rowmap: dict, eid: Any, attr: str, lang: str) -> Any:
    """
    从加载好的 i18n 映射中取出某字段值。
    取值优先级：请求语言(lang)行 → 中文(zh)行 → None。
    这样即使某种语言缺失翻译，也能回退到中文，避免前端拿到空文本。
    """
    lang = normalize_lang(lang)
    slot = rowmap.get(eid, {})
    # 优先请求语言，其次中文；两行都取不到该字段则返回 None
    row = slot.get(lang) or slot.get(DEFAULT_LANG)
    return getattr(row, attr, None) if row is not None else None
