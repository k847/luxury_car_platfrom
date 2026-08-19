# =============================================================
# 段功能：安全工具（M1 鉴权基础设施）
# 说明：封装两类安全能力：
#   1) 密码哈希：注册 / 改密时对明文密码做 bcrypt 加盐哈希，登录时校验
#   2) JWT：签发 access / refresh token，以及解析校验 token 取出用户身份
# =============================================================

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import bcrypt

from app.core.config import settings


def hash_password(plain: str) -> str:
    """
    对明文密码进行 bcrypt 哈希（自动加盐，不可逆）。
    直接使用 bcrypt 库（passlib 已停维护且与 bcrypt>=4 不兼容）。
    返回形如 '$2b$12$...' 的哈希串，兼容已有 seed 数据。
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    校验明文密码与数据库中的哈希是否匹配。
    用于登录时验证用户提交的密码是否正确。
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # 哈希格式不合法（如空串/损坏）时视为校验失败，不抛异常
        return False


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """
    签发 access token（短期，默认 1 小时）。
    :param subject: 载荷中的主体，通常放入用户 id
    :param extra: 额外写入 payload 的字段（如 role_code）
    """
    now = datetime.now(timezone.utc)
    # exp：过期时间；iat：签发时间；sub：用户标识
    payload = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE),
    }
    if extra:
        payload.update(extra)
    # 使用 HS256 算法 + 配置中的密钥签名
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def create_refresh_token(subject: str | int) -> str:
    """
    签发 refresh token（长期，默认 7 天）。
    用于在 access token 过期后换取新的令牌对，避免频繁重新登录。
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    """
    校验并解析 JWT。
    若签名无效或已过期，jwt 会抛出异常，由调用方（deps）捕获为 401。
    返回解码后的 payload 字典。
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
