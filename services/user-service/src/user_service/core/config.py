from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_version: str = "v1"
    app_name: str = "User Service"
    app_description: str = ""

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/user_db"
    )
    echo_sql: bool = False

    # Kubernetes & AWS RDS Proxy connection pool settings
    db_pool_size: int = 5
    db_max_overflow: int = 2
    db_pool_timeout: int = 30
    db_pool_recycle: int = 300  # Recycle after 5 mins to prevent stale AWS NAT/proxy connections
    db_prepare_threshold: int | None = None  # None disables prepared statements to prevent RDS Proxy pinning

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v or "postgresql+psycopg://postgres:postgres@localhost:5432/user_db"


settings = Settings()
