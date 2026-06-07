from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Core
    env: str = Field(default="dev")
    log_level: str = Field(default="INFO")
    allowed_origins: str = Field(default="http://localhost:3000")

    # DB
    database_url: str
    sync_database_url: str

    # Redis
    redis_url: str

    # Storage
    s3_endpoint_url: str = ""
    s3_region: str = "auto"
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str

    # Crypto
    master_encryption_key: str  # base64-encoded 32 bytes

    # Auth (Clerk)
    clerk_jwks_url: str = ""
    clerk_secret_key: str = ""

    # System fallback keys
    system_openai_key: str = ""
    system_anthropic_key: str = ""
    system_gemini_key: str = ""
    system_tavily_key: str = ""
    system_unsplash_key: str = ""
    system_pexels_key: str = ""
    system_pixabay_key: str = ""

    # Observability
    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: str = ""

    # Limits
    rate_limit_generations_per_day: int = 10
    max_pptx_upload_mb: int = 50
    max_image_upload_mb: int = 10

    # Public
    api_base_url: str = "http://localhost:8000"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
