"""Cross-linking: every clickable name, unit, tower, deal or partner the API sends must open a real entity."""
import uuid

from app.db.models import Risk
from app.services.common import Filters
from app.services.entities import ENTITIES, get_entity
from app.services.pages import (
    construction_summary, employees_summary, overview, projects, search,
)
from datetime import timedelta


def refs_in(value):
    """Find every {type, id, label} pointer anywhere inside a reply."""
    if isinstance(value, dict):
        if set(value) >= {"type", "id", "label"} and value["type"] in ENTITIES:
            yield value
        for item in value.values():
            yield from refs_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from refs_in(item)


def assert_all_open(snapshot, reply, where: str) -> int:
    count = 0
    for pointer in refs_in(reply):
        view = get_entity(snapshot, pointer["type"], uuid.UUID(pointer["id"]), quick=True)
        assert view is not None and view["title"], (where, pointer)
        count += 1
    return count


def test_every_link_on_the_page_summaries_opens(snapshot):
    f = Filters(snapshot.today - timedelta(days=729), snapshot.today)
    total = assert_all_open(snapshot, overview(snapshot, f), "overview")
    total += assert_all_open(snapshot, construction_summary(snapshot, f), "construction")
    total += assert_all_open(snapshot, employees_summary(snapshot, f), "employees")
    total += assert_all_open(snapshot, projects(snapshot), "projects")
    assert total > 300


def test_every_link_inside_a_risk_opens(snapshot):
    risks = snapshot.all(Risk)
    assert len(risks) >= 25
    for risk in risks:
        assert assert_all_open(snapshot, risk.entity_refs_json, risk.title) >= 1


def test_search_finds_every_story_character(snapshot):
    for words, kind in [("karthik reddy", "customer"), ("sneha rao", "employee"), ("arjun varma", "employee"),
                        ("skyway", "partner"), ("radhe greens", "project"), ("B-30", "unit")]:
        groups = search(snapshot, words)
        found = [item for group in groups for item in group["items"] if item["type"] == kind]
        assert found, words
        assert assert_all_open(snapshot, found, words) >= 1


def test_every_link_inside_a_drawer_opens(snapshot):
    """Follow the links one level deep from a sample of each entity type."""
    for kind, (model, _) in ENTITIES.items():
        for obj in snapshot.all(model)[:12]:
            assert_all_open(snapshot, get_entity(snapshot, kind, obj.id), kind)
