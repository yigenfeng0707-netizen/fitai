"""
应用配置
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    APP_NAME: str = "健身瑜伽教培管理系统"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库
    DATABASE_URL: str = "postgresql://fituser:fitpass123@localhost:5432/fit_saas"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "*"

    # 密码
    PASSWORD_SECRET_KEY: str = "password-secret-key-change-in-production"

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
    WECHAT_PAY_API_KEY: str = ""
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
        if v == "dev-secret-key-change-in-production":
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY is still using the default dev value! "
                "Set JWT_SECRET_KEY in .env for production."
            )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        if v == "*" and cls._is_production():
            raise ValueError("CORS_ORIGINS cannot be '*' in production")
        return v

    @classmethod
    def _is_production(cls) -> bool:
        try:
            instance = getattr(cls, "_settings_instance", None)
            if instance:
                return instance.APP_ENV == "production"
        except Exception:
            pass
        return False

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.APP_ENV == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if self.JWT_SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError("JWT_SECRET_KEY must be changed in production")
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
