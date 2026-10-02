"""The portals must show each person only their own records. These tests try to break that."""
import json
import os

import pytest
from fastapi.testclient import TestClient

from app.db.models import Base, Customer, Unit
from app.db.session import get_engine
from app.services import portal
from app.services.entities import ENTITIES
from seed import stories as S
from seed.build import insert_rows

PORTAL_TEST_PASSWORD = os.environ["PORTAL_PASSWORD"]  # set in conftest.py, never a real password

KARTHIK, SNEHA, ARJUN = "karthik.reddy@example.com", "sneha.rao@radheconstructions.demo", "arjun.varma@radheconstructions.demo"


@pytest.fixture(scope="module")
def app_client(world):
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        insert_rows(conn, world.rows)
    from app.main import app
    from app.services.snapshot import _cache
    _cache["snapshot"] = None  # make the app load this fresh data
    with TestClient(app) as client:
        yield client


def sign_in(client, email) -> dict:
    client.cookies.clear()
    reply = client.post("/api/auth/login", json={"email": email, "password": PORTAL_TEST_PASSWORD})
    assert reply.status_code == 200, email
    return reply.json()


def links_in(value):
    if isinstance(value, dict):
        if set(value) >= {"type", "id", "label"} and value["type"] in ENTITIES:
            yield value["type"], value["id"]
        if "target_id" in value and "type" in value:
            yield value["type"], value["target_id"]
        for item in value.values():
            yield from links_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from links_in(item)


def test_each_person_lands_in_their_own_area(app_client):
    assert sign_in(app_client, KARTHIK)["home"] == "/my/journey"
    assert sign_in(app_client, SNEHA)["home"] == "/employee/day"
    assert sign_in(app_client, ARJUN)["role"] == "employee"


def test_customer_sees_his_own_journey_and_nothing_else(app_client, snapshot):
    sign_in(app_client, KARTHIK)
    journey = app_client.get("/api/portal/customer/journey").json()
    home = journey["blocks"][0]
    assert home["kind"] == "journey" and home["title"].startswith("Unit B-")
    assert [step["key"] for step in home["steps"]][:2] == ["booking", "agreement"]
    build = next(step for step in home["steps"] if step["key"] == "build")
    assert build["here"] and build["state"] == "issue" and "days late" in build["text"]

    # His home is described in full, and all 11 payments of his plan are listed with what happened to each.
    facts = {f["label"]: f["value"] for f in journey["blocks"][1]["items"]}
    assert facts["Project"] == "Radhe Skyline, Narsingi" and facts["Tower"] == "Tower B" and facts["Type"] == "4 BHK"
    assert facts["Floor"].endswith("of 30") and facts["Payment plan"] == "Construction-linked plan"
    assert "11 payments" in journey["blocks"][2]["text"] and "5 of the 11" in journey["blocks"][2]["text"]
    stages = journey["blocks"][3]["rows"]
    assert [row["stage"] for row in stages][3:6] == ["5th floor slab", "10th floor slab", "14th floor slab"]
    assert [row["state"]["label"] for row in stages][:6] == ["Paid"] * 5 + ["Held: this stage is running late"]
    profile = app_client.get("/api/portal/customer/profile").json()
    assert profile["blocks"][1]["title"].startswith("My home: unit B-")

    payments = app_client.get("/api/portal/customer/payments").json()
    assert payments["kpis"][1]["note"] == "45% of the total"
    requests = app_client.get("/api/portal/customer/requests").json()
    assert requests["kpis"][0]["value"] == 3  # his three unanswered emails

    everything = [app_client.get(f"/api/portal/customer/{page}") for page in portal.CUSTOMER_PAGES]
    assert all(reply.status_code == 200 for reply in everything)
    text = json.dumps([reply.json() for reply in everything]).lower()
    assert "health" not in text and "lead score" not in text and "commission" not in text
    others = [c.name for c in snapshot.all(Customer) if c.name != S.KARTHIK][:400]
    assert not [name for name in others if name.lower() in text]


