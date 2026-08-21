# =============================================================
# 段功能：百度地图 API 路由（前端经销商门店地图联动）
# 说明：
#   1) GET /api/v1/map/config  —— 返回百度地图接入状态（key 是否已配置）
#   2) GET /api/v1/map/geocode —— 代理百度地图地理编码 API v3（address -> 经纬度）
#   3) GET /api/v1/map/marker  —— 返回门店跳转百度地图的链接（前端卡片跳转用）
# key 来源（优先级）：环境变量 BAIDU_MAP_KEY > 后台系统配置 map.baidu_key
#   前端"百度地图导航"按钮目前使用百度 URI 协议（api.map.baidu.com/marker，
#   按门店经纬度直接跳转，无需 key）；本路由为后续 Web 端内嵌地图 / 地理编码
#   反向代理预留，等您提供百度地图开放平台（lbsyun.baidu.com）的 AK 后填入即可。
# =============================================================

import json
import urllib.parse
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas import ResponseEnvelope

router = APIRouter(prefix="/api/v1/map", tags=["map"])

# 百度地图开放平台：地理编码 API v3 接口地址
BAIDU_GEOCODE_URL = "https://api.map.baidu.com/geocoding/v3/"


def _baidu_key(db: Session) -> str:
    """
    读取百度地图 AK：优先后台系统配置 map.baidu_key，其次环境变量 BAIDU_MAP_KEY。
    """
    try:
        from app.models import SystemConfig

        row = (
            db.query(SystemConfig)
            .filter(SystemConfig.key == "map.baidu_key")
            .first()
        )
        if row and row.value:
            return row.value
    except Exception:
        pass
    return settings.BAIDU_MAP_KEY


@router.get("/config")
def map_config(db: Session = Depends(get_db)):
    """
    百度地图接入状态。
    返回 { enabled: bool, key_present: bool, hint: 说明 }，
    供前端判断是否启用"地图渲染"类功能（跳转类功能无需 key）。
    """
    key = _baidu_key(db)
    return ResponseEnvelope(
        data={
            "enabled": bool(key),
            "key_present": bool(key),
            "provider": "baidu",
            "hint": "前端门店卡片跳转使用百度 URI 协议，无需 key；"
                    "仅 Web 端内嵌地图 / 地理编码代理需要 key。",
        }
    )


@router.get("/geocode")
def baidu_geocode(
    address: str = Query(..., min_length=1, description="要解析的地址，如：上海市静安区南京西路1266号"),
    city: str = Query("", description="所属城市（可选，辅助提高精度）"),
    db: Session = Depends(get_db),
):
    """
    代理百度地图地理编码 API v3：地址 -> 经纬度。
    需要百度地图开放平台 AK（BAIDU_MAP_KEY 或后台系统配置 map.baidu_key）。
    """
    ak = _baidu_key(db)
    if not ak:
        raise HTTPException(
            status_code=400,
            detail="百度地图 AK 未配置：请设置环境变量 BAIDU_MAP_KEY "
                   "或在后台「系统设置」中配置 map.baidu_key（百度开放平台 lbsyun.baidu.com 申请）",
        )
    params = {
        "address": address,
        "output": "json",
        "ak": ak,
    }
    if city:
        params["city"] = city
    url = BAIDU_GEOCODE_URL + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (regalia backend)"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode("utf-8")
    except Exception as exc:  # 网络 / 超时
        raise HTTPException(status_code=502, detail=f"百度地图服务不可达: {exc}") from exc
    try:
        data = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"百度地图返回异常: {exc}") from exc
    if data.get("status") != 0:
        raise HTTPException(
            status_code=400,
            detail=f"百度地理编码失败: status={data.get('status')} "
                   f"message={data.get('message', '')}",
        )
    loc = (data.get("result") or {}).get("location") or {}
    return ResponseEnvelope(
        data={
            "address": address,
            "lng": loc.get("lng"),
            "lat": loc.get("lat"),
            "precise": (data.get("result") or {}).get("precise", 0),
        }
    )


@router.get("/marker")
def baidu_marker_link(
    name: str = Query("", description="门店名称"),
    lng: float = Query(None, description="经度"),
    lat: float = Query(None, description="纬度"),
    address: str = Query("", description="门店地址（无经纬度时按地址搜索）"),
):
    """
    生成门店跳转百度地图的链接（前端卡片"百度地图导航"按钮使用，无需 key）。
    - 有经纬度：api.map.baidu.com/marker?location=lat,lng&title=...
    - 无经纬度：api.map.baidu.com/geocoder?address=...
    """
    if lng is not None and lat is not None:
        url = (
            "https://api.map.baidu.com/marker?location="
            + urllib.parse.quote(f"{lat},{lng}")
            + "&title=" + urllib.parse.quote(name or "")
            + "&content=" + urllib.parse.quote(address or "")
            + "&output=html&src=regalia"
        )
    else:
        url = (
            "https://api.map.baidu.com/geocoder?address="
            + urllib.parse.quote(address or name or "")
            + "&output=html&src=regalia"
        )
    return ResponseEnvelope(data={"url": url})
