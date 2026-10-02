"""The KPI registry. Every number on a KPI card comes from here.

Each metric returns its value AND the rows behind it, so the "Explain" drawer can show
the formula, the filters and the exact rows. Nothing is hard-coded.
"""
from datetime import timedelta

from app.db.models import (
    Booking, ConstructionMilestone, Customer, CustomerInteraction, Demand, Employee, Lead, Project,
    ProjectBudget, QualityIssue, Receipt, Risk, SiteVisit, Task, Tower, Unit,
)
from app.scoring.scores import customer_health, employee_scorecard
from app.services.common import Filters, inr, paginate, pct
from app.services.snapshot import num, to_date
from app.services.tables import build

METRICS: dict[str, dict] = {}


def metric(key: str, label: str, kind: str, table: str, flow: bool = False, note=None):
    """Register a KPI.

    A `flow` KPI is counted over the date range, so it has a previous period and a trend.
    The others are "as of today" numbers (a stock). For those, `note` can say what changed
    inside the chosen period, so the card still responds to the date filter.
    """
    def register(fn):
        METRICS[key] = {"label": label, "kind": kind, "table": table, "flow": flow, "fn": fn, "note": note}
        return fn
    return register


# ---- small selectors shared by the metrics ----
def project_of_booking(s, booking):
    return s.unit(booking).project_id


def bookings_in(s, f: Filters, active_only: bool = True) -> list:
    pool = s.active_bookings if active_only else s.all(Booking)
    return [b for b in pool if f.covers(b.booked_on) and f.project_ok(project_of_booking(s, b))]


def demands_of(s, f: Filters) -> list:
    """Demands of active bookings in the chosen project."""
    return [d for b in s.active_bookings if f.project_ok(project_of_booking(s, b)) for d in s.demands(b)]


def buyers_of(s, f: Filters) -> list:
    """Buyers who booked a home in the chosen period (and project). "All time" gives every buyer."""
    return [c for c in s.active_customers
            if any(f.covers(b.booked_on) and f.project_ok(project_of_booking(s, b)) for b in s.bookings_of(c.id))]


def stages_of(s, f: Filters) -> list:
    return [m for m in s.all(ConstructionMilestone) if f.project_ok(s.project_id_of_tower(m.tower_id))]


def staff(s) -> list:
    return [e for e in s.all(Employee) if e.status != "exited"]


# ---- Overview ----
@metric("bookings_value", "Bookings value", "money", "bookings", flow=True)
def bookings_value(s, f):
    rows = bookings_in(s, f)
    return sum(num(b.agreement_value) for b in rows), rows, "Sum of agreement value of bookings made in the period (cancelled bookings left out)."


@metric("collections_received", "Collections received", "money", "receipts", flow=True)
def collections_received(s, f):
    rows = [r for r in s.all(Receipt) if f.covers(r.received_on)
            and f.project_ok(project_of_booking(s, s.one(Booking, s.one(Demand, r.demand_id).booking_id)))]
    return sum(num(r.amount) for r in rows), rows, "Sum of receipts received in the period."


def _note_overdue(s, f):
    amount = sum(s.left(d) for d in demands_of(s, f) if s.late(d) and f.covers(d.due_on))
    return f"{inr(amount)} of it fell due in this period"


def _note_listed(s, f):
    count = sum(1 for u in s.all(Unit) if u.status in ("available", "blocked") and f.project_ok(u.project_id) and f.covers(u.listed_on))
    return f"{count} of these units were listed in this period"


def _note_new_buyers(s, f):
    count = sum(1 for c in buyers_of(s, f) if f.covers(min(b.booked_on for b in s.bookings_of(c.id))))
    return f"{count} new buyers in this period"


def _note_queries(s, f):
    buyers = {c.id for c in buyers_of(s, f)}
    count = sum(1 for i in s.all(CustomerInteraction) if i.customer_id in buyers and i.direction == "inbound"
                and i.needs_reply and i.replied_at is None and f.covers(to_date(i.occurred_at)))
    return f"{count} of them arrived in this period"


def _note_joined(s, f):
    return f"{sum(1 for e in staff(s) if f.covers(e.joined_on))} joined in this period"


@metric("collections_overdue", "Collections overdue", "money", "demands", note=_note_overdue)
def collections_overdue(s, f):
    rows = [d for d in demands_of(s, f) if s.late(d)]
    buyers = {s.one(Booking, d.booking_id).customer_id for d in rows}
    projects = {project_of_booking(s, s.one(Booking, d.booking_id)) for d in rows}
    total = sum(s.left(d) for d in rows)
    return total, rows, (f"Collections overdue {inr(total)} = sum of unpaid demands past their due date, "
                         f"{len(buyers)} customers, {len(projects)} projects. Part payments are subtracted.")