def test_customer_cannot_reach_the_console_or_other_people(app_client, snapshot):
    sign_in(app_client, KARTHIK)
    for path in ("/api/overview", "/api/customers", "/api/risks", "/api/metrics/total_buyers", "/api/search?q=sneha",
                 "/api/portal/employee/day"):
        assert app_client.get(path).status_code == 403, path
    karthik = next(c for c in snapshot.all(Customer) if c.name == S.KARTHIK)
    mine = snapshot.unit(snapshot.bookings_of(karthik.id)[0])
    other = next(u for u in snapshot.all(Unit) if u.id != mine.id and u.id in snapshot.unit_booking)
    assert app_client.get(f"/api/portal/entity/unit/{mine.id}?view=quick").status_code == 200
    assert app_client.get(f"/api/portal/entity/unit/{other.id}?view=quick").status_code == 403
    assert app_client.get(f"/api/portal/entity/customer/{karthik.id}").status_code == 403  # the admin's view of him
    assert app_client.patch(f"/api/risks/{mine.id}", json={"status": "resolved"}).status_code == 403


def test_customer_replies_link_only_to_his_own_records(app_client, snapshot, world):
    user = sign_in(app_client, KARTHIK)
    allowed = portal.scope(snapshot, next(u for u in world.rows if getattr(u, "email", None) == KARTHIK and hasattr(u, "customer_id")))
    for page in portal.CUSTOMER_PAGES:
        for link in links_in(app_client.get(f"/api/portal/customer/{page}").json()):
            assert link in allowed and link[0] in portal.CUSTOMER_TYPES, (page, link)
    assert user["role"] == "customer"


def test_employee_sees_only_assigned_records(app_client, snapshot):
    sign_in(app_client, SNEHA)
    for page in portal.EMPLOYEE_PAGES:
        assert app_client.get(f"/api/portal/employee/{page}").status_code == 200, page
    day = app_client.get("/api/portal/employee/day").json()
    assert day["kpis"][0] == {"label": "My buyers", "value": 62, "kind": "number", "note": "Team average 38"}
    work = app_client.get("/api/portal/employee/work").json()
    assert len(work["blocks"][-1]["rows"]) == 62
    overdue = work["blocks"][1]  # the money her buyers owe, with the unpaid amount in view
    assert overdue["title"].startswith("Overdue payments of my buyers: ₹")
    assert next(c for c in overdue["columns"] if c["key"] == "outstanding")["default"] is True
    assert all(row["outstanding"] > 0 for row in overdue["rows"])
    day_tasks = day["blocks"][1]["rows"]
    assert day_tasks and all(row["status"]["label"] == "Past due date" for row in day_tasks)
    assert app_client.get("/api/portal/employee/meetings").json()["blocks"][0]["title"] == "Scheduled calls with buyers"

    mine = next(c for c in snapshot.all(Customer) if c.name == S.KARTHIK)
    theirs = next(c for c in snapshot.active_customers if c.rm_employee_id != mine.rm_employee_id)
    assert app_client.get(f"/api/portal/entity/customer/{mine.id}?view=quick").status_code == 200
    assert app_client.get(f"/api/portal/entity/customer/{theirs.id}?view=quick").status_code == 403
    for path in ("/api/overview", "/api/employees", "/api/portal/customer/journey"):
        assert app_client.get(path).status_code == 403, path


def test_sales_manager_sees_his_stalled_deals(app_client):
    sign_in(app_client, ARJUN)
    day = app_client.get("/api/portal/employee/day").json()
    assert day["kpis"][3]["label"] == "Stalled deals" and day["kpis"][3]["value"] == 9
    work = app_client.get("/api/portal/employee/work").json()
    assert work["blocks"][0]["title"] == "Stalled negotiations" and len(work["blocks"][0]["rows"]) == 9
    assert all("type" in row for row in work["blocks"][0]["rows"])  # his own leads are clickable
    card = app_client.get("/api/portal/employee/scorecard").json()
    assert card["kpis"][0]["value"] < 60


def test_wrong_portal_password_is_refused(app_client):
    app_client.cookies.clear()
    reply = app_client.post("/api/auth/login", json={"email": KARTHIK, "password": "not-the-password"},
                            headers={"x-forwarded-for": "198.51.100.7"})
    assert reply.status_code == 401
