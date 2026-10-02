"""Shared pieces for the routes: who is logged in, the global filters, paging."""
import uuid
from datetime import date, datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Query, Request

from app.core.config import get_settings
from app.db.models import Project, User
from app.services.common import Filters
from app.services.snapshot import Snapshot, get_snapshot

COOKIE_NAME = "radhe_session"


def make_token(user_id: uuid.UUID, remember: bool) -> tuple[str, int | None]:
    """Returns (signed token, cookie lifetime in seconds). No lifetime = cookie ends when the browser closes."""
    settings = get_settings()
    life = timedelta(days=settings.jwt_remember_days) if remember else timedelta(minutes=settings.jwt_expire_minutes)
    token = jwt.encode({"sub": str(user_id), "exp": datetime.now(timezone.utc) + life}, settings.jwt_secret, "HS256")
    return token, int(life.total_seconds()) if remember else None


def current_user(request: Request, s: Snapshot = Depends(get_snapshot)) -> User:
    """Every /console route depends on this. No valid cookie means 401, and the frontend sends you to /login."""
    problem = HTTPException(status_code=401, detail="Please sign in.")
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise problem
    try:
        user_id = uuid.UUID(jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise problem
    user = s.one(User, user_id)
    if user is None or not user.is_active:
        raise problem
    return user


def filters(s: Snapshot = Depends(get_snapshot), date_from: date | None = None, date_to: date | None = None,
            project_id: uuid.UUID | None = None) -> Filters:
    """The global filters. Default range: the last 90 days."""
    end = date_to or s.today
    start = date_from or end - timedelta(days=89)
    if start > end:
        raise HTTPException(status_code=422, detail="date_from must be on or before date_to.")
    if project_id and s.one(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return Filters(start, end, project_id)


def paging(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=5000), sort: str | None = None,
           order: str = Query("asc", pattern="^(asc|desc)$"), q: str | None = Query(None, max_length=80)) -> dict:
    return {"page": page, "page_size": page_size, "sort": sort, "order": order, "q": q}
