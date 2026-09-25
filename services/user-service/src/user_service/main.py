from user_service.db import close_db_connections
from user_service.core.config import settings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Pod startup
    yield
    # Pod shutdown (SIGTERM): dispose connection pool cleanly
    close_db_connections()


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)
