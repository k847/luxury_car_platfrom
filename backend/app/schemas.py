# =============================================================
# 段功能：Pydantic 数据模型（M1 校验层）
# 说明：定义接口请求体与响应体的数据结构，承担：
#   - 请求参数校验（如手机号格式、必填项）
#   - 统一响应信封（code/message/data）对应《开发技术文档》附录 B 错误码表
#   目前仅覆盖 M1 鉴权所需结构，后续里程碑按接口契约补充。
# =============================================================

from pydantic import BaseModel, Field

from datetime import datetime


# ---------- 统一响应信封 ----------
class ResponseEnvelope(BaseModel):
    """
    统一 API 响应结构。
    code: 业务码，0 表示成功（见附录 B）
    message: 提示文案
    data: 业务数据（成功时存放，失败时可为 None）
    """

    code: int = 0
    message: str = "ok"
    data: object | None = None


# ---------- 鉴权：登录 ----------
class LoginRequest(BaseModel):
    """登录请求体：用户名 + 密码（OAuth2 密码模式所需字段）。"""

    username: str = Field(..., min_length=1, description="登录用户名")
    password: str = Field(..., min_length=1, description="登录密码（明文，传输层由 HTTPS 保护）")


class TokenPair(BaseModel):
    """登录/刷新成功返回的令牌对。"""

    access_token: str = Field(..., description="短期访问令牌")
    refresh_token: str = Field(..., description="长期刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class LoginResponse(BaseModel):
    """登录响应：令牌对 + 当前用户简讯。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "AdminUserBrief"


class RefreshRequest(BaseModel):
    """刷新请求：提交 refresh_token 换取新令牌对。"""

    refresh_token: str = Field(..., description="原 refresh token")


# ---------- 当前用户简讯 ----------
class AdminUserBrief(BaseModel):
    """当前登录用户的核心信息（返回给前端，不含密码哈希）。"""

    id: int
    username: str
    real_name: str | None = None
    nickname: str | None = None
    role_id: int
    is_active: int

    model_config = {"from_attributes": True}  # 允许从 ORM 对象直接构造


# 解决前向引用（LoginResponse.user 引用 AdminUserBrief）
LoginResponse.model_rebuild()
