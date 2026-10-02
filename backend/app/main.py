"""Backend starting point. Run from the backend folder: uvicorn app.main:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api import auth, console, health, public
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.snapshot import get_snapshot

setup_logging()
settings = get_settings()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup: load the data into memory so the first page is fast."""
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is empty. Set it in the .env file.")
    try:
        snapshot = get_snapshot()
        log.info("Data loaded for %s", snapshot.today)
    except Exception as exc:  # the database may still be waking up; the first request will try again
        log.error("Could not load data at startup: %s", type(exc).__name__)
    yield


app = FastAPI(
    title="Radhe Constructions Console API",
    version="0.2.0",
    lifespan=lifespan,
    # The interactive API docs are for development only.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
)

# Every route lives under /api, so the frontend can always call /api/... on its own address.
api = APIRouter(prefix="/api")
api.include_router(health.router)
api.include_router(auth.router)
api.include_router(public.router)
api.include_router(console.router)

app.include_router(api)
