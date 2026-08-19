# =============================================================
# 段功能：轻量响应缓存（M2 公共端：i18n 读取 + 缓存）
# 说明：默认使用进程内 TTL 缓存（dict），无需启动 Redis 即可验证；
#   接口形态刻意做得“可平滑替换”——未来接入 Redis 时，只需把
#   _local_cache 的读写改为 redis 客户端即可，路由层代码无需改动。
#   缓存键由“前缀 + 参数 JSON 哈希”生成，保证不同查询参数互不干扰。
# =============================================================

import time
import json
import hashlib
from typing import Optional

# 进程内缓存存储：key -> (过期时间戳, JSON 字符串)
_local_cache: dict[str, tuple[float, str]] = {}

# 公开数据变化不频繁，默认缓存 60 秒，兼顾实时性与 DB 压力
DEFAULT_TTL = 60


def _now() -> float:
    """返回当前秒级时间戳，供 TTL 判断使用。"""
    return time.time()


def make_key(prefix: str, **params) -> str:
    """
    生成稳定缓存键。
    将前缀与所有查询参数序列化为 JSON 再取 MD5，确保相同查询命中同一键。
    """
    raw = prefix + ":" + json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def cache_get(key: str) -> Optional[object]:
    """
    读取缓存。
    不存在或已过期（过期时间戳小于当前时间）均返回 None，并顺手清理过期项。
    """
    item = _local_cache.get(key)
    if not item:
        return None
    expire_at, payload = item
    if expire_at < _now():
        _local_cache.pop(key, None)  # 惰性淘汰过期缓存
        return None
    return json.loads(payload)


def cache_set(key: str, value: object, ttl: int = DEFAULT_TTL) -> None:
    """
    写入缓存。
    value 必须是可 JSON 序列化的对象（Pydantic model_dump() 的结果即满足）。
    """
    _local_cache[key] = (_now() + ttl, json.dumps(value, default=str))
