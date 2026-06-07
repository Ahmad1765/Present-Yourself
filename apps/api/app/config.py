import base64
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
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
    # When `auth_enabled` is true, clerk_jwks_url + clerk_audience are required at startup.
    # Otherwise the dev bypass in app.auth (X-Dev-User-Id header) is used.
    auth_enabled: bool = False
    clerk_jwks_url: str = ""
    clerk_secret_key: str = ""
    clerk_audience: str = ""

    # System fallback keys
    system_openai_key: str = ""
    system_anthropic_key: str = ""
    system_gemini_key: str = ""
    system_tavily_key: str = ""
    system_unsplash_key: str = ""
    system_pexels_key: str = ""
    system_pixabay_key: str = ""
    system_stability_key: str = ""

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

    @field_validator("master_encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        try:
            decoded = base64.b64decode(v, validate=True)
        except Exception as e:  # noqa: BLE001
            raise ValueError("MASTER_ENCRYPTION_KEY must be valid base64") from e
        if len(decoded) != 32:
            raise ValueError(
                f"MASTER_ENCRYPTION_KEY must decode to 32 bytes (got {len(decoded)})"
            )
        return v

    @model_validator(mode="after")
    def validate_auth_config(self) -> "Settings":
        if self.auth_enabled and (not self.clerk_jwks_url or not self.clerk_audience):
            raise ValueError(
                "auth_enabled=true requires CLERK_JWKS_URL and CLERK_AUDIENCE to be set"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
