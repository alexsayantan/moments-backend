from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_version: str = "v1"
    app_name: str = "User Service"
    app_description: str = ""

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/user_db"
    )
    echo_sql: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v or "postgresql+psycopg://postgres:postgres@localhost:5432/user_db"


settings = Settings()