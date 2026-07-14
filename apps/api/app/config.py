from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/weave"
    redis_url: str = "redis://localhost:6379/0"
    api_key_secret: str = "change-me-in-production"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    resend_api_key: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    moz_api_key: str | None = None
    jwt_secret: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_prefix": "WEAVE_", "env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
