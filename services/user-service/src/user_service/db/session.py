from user_service.core.config import settings
from sqlalchemy.orm import sessionmaker
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlmodel import Session
from typing import Any


# In Psycopg 3, setting prepare_threshold=None disables server-side prepared statements,
# preventing AWS RDS Proxy connection pinning when multiplexing transactions across pods.
connect_args: dict[str, Any] = {}
if settings.db_prepare_threshold is None:
    connect_args["prepare_threshold"] = None
else:
    connect_args["prepare_threshold"] = settings.db_prepare_threshold

# Optimized for Kubernetes horizontal scaling with AWS RDS Proxy:
# - Small pool per pod (prevents connection storms across hundreds of pods)
# - Controlled overflow to absorb micro-bursts without thundering herd
# - pool_recycle drops connections before AWS NAT / RDS Proxy idle timeouts
# - pool_pre_ping tests connection health to transparently recycle dropped connections
engine = create_engine(
    settings.database_url,
    echo=settings.echo_sql,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session.

    Guarantees session rollback on unhandled exceptions and immediate closure
    so underlying database connections return to the pool for reuse.
    """
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


get_db = get_session


def close_db_connections() -> None:
    """Dispose of the connection pool cleanly during pod termination."""
    engine.dispose()