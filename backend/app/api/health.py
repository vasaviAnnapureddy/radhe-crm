"""GET /api/health: is the API alive, and can it reach the database?"""
import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import get_engine

router = APIRouter(tags=["health"])
log = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "ok"
    except Exception as exc:
        # Log only the error type. The full message can contain the connection string.
        log.error("Database check failed: %s", type(exc).__name__)
        database = "error"
    return {"status": "ok", "database": database}
