# =============================================================
# 段功能：鉴权依赖（M1 鉴权基础设施）
# 说明：提供 FastAPI 路由层复用鉴权逻辑：
#   - get_current_user：解析请求头 JWT，校验有效性并加载当前后台用户
#   - require_permission：RBAC 权限校验工厂，装饰需要特定权限的接口
# 对应《开发技术文档》M1 的 get_current_user / require_permission 要求。
# =============================================================

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import AdminUser, Permission, RolePermission

# Bearer 认证方案：从 Authorization: Bearer <token> 中提取令牌
# auto_error=False 让我们能自定义 401 文案
bearer_scheme = HTTPBearer(auto_error=False)

# 统一异常：未登录 / Token 失效
UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="未登录或 Token 失效",
    headers={"WWW-Authenticate": "Bearer"},
)
# 统一异常：无权限
FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="无权限访问该资源",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    """
    依赖：获取当前登录的后台用户。
    流程：
      1. 校验请求头是否携带 Bearer token，否则抛 401
      2. 解码 JWT（失败/过期抛 401）
      3. 通过 payload 中的 sub（用户 id）查询 admin_users
      4. 用户不存在或被禁用抛 401
    返回 AdminUser ORM 对象，供后续路由直接使用。
    """
    if credentials is None or not credentials.credentials:
        raise UNAUTHENTICATED

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise UNAUTHENTICATED

    # token 类型必须是 access，且包含 sub
    if payload.get("type") != "access" or "sub" not in payload:
        raise UNAUTHENTICATED

    user = db.get(AdminUser, int(payload["sub"]))
    if user is None or user.is_active != 1:
        raise UNAUTHENTICATED
    return user


def get_current_permissions(user: AdminUser, db: Session) -> set[str]:
    """
    工具：查询某用户拥有的全部权限编码集合（如 {'model:create', 'lead:view'}）。
    通过 role_permissions 关联表 → permissions 表获得。
    结果用于 RBAC 判断。
    """
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(
            RolePermission.role_id == user.role_id,
            RolePermission.is_active == 1,
            Permission.is_active == 1,
        )
        .all()
    )
    # rows 形如 [(code,), ...]，提取为 set 便于 O(1) 判定
    return {r[0] for r in rows}


def require_permission(permission_code: str) -> Callable:
    """
    权限依赖工厂（RBAC）。
    用法：@router.get("/", dependencies=[Depends(require_permission("dashboard:view"))])
    返回的函数会：
      1. 先拿到当前用户（复用 get_current_user）
      2. 查询其权限集合
      3. 若不包含所需 permission_code，抛 403
    这样无需在每个接口内手写权限判断。
    """

    def _checker(
        current_user: AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        # 获取用户全部权限编码集合；支持通配符前缀匹配（seed 用 brand:*、lead.test_drive:* 等）
        perms = get_current_permissions(current_user, db)
        for p in perms:
            if p == permission_code:
                return
            # 通配符：如权限 brand:* 可放行 brand:view / brand:create / brand:update / brand:delete
            if p.endswith(":*") and permission_code.startswith(p[:-1]):
                return
        raise FORBIDDEN

    return _checker
