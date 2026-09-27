from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """Configuration for JWT authentication across microservices."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # JWT Settings
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = "dev-insecure-secret-key-must-be-changed-in-production-32-chars-min"
    jwt_public_key: str | None = None
    jwt_private_key: str | None = None

    # Token Lifetimes
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Claims
    token_issuer: str = "moments-user-service"
    token_audience: str = "moments-platform"


auth_settings = AuthSettings()
