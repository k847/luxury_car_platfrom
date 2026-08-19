# =============================================================
# 段功能：鉴权路由（M1 接口层）
# 说明：实现《开发技术文档》M1 的三个接口：
#   POST /auth/login   用户名密码登录，返回令牌对 + 用户信息
#   POST /auth/refresh 用 refresh token 换取新的令牌对
#   GET  /auth/me      获取当前登录用户信息（需 Bearer token）
# 鉴权逻辑委托给 app.core.security 与 app.core.deps。
# =============================================================

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models import AdminUser
from app.schemas import (
    AdminUserBrief,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TokenPair,
)

# 定义本路由前缀 /auth，标签用于 OpenAPI 分组
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    登录接口。
    流程：
      1. 按用户名查询后台账号
      2. 账号不存在 / 已禁用 / 密码不匹配 → 401
      3. 成功则刷新 last_login_at
      4. 签发 access + refresh token，返回令牌对与用户简讯
    """
    user = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    # 统一返回 401，避免泄露"用户不存在"与"密码错误"的区别（安全）
    if user is None or user.is_active != 1 or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最近登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 将角色编码写入 token 的额外载荷，便于后续快速判定（可选）
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=AdminUserBrief.model_validate(user),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    """
    刷新接口：用未过期的 refresh token 换取新令牌对。
    若 refresh token 无效/过期/类型不对 → 401。
    """
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 类型错误")

    # 校验用户仍存在且激活
    user = db.get(AdminUser, int(decoded["sub"]))
    if user is None or user.is_active != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")

    # 重新签发一对令牌（refresh 也轮换，提升安全性）
    new_access = create_access_token(subject=user.id)
    new_refresh = create_refresh_token(subject=user.id)
    return TokenPair(access_token=new_access, refresh_token=new_refresh, token_type="bearer")


@router.get("/me", response_model=AdminUserBrief)
def me(current_user: AdminUser = Depends(get_current_user)) -> AdminUserBrief:
    """
    获取当前登录用户信息（需 Bearer token）。
    直接复用 get_current_user 依赖，返回脱敏后的用户信息。
    """
    return AdminUserBrief.model_validate(current_user)
