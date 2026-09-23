from user_service.core.config import settings
from fastapi import FastAPI


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)