@metric("unsold_inventory_value", "Unsold inventory value", "money", "units", note=_note_listed)
def unsold_inventory_value(s, f):
    rows = [u for u in s.all(Unit) if u.status in ("available", "blocked") and f.project_ok(u.project_id)]
    return sum(s.price(u) for u in rows), rows, f"Sum of list price of {len(rows)} units that are available or blocked."


@metric("open_high_risks", "Open high risks", "number", "risks")
def open_high_risks(s, f):
    rows = [r for r in s.all(Risk) if r.severity == "high" and r.status != "resolved"]
    return len(rows), rows, "Count of risks with severity High that are not resolved."


# ---- Sales ----
@metric("new_leads", "New leads", "number", "leads", flow=True)
def new_leads(s, f):
    rows = [x for x in s.all(Lead) if f.covers(to_date(x.created_at)) and f.project_ok(x.preferred_project_id)]
    return len(rows), rows, "Count of leads created in the period."


def visits_in(s, f):
    return [v for v in s.all(SiteVisit) if v.status == "done" and f.covers(to_date(v.scheduled_at)) and f.project_ok(v.project_id)]


@metric("site_visits", "Site visits", "number", "visits", flow=True)
def site_visits(s, f):
    rows = visits_in(s, f)
    return len(rows), rows, "Count of site visits completed in the period."


@metric("visit_to_booking_conversion", "Visit-to-booking conversion", "percent", "bookings", flow=True)
def conversion(s, f):
    rows, visits = bookings_in(s, f, active_only=False), len(visits_in(s, f))
    return pct(len(rows), visits), rows, f"Bookings / site visits done = {len(rows)} / {visits} in the period."


@metric("cancellations", "Cancellations", "number", "bookings", flow=True)
def cancellations(s, f):
    rows = [b for b in bookings_in(s, f, active_only=False) if b.status == "cancelled"]
    return len(rows), rows, "Count of bookings made in the period that were later cancelled."


# ---- Customers ----
@metric("total_buyers", "Total buyers", "number", "customers", flow=True)
def total_buyers(s, f):
    rows = buyers_of(s, f)
    return len(rows), rows, "Count of customers who booked a home in the period (cancelled bookings left out)."


@metric("nri_share", "NRI share", "percent", "customers", flow=True)
def nri_share(s, f):
    buyers = buyers_of(s, f)
    rows = [c for c in buyers if c.is_nri]
    return pct(len(rows), len(buyers)), rows, f"NRI buyers / all buyers = {len(rows)} / {len(buyers)}."


@metric("average_health", "Average health", "score", "customers", flow=True)
def average_health(s, f):
    rows = buyers_of(s, f)
    total = sum(customer_health(s, c)["score"] for c in rows)
    return round(total / len(rows)) if rows else 0, rows, "Average of buyer health (0 to 100): payments 40, engagement 25, complaints 20, loan 15."


@metric("at_risk_buyers", "At-risk buyers", "number", "customers", flow=True)
def at_risk_buyers(s, f):
    rows = [c for c in buyers_of(s, f) if customer_health(s, c)["band"] == "risk"]
    return len(rows), rows, "Count of buyers whose health score is below 60."


@metric("open_queries", "Open queries", "number", "interactions", flow=True)
def open_queries(s, f):
    buyers = {c.id for c in buyers_of(s, f)}
    rows = [i for i in s.all(CustomerInteraction)
            if i.customer_id in buyers and i.direction == "inbound" and i.needs_reply and i.replied_at is None]
    return len(rows), rows, "Count of buyer messages that are still waiting for a reply."


# ---- Collections ----
@metric("demands_raised", "Demands raised", "money", "demands", flow=True)
def demands_raised(s, f):
    rows = [d for d in demands_of(s, f) if f.covers(d.raised_on)]
    return sum(num(d.amount) for d in rows), rows, "Sum of demands raised in the period."


@metric("collection_efficiency", "Collection efficiency", "percent", "demands", flow=True)
def collection_efficiency(s, f):
    rows = [d for d in demands_of(s, f) if f.covers(d.due_on)]
    return s.efficiency(rows) or 0.0, rows, "Amount collected / amount demanded, for demands that fell due in the period."


@metric("blocked_by_delay", "Blocked by construction delay", "money", "demands")
def blocked_by_delay(s, f):
    rows = [d for m in s.delayed.values() if f.project_ok(s.project_id_of_tower(m.tower_id)) for d in s.blocked(m)]
    return sum(num(d.amount) for d in rows), rows, (
        f"Sum of {len(rows)} demands that cannot be raised because their construction stage is late.")


# ---- Construction ----
def _note_finished(s, f):
    return f"{sum(1 for m in stages_of(s, f) if f.covers(m.actual_date))} stages finished in this period"


def _note_quality(s, f):
    count = sum(1 for q in s.all(QualityIssue) if q.status == "open" and f.covers(q.raised_on)
                and f.project_ok(s.project_id_of_tower(q.tower_id)))
    return f"{count} of them were raised in this period"


