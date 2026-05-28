"""
应用配置
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    APP_NAME: str = "FitAI"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库
    DATABASE_URL: str = "postgresql://fituser:@localhost:5432/fit_saas"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT — required in production; dev/test uses a default for convenience
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "*"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # AI (Phase 2)
    AI_PROVIDER: str = ""
    AI_API_KEY: str = ""

    # Payment (Phase 1.2)
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_GATEWAY_URL: str = "https://openapi.alipay.com/gateway.do"
    ALIPAY_NOTIFY_URL: str = ""

    WECHAT_PAY_APP_ID: str = ""
    WECHAT_PAY_MCH_ID: str = ""
    WECHAT_PAY_API_KEY: str = ""          # V2 legacy key (for refunds)
    WECHAT_PAY_API_V3_KEY: str = ""       # V3 key (32 bytes, for notification decryption)
    WECHAT_PAY_CERT_SERIAL_NO: str = ""   # Merchant certificate serial number
    WECHAT_PAY_PRIVATE_KEY_PATH: str = "" # Path to apiclient_key.pem
    WECHAT_PAY_GATEWAY_URL: str = "https://api.mch.weixin.qq.com"
    WECHAT_PAY_NOTIFY_URL: str = ""

    @field_validator("APP_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if v.lower() not in allowed:
            raise ValueError(f"APP_ENV must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        return v

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.APP_ENV == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            if self.CORS_ORIGINS == "*":
                pass  # nginx handles CORS in production
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """获取配置 (缓存)"""
    return Settings()


settings = get_settings()
