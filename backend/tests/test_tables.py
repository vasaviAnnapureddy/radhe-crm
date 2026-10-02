"""Checks on the table rows and on how the date range changes what the API returns."""
import uuid
from datetime import timedelta

from app.services.common import Filters
from app.services.entities import ENTITIES
from app.services.metrics import METRICS, get_metric
from app.services.pages import LIST_NAMES, list_rows, sales_funnel


def test_every_clickable_row_opens_a_real_entity(snapshot):
    """A row's (type, target_id) must point at something that exists. An interaction row opens its customer."""
    checked = 0
    for kind, (model, builder) in ENTITIES.items():
        for obj in snapshot.all(model)[:25]:
            for tab in builder(snapshot, obj, False)["tabs"]:
                for block in tab["blocks"]:
                    for row in block.get("rows", []) if block["kind"] == "table" else []:
                        if "type" in row:
                            target = snapshot.one(ENTITIES[row["type"]][0], uuid.UUID(row["target_id"]))
                            assert target is not None, (kind, tab["key"], row["type"])
                            checked += 1
    assert checked > 500


def test_list_rows_point_at_real_entities(snapshot):
    everything = Filters(snapshot.today - timedelta(days=5000), snapshot.today)
    for name in LIST_NAMES:
        for row in list_rows(snapshot, name, everything, {})[1][:50]:
            if "type" in row:
                assert snapshot.one(ENTITIES[row["type"]][0], uuid.UUID(row["target_id"])) is not None, name


def test_the_date_range_changes_period_numbers(snapshot):
    month = Filters(snapshot.today - timedelta(days=29), snapshot.today)
    year = Filters(snapshot.today - timedelta(days=364), snapshot.today)
    for key in ("bookings_value", "collections_received", "new_leads", "site_visits", "demands_raised"):
        assert get_metric(snapshot, key, month)["value"] < get_metric(snapshot, key, year)["value"], key
    for name in ("leads", "bookings", "lost", "demands"):
        assert len(list_rows(snapshot, name, month, {})[1]) < len(list_rows(snapshot, name, year, {})[1]), name
    assert sales_funnel(snapshot, month)["funnel"]["series"][0]["data"][0] < sales_funnel(snapshot, year)["funnel"]["series"][0]["data"][0]


def test_as_of_today_numbers_say_what_changed_in_the_period(snapshot):
    month = Filters(snapshot.today - timedelta(days=29), snapshot.today)
    year = Filters(snapshot.today - timedelta(days=364), snapshot.today)
    overdue_month, overdue_year = (get_metric(snapshot, "collections_overdue", f) for f in (month, year))
    assert overdue_month["value"] == overdue_year["value"]              # the total is "as of today"
    assert overdue_month["period_note"] != overdue_year["period_note"]  # but the note follows the range
    assert overdue_month["is_flow"] is False and get_metric(snapshot, "new_leads", month)["is_flow"] is True
    # The Customers page counts buyers who booked in the period, so its numbers follow the range.
    everything = Filters(snapshot.today - timedelta(days=729), snapshot.today)
    buyers = [get_metric(snapshot, "total_buyers", f)["value"] for f in (month, year, everything)]
    assert buyers[0] < buyers[1] < buyers[2] == 798
    assert len(list_rows(snapshot, "customers", month, {})[1]) == buyers[0]
    assert all("is_flow" in get_metric(snapshot, key, month) for key in METRICS)