@metric("towers_on_schedule", "Towers on schedule", "number", "milestones", note=_note_finished)
def towers_on_schedule(s, f):
    towers = [t for t in s.all(Tower) if f.project_ok(t.project_id)]
    late = [m for m in s.delayed.values() if f.project_ok(s.project_id_of_tower(m.tower_id))]
    ok = len(towers) - len({m.tower_id for m in late})
    return ok, late, f"{ok} of {len(towers)} towers have no stage past its planned date. The rows are the late stages."


@metric("average_slip_days", "Average slip", "days", "milestones", flow=True)
def average_slip_days(s, f):
    rows = [m for m in stages_of(s, f) if f.covers(m.actual_date) or (m.id in s.delayed and f.covers(m.planned_date))]
    return round(sum(s.slip(m) for m in rows) / len(rows), 1) if rows else 0, rows, (
        "Average days behind plan, for stages finished in the period and stages that fell late in it.")


@metric("milestones_due_this_month", "Milestones due this month", "number", "milestones")
def milestones_due(s, f):
    rows = [m for m in stages_of(s, f) if m.actual_date is None
            and (m.planned_date.year, m.planned_date.month) == (s.today.year, s.today.month)]
    return len(rows), rows, "Count of unfinished stages planned for this calendar month."


@metric("cost_variance_pct", "Cost variance", "percent", "budgets")
def cost_variance(s, f):
    rows = [b for b in s.all(ProjectBudget) if f.project_ok(b.project_id)]
    budget = sum(num(b.budget_amount) for b in rows)
    actual = sum(num(b.actual_amount) for b in rows)
    return round(100 * (actual - budget) / budget, 1) if budget else 0, rows, (
        f"(Actual - budget) / budget = ({inr(actual)} - {inr(budget)}) / {inr(budget)}.")


@metric("open_quality_issues", "Open quality issues", "number", "quality", note=_note_quality)
def open_quality_issues(s, f):
    rows = [q for q in s.all(QualityIssue) if q.status == "open" and f.project_ok(s.project_id_of_tower(q.tower_id))]
    return len(rows), rows, "Count of quality issues that are still open."


# ---- Employees ----
@metric("headcount", "Headcount", "number", "employees", note=_note_joined)
def headcount(s, f):
    rows = staff(s)
    return len(rows), rows, "Count of employees who have not left."


@metric("new_joiners", "New joiners", "number", "employees", flow=True)
def new_joiners(s, f):
    rows = sorted((e for e in staff(s) if f.covers(e.joined_on)), key=lambda e: e.joined_on, reverse=True)
    return len(rows), rows, "Count of employees whose joining date falls in the period."


@metric("avg_target_achievement", "Average target achievement", "percent", "employees")
def avg_target_achievement(s, f):
    rows = staff(s)
    return round(sum(employee_scorecard(s, e)["score"] for e in rows) / len(rows)), rows, (
        "Average scorecard score. Each score = sum of (weight x achievement vs target) for that role.")


@metric("people_needing_attention", "People needing attention", "number", "employees")
def people_needing_attention(s, f):
    rows = [e for e in staff(s) if employee_scorecard(s, e)["needs_attention"]]
    return len(rows), rows, "Count of employees whose scorecard score is below 60."


@metric("overdue_tasks", "Overdue tasks", "number", "tasks")
def overdue_tasks(s, f):
    rows = [t for t in s.all(Task) if t.status == "open" and t.due_on < s.today]
    return len(rows), rows, "Count of open tasks past their due date."


METRICS["collected"] = {**METRICS["collections_received"], "label": "Collected"}


# ---- public functions used by the API (and later by the V2 copilot) ----
def get_metric(s, key: str, f: Filters) -> dict:
    spec = METRICS[key]
    value, rows, formula = spec["fn"](s, f)
    out = {"key": key, "label": spec["label"], "kind": spec["kind"], "value": value, "previous_value": None,
           "formula_text": formula, "row_count": len(rows), "sparkline": None,
           "is_flow": spec["flow"], "period_note": spec["note"](s, f) if spec["note"] else None,
           "filters": {"date_from": f.date_from if spec["flow"] else None, "date_to": f.date_to if spec["flow"] else None,
                       "project": s.one(Project, f.project_id).name if f.project_id else "All projects"},
           "drilldown_url": f"/api/metrics/{key}/rows"}
    if spec["flow"]:
        out["previous_value"] = spec["fn"](s, f.previous())[0]
        # Six equal slices of the period, oldest first, for the tiny trend line.
        step = (f.date_to - f.date_from + timedelta(days=1)) / 6
        out["sparkline"] = [spec["fn"](s, Filters(f.date_from + step * i, f.date_from + step * (i + 1) - timedelta(days=1),
                                                  f.project_id))[0] for i in range(6)]
    return out


def get_metric_rows(s, key: str, f: Filters, **page) -> dict:
    spec = METRICS[key]
    columns, rows = build(s, spec["table"], spec["fn"](s, f)[1])
    return paginate(columns, rows, **page)
