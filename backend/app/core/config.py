# =============================================================
# 段功能：全局配置读取（M1 基础设施）
# 说明：使用 pydantic-settings 从环境变量 / .env 读取配置，
#       集中管理数据库、JWT、CORS、运行环境等参数。
#       所有配置项对应《开发技术文档》附录 D 的环境变量表。
# =============================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类。
    字段含义（均可通过环境变量覆盖，详见 .env.example）：
    """

    # model_config：指定从 .env 文件加载，且允许环境变量覆盖
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---------- 数据库（MySQL 8）----------
    DB_HOST: str = "127.0.0.1"          # 数据库主机
    DB_PORT: int = 3306                 # 数据库端口
    DB_USER: str = "root"               # 数据库用户名
    DB_PASSWORD: str = "root"           # 数据库密码
    DB_NAME: str = "luxury_car"         # 数据库名

    # ---------- Redis（限流 / refresh token，M1 先预留）----------
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # ---------- JWT 鉴权 ----------
    JWT_SECRET: str = "change-me-in-prod"        # JWT 签名密钥，生产必须替换
    ACCESS_TOKEN_EXPIRE: int = 3600              # access token 有效期（秒），默认 1 小时
    REFRESH_TOKEN_EXPIRE: int = 7 * 24 * 3600    # refresh token 有效期（秒），默认 7 天

    # ---------- CORS（前台域名白名单）----------
    CORS_ORIGINS: str = "http://localhost:5173"  # 多个域名用逗号分隔

    # ---------- 运行环境 ----------
    ENV: str = "dev"                  # dev / staging / prod
    API_PREFIX: str = "/api"          # 全局接口前缀

    # ---------- 百度地图（经销商门店地图联动，M6 新增）----------
    BAIDU_MAP_KEY: str = ""           # 百度地图开放平台 AK（lbsyun.baidu.com 申请），
                                      # 用于 /api/v1/map/geocode 地理编码代理；留空表示未接入

    @property
    def database_url(self) -> str:
        """
        拼接 SQLAlchemy 使用的 MySQL 连接串（PyMySQL 驱动，utf8mb4）。
        """
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        """
        将逗号分隔的 CORS_ORIGINS 字符串解析为列表，供 FastAPI CORSMiddleware 使用。
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


# 全局唯一配置实例，供其他模块直接 import 使用
settings = Settings()
