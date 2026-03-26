"""Configuration management using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # Cloudflare R2
    r2_account_id: str
    r2_bucket_name: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_public_url: str

    # Upstash Redis
    upstash_redis_url: str

    # LLM APIs (used by agent — imported here for worker processes)
    groq_api_key: str = ""
    gemini_api_key: str = ""
    together_api_key: str = ""

    # Email
    resend_api_key: str = ""

    # Limits
    max_pdf_size_mb: int = 50
    max_free_papers_per_month: int = 5
    max_agent_steps: int = 25
    job_timeout_seconds: int = 180
    sse_heartbeat_interval: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get the cached settings instance."""
    return Settings()
