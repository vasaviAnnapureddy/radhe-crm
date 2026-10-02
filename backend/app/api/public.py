"""The one route the landing page needs. No login, and no personal data."""
from fastapi import APIRouter, Depends

from app.db.models import Project
from app.services.common import nice
from app.services.snapshot import Snapshot, get_snapshot

router = APIRouter(prefix="/public", tags=["public"])
FEATURED = ["Radhe Skyline", "Radhe Vanam Villas", "Radhe Bhoomi"]


@router.get("/featured-projects")
def featured_projects(s: Snapshot = Depends(get_snapshot)) -> list[dict]:
    projects = {p.name: p for p in s.all(Project)}
    return [{"name": p.name, "locality": p.locality, "type": nice(p.type), "status": nice(p.status),
             "hero_image": p.hero_image} for p in (projects.get(name) for name in FEATURED) if p]
