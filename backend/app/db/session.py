"""Database connection. One engine for the app, one session per API request."""
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is empty. Paste the Neon connection string into the .env file.")
    # Neon pauses when idle. pool_pre_ping checks a connection is alive before using it,
    # and pool_recycle drops connections older than 5 minutes.
    return create_engine(url, pool_pre_ping=True, pool_recycle=300)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: opens a session for one request and always closes it."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
