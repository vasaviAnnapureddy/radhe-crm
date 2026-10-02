"""Routes for the employee and customer portals.

No route here takes a customer id or an employee id. The server reads the signed-in user
and returns only that person's data, so nobody can ask for someone else's.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import current_user
from app.db.models import User
from app.services import portal
from app.services.snapshot import Snapshot, get_snapshot

router = APIRouter(prefix="/portal", tags=["portal"])


def _member(role: str):
    def check(user: User = Depends(current_user)) -> User:
        linked = user.employee_id if role == "employee" else user.customer_id
        if user.role != role or linked is None:
            raise HTTPException(status_code=403, detail="This area is not available to your account.")
        return user
    return check


@router.get("/employee/{page}")
def employee_page(page: str, user: User = Depends(_member("employee")), s: Snapshot = Depends(get_snapshot)):
    if page not in portal.EMPLOYEE_PAGES:
        raise HTTPException(status_code=404, detail="Page not found.")
    return portal.scrub(portal.employee_page(s, user, page), portal.scope(s, user))


@router.get("/customer/{page}")
def customer_page(page: str, user: User = Depends(_member("customer")), s: Snapshot = Depends(get_snapshot)):
    if page not in portal.CUSTOMER_PAGES:
        raise HTTPException(status_code=404, detail="Page not found.")
    return portal.scrub(portal.customer_page(s, user, page), portal.scope(s, user))


@router.get("/entity/{kind}/{entity_id}")
def entity(kind: str, entity_id: uuid.UUID, view: str = Query("full", pattern="^(quick|full)$"),
           user: User = Depends(current_user), s: Snapshot = Depends(get_snapshot)):
    """A hover card or drawer inside a portal, allowed only for the person's own records."""
    if user.role not in ("employee", "customer"):
        raise HTTPException(status_code=403, detail="This area is not available to your account.")
    result = portal.portal_entity(s, user, kind, entity_id, quick=view == "quick")
    if result is None:  # the same answer whether it does not exist or is not theirs
        raise HTTPException(status_code=403, detail="You do not have access to this record.")
    return result
