"""Every protected read route of the console, plus the one write: changing a risk's status.

The routes are thin. All calculations live in app/services, so the V2 copilot can call the same functions.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import filters, paging, require_admin
from app.db.models import AuditLog, Employee, Project, Risk, User
from app.db.session import get_db
from app.scoring.scores import employee_scorecard
from app.schemas.auth import RiskStatusUpdate
from app.services import pages
from app.services.common import Filters, paginate
from app.services.entities import get_entity
from app.services.metrics import METRICS, get_metric, get_metric_rows
from app.services.snapshot import Snapshot, get_snapshot
from app.services.tables import risk_card

router = APIRouter(dependencies=[Depends(require_admin)])  # every route below is admin-only
Snap = Depends(get_snapshot)
F = Depends(filters)


# ---- search and KPIs ----
@router.get("/search", tags=["search"])
def search(q: str = Query(max_length=80), s: Snapshot = Snap):
    return pages.search(s, q)


def _known(key: str) -> str:
    if key not in METRICS:
        raise HTTPException(status_code=404, detail=f"Unknown metric '{key}'.")
    return key


@router.get("/metrics", tags=["metrics"])
def metrics(keys: str = Query(description="Comma-separated metric keys"), s: Snapshot = Snap, f: Filters = F):
    return [get_metric(s, _known(key.strip()), f) for key in keys.split(",") if key.strip()]


@router.get("/metrics/{key}", tags=["metrics"])
def metric(key: str, s: Snapshot = Snap, f: Filters = F):
    return get_metric(s, _known(key), f)


@router.get("/metrics/{key}/rows", tags=["metrics"])
def metric_rows(key: str, s: Snapshot = Snap, f: Filters = F, page: dict = Depends(paging)):
    return get_metric_rows(s, _known(key), f, **page)


# ---- page summaries (charts and panels) ----
@router.get("/overview", tags=["pages"])
def overview(s: Snapshot = Snap, f: Filters = F):
    return pages.overview(s, f)


@router.get("/sales/funnel", tags=["pages"])
def sales_funnel(s: Snapshot = Snap, f: Filters = F):
    return pages.sales_funnel(s, f)


@router.get("/customers/summary", tags=["pages"])
def customers_summary(s: Snapshot = Snap, f: Filters = F):
    return pages.customers_summary(s, f)


@router.get("/collections/summary", tags=["pages"])
def collections_summary(s: Snapshot = Snap, f: Filters = F):
    return pages.collections_summary(s, f)


@router.get("/collections/ageing", tags=["pages"])
def collections_ageing(s: Snapshot = Snap, f: Filters = F):
    return pages.collections_summary(s, f)["ageing"]


@router.get("/construction/summary", tags=["pages"])
def construction_summary(s: Snapshot = Snap, f: Filters = F):
    return pages.construction_summary(s, f)


@router.get("/construction/delay-impact", tags=["pages"])
def delay_impact(s: Snapshot = Snap, f: Filters = F):
    return pages.delay_impact(s, f)


@router.get("/employees/summary", tags=["pages"])
def employees_summary(s: Snapshot = Snap, f: Filters = F):
    return pages.employees_summary(s, f)


@router.get("/sales/lost/summary", tags=["pages"])
def sales_lost_summary(s: Snapshot = Snap, f: Filters = F):
    return pages.sales_lost(s, f)


# ---- projects and the unit grid ----
@router.get("/projects", tags=["projects"])
def projects(s: Snapshot = Snap):
    return pages.projects(s)


@router.get("/projects/{project_id}/inventory", tags=["projects"])
def inventory(project_id: uuid.UUID, tower_id: uuid.UUID | None = None, s: Snapshot = Snap):
    project = s.one(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return pages.inventory(s, project, tower_id)


# ---- lists: the table on each page and tab ----
LIST_ROUTES = {"/customers": "customers", "/leads": "leads", "/bookings": "bookings", "/demands": "demands",
               "/units": "units", "/employees": "employees", "/channel-partners": "partners",
               "/sales/stalled": "stalled", "/sales/lost": "lost", "/construction/milestones": "milestones",
               "/construction/contractors": "contractors", "/construction/budgets": "budgets",
               "/construction/quality": "quality", "/construction/safety": "safety", "/towers": "towers"}


def _list_route(name: str):
    def handler(request: Request, s: Snapshot = Snap, f: Filters = F, page: dict = Depends(paging)):
        columns, rows = pages.list_rows(s, name, f, dict(request.query_params))
        return paginate(columns, rows, **page)
    return handler


for _path, _name in LIST_ROUTES.items():
    router.add_api_route(_path, _list_route(_name), methods=["GET"], tags=["lists"], name=f"list_{_name}")


# ---- risks ----
@router.get("/risks", tags=["risks"])
def risks(category: str | None = None, status: str | None = None, severity: str | None = None, s: Snapshot = Snap):
    return pages.risks_page(s, category, status, severity)


@router.patch("/risks/{risk_id}", tags=["risks"])
def update_risk(risk_id: uuid.UUID, body: RiskStatusUpdate, s: Snapshot = Snap, db: Session = Depends(get_db),
                user: User = Depends(require_admin)):
    """The only data change the console allows. It is written to the audit log."""
    row = db.get(Risk, risk_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Risk not found.")
    before = row.status
    row.status = body.status
    row.resolved_at = datetime.now(timezone.utc) if body.status == "resolved" else None
    db.add(AuditLog(user_id=user.id, action="risk_status_change", entity_type="risk", entity_id=risk_id,
                    details_json={"from": before, "to": body.status}))
    db.commit()
    cached = s.one(Risk, risk_id)
    if cached is not None:  # keep the in-memory copy in step with the database
        cached.status, cached.resolved_at = row.status, row.resolved_at
        return risk_card(s, cached)
    return {"id": str(risk_id), "status": row.status}


# ---- entities: quick view (?view=quick) and drawer ----
@router.get("/employees/{employee_id}/scorecard", tags=["entities"])
def scorecard(employee_id: uuid.UUID, s: Snapshot = Snap):
    employee = s.one(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return employee_scorecard(s, employee)


ENTITY_ROUTES = {"/customers": "customer", "/units": "unit", "/towers": "tower", "/projects": "project",
                 "/employees": "employee", "/leads": "lead", "/bookings": "booking", "/channel-partners": "partner",
                 "/demands": "demand", "/milestones": "milestone", "/contractors": "contractor"}


def _entity_route(kind: str):
    def handler(entity_id: uuid.UUID, view: str = Query("full", pattern="^(quick|full)$"), s: Snapshot = Snap):
        result = get_entity(s, kind, entity_id, quick=view == "quick")
        if result is None:
            raise HTTPException(status_code=404, detail=f"{kind.capitalize()} not found.")
        return result
    return handler


for _path, _kind in ENTITY_ROUTES.items():
    router.add_api_route(f"{_path}/{{entity_id}}", _entity_route(_kind), methods=["GET"], tags=["entities"],
                         name=f"get_{_kind}")
