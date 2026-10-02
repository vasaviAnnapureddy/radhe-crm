"""End-to-end API tests: real login cookie, real routes, data loaded from a throwaway SQLite database."""
import pytest
from fastapi.testclient import TestClient

from app.api.console import ENTITY_ROUTES, LIST_ROUTES
from app.core.security import hash_password
from app.db.models import Base, Risk, User
from app.db.session import get_engine
from app.services.entities import ENTITIES
from app.services.metrics import METRICS
from seed.build import insert_rows

LOGIN = {"email": "admin@test.local", "password": "test-only-password"}


@pytest.fixture(scope="module")
def client(world):
    engine = get_engine()
    Base.metadata.create_all(engine)
    admin = User(email=LOGIN["email"], name="Test Admin", role="admin", is_active=True,
                 password_hash=hash_password(LOGIN["password"]))
    admin.id = world.rows[0].id.__class__(int=1)
    with engine.begin() as conn:
        insert_rows(conn, world.rows + [admin])
    with TestClient(app_under_test()) as test_client:
        yield test_client


def app_under_test():
    from app.main import app
    return app


@pytest.fixture(scope="module")
def signed_in(client):
    assert client.post("/api/auth/login", json=LOGIN).status_code == 200
    return client


def test_console_routes_need_a_login(client):
    client.cookies.clear()
    assert client.get("/api/overview").status_code == 401
    assert client.get("/api/customers").status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_public_routes_work_without_login(client):
    client.cookies.clear()
    assert client.get("/api/health").json() == {"status": "ok", "database": "ok"}
    featured = client.get("/api/public/featured-projects").json()
    assert len(featured) == 3 and set(featured[0]) == {"name", "locality", "type", "status", "hero_image"}


def test_wrong_password_gives_a_clear_error(client):
    reply = client.post("/api/auth/login", json={**LOGIN, "password": "wrong"})
    assert reply.status_code == 401 and reply.json()["detail"] == "Email or password is incorrect."


def test_login_sets_an_httponly_cookie(signed_in):
    reply = signed_in.post("/api/auth/login", json=LOGIN)
    assert "HttpOnly" in reply.headers["set-cookie"]
    assert "password" not in reply.text
    assert signed_in.get("/api/auth/me").json()["email"] == LOGIN["email"]


def test_every_metric_explains_itself(signed_in):
    for key in METRICS:
        body = signed_in.get(f"/api/metrics/{key}").json()
        assert {"value", "previous_value", "formula_text", "filters", "drilldown_url"} <= set(body), key
        rows = signed_in.get(f"/api/metrics/{key}/rows").json()
        assert rows["total"] == body["row_count"], key
    assert signed_in.get("/api/metrics/not_a_metric").status_code == 404
    assert len(signed_in.get("/api/metrics?keys=bookings_value,collections_overdue").json()) == 2


def test_overdue_metric_matches_the_seed_story(signed_in):
    body = signed_in.get("/api/metrics/blocked_by_delay").json()
    assert 6.7e7 <= body["value"] <= 6.9e7 and body["row_count"] == 41


@pytest.mark.parametrize("path", sorted(LIST_ROUTES))
def test_every_list_works_with_paging_sorting_and_search(signed_in, path):
    body = signed_in.get(f"/api{path}?page_size=5&date_from=2020-01-01").json()
    assert body["total"] > 0 and len(body["items"]) <= 5, path
    keys = {c["key"] for c in body["columns"]}
    assert keys <= set(body["items"][0]) | {"id"}, path
    assert 4 <= sum(c["default"] for c in body["columns"]) <= 7, path  # anti-congestion rule
    first = body["columns"][0]["key"]
    assert signed_in.get(f"/api{path}?sort={first}&order=desc&q=a").status_code == 200, path


@pytest.mark.parametrize("path", ["/overview", "/sales/funnel", "/sales/lost/summary", "/customers/summary",
                                  "/collections/summary", "/collections/ageing", "/construction/summary",
                                  "/construction/delay-impact", "/employees/summary", "/projects", "/risks",
                                  "/search?q=karthik", "/demands?tab=blocked", "/demands?tab=awaiting_bank",
                                  "/units?ageing=1", "/leads?stage=negotiation"])
def test_page_endpoints(signed_in, path):
    reply = signed_in.get(f"/api{path}")
    assert reply.status_code == 200 and reply.json(), path


@pytest.mark.parametrize("path,kind", sorted(ENTITY_ROUTES.items()))
def test_every_entity_has_a_quick_view_and_a_drawer(signed_in, snapshot, path, kind):
    model = ENTITIES[kind][0]
    for obj in snapshot.all(model)[:40]:
        quick = signed_in.get(f"/api{path}/{obj.id}?view=quick").json()
        assert quick["title"] and "tabs" not in quick, kind
        assert len(quick["facts"]) <= 12, kind  # hover cards stay small
        full = signed_in.get(f"/api{path}/{obj.id}").json()
        assert full["tabs"], kind
    assert signed_in.get(f"/api{path}/00000000-0000-0000-0000-000000000000").status_code == 404


def test_inventory_grid_and_filters(signed_in):
    skyline = next(p for p in signed_in.get("/api/projects").json() if p["name"] == "Radhe Skyline")
    tower_b = next(t for t in skyline["towers"] if t["name"] == "Tower B")
    grid = signed_in.get(f"/api/projects/{skyline['id']}/inventory?tower_id={tower_b['id']}").json()
    assert len(grid["floors"]) == 30 and all(len(f["units"]) == 6 for f in grid["floors"])
    assert signed_in.get(f"/api/customers?project_id={skyline['id']}").json()["total"] < \
        signed_in.get("/api/customers").json()["total"]
    assert signed_in.get("/api/overview?date_from=2026-02-01&date_to=2026-01-01").status_code == 422


def test_phones_are_masked_in_lists_and_full_in_the_drawer(signed_in, snapshot):
    row = signed_in.get("/api/customers?page_size=1").json()["items"][0]
    assert "xxxxxx" in row["phone"]
    profile = signed_in.get(f"/api/customers/{row['id']}").json()["tabs"][0]["blocks"][0]["items"]
    assert next(f["value"] for f in profile if f["label"] == "Phone").isdigit()


def test_risk_status_can_be_changed_and_is_saved(signed_in, snapshot):
    risk = signed_in.get("/api/risks").json()["items"][0]
    reply = signed_in.patch(f"/api/risks/{risk['id']}", json={"status": "acknowledged"})
    assert reply.status_code == 200 and reply.json()["status"] == "acknowledged"
    assert signed_in.patch(f"/api/risks/{risk['id']}", json={"status": "deleted"}).status_code == 422
    saved = next(r for r in signed_in.get("/api/risks").json()["items"] if r["id"] == risk["id"])
    assert saved["status"] == "acknowledged"


def test_login_is_rate_limited(client):
    headers = {"x-forwarded-for": "203.0.113.9"}  # a separate visitor, so other tests are not blocked
    bad = {**LOGIN, "password": "wrong"}
    codes = [client.post("/api/auth/login", json=bad, headers=headers).status_code for _ in range(6)]
    assert codes == [401, 401, 401, 401, 401, 429]


def test_logout_ends_the_session(signed_in):
    assert signed_in.post("/api/auth/login", json=LOGIN).status_code == 200
    assert signed_in.post("/api/auth/logout").status_code == 204
    assert signed_in.get("/api/auth/me").status_code == 401
