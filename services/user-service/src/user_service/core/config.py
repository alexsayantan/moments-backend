from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_version: str = "v1"
    app_name: str = "User Service"
    app_description: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = True


settings = Settings()