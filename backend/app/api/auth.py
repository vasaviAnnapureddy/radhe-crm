"""Login, logout and "who am I". The session is a signed token in an httpOnly cookie."""
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME, current_user, make_token
from app.core.config import get_settings
from app.core.security import verify_password
from app.db.models import AuditLog, User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger(__name__)
_failed: dict[str, deque] = defaultdict(deque)  # address -> times of recent wrong-password tries


def _client(request: Request) -> str:
    """The visitor's address. Behind Vercel or Render the real one is in X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")


def _user_out(user: User) -> UserOut:
    return UserOut(id=str(user.id), name=user.name, email=user.email, role=user.role)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    settings = get_settings()
    tries, now = _failed[_client(request)], time.time()
    while tries and now - tries[0] > 60:
        tries.popleft()
    if len(tries) >= settings.login_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait a minute and try again.")

    user = db.scalars(select(User).where(User.email == body.email.strip().lower())).first()
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        tries.append(now)
        log.warning("Failed login attempt")  # never log the email or the password
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    user.last_login_at = datetime.now(timezone.utc)
    db.add(AuditLog(user_id=user.id, action="login"))
    db.commit()
    token, max_age = make_token(user.id, body.remember)
    response.set_cookie(COOKIE_NAME, token, max_age=max_age, httponly=True, secure=settings.cookie_secure,
                        samesite="lax", path="/")
    return _user_out(user)


@router.post("/logout", status_code=204)
def logout(response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.add(AuditLog(user_id=user.id, action="logout"))
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return _user_out(user)
