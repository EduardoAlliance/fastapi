from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FastAPI API"
    environment: str = "local"
    debug: bool = False
    log_level: str = "INFO"

    secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "mysql+pymysql://fastapi:fastapi@127.0.0.1:3306/fastapi_db?charset=utf8mb4"
    redis_url: str = "redis://localhost:6379/0"

    rate_limit_enabled: bool = True
    login_rate_limit_ip_attempts: int = 20
    login_rate_limit_email_attempts: int = 5
    login_rate_limit_window_seconds: int = 60

    cors_origins: list[str] = Field(default_factory=list)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
