from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    project_name: str = "FitAI"
    project_version: str = "1.0.0"
    
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./fitai.db")
    database_url_local: str = "sqlite:///./fitai.db"
    
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_url_local: str = "redis://localhost:6379/0"
    
    secret_key: str = os.getenv("SECRET_KEY", "default-secret-key-for-testing-must-be-at-least-32-characters-long")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    
    wechat_app_id: Optional[str] = None
    wechat_mch_id: Optional[str] = None
    wechat_api_key: Optional[str] = None
    wechat_notify_url: Optional[str] = None
    
    aliyun_access_key_id: Optional[str] = None
    aliyun_access_key_secret: Optional[str] = None
    aliyun_sms_sign_name: Optional[str] = None
    
    deepseek_api_key: Optional[str] = None
    tongyi_api_key: Optional[str] = None
    
    sensenova_api_key: Optional[str] = os.getenv("SENSENOVA_API_KEY")
    sensenova_base_url: str = os.getenv("SENSENOVA_BASE_URL", "https://token.sensenova.cn/v1/chat/completions")
    sensenova_model_id: str = os.getenv("SENSENOVA_MODEL_ID", "sensenova-6.7-flash-lite")
    
    environment: str = os.getenv("ENVIRONMENT", "development")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    model_config = SettingsConfigDict(env_file=os.getenv("ENV_FILE", ".env"), extra="ignore")

settings = Settings()