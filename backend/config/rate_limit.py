from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitSettings(BaseSettings):
    """限流配置独立校验，不把 Redis 凭据写入代码或日志。"""

    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = True
    redis_url: SecretStr = Field(
        default=SecretStr("redis://127.0.0.1:6379/0"), validation_alias="REDIS_URL"
    )
    namespace: str = Field(default="knowledge-ai", pattern=r"^[a-zA-Z0-9:_-]{1,80}$")
    chat_requests: int = Field(default=10, ge=1, le=10000)
    interview_requests: int = Field(default=10, ge=1, le=10000)
    window_seconds: int = Field(default=60, ge=1, le=86400)
    redis_timeout_seconds: float = Field(default=1, gt=0, le=10)
    unavailable_retry_seconds: int = Field(default=5, ge=1, le=60)
