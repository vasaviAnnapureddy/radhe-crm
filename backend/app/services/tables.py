"""One definition per table type: its columns and how to turn a database row into a table row.

Page lists, drawer tabs and the "Explain this number" rows all reuse these, so a customer row
looks the same everywhere. Phones and emails are masked here (privacy by default).
"""
from app.db.models import (
    Booking, ChannelPartner, ConstructionMilestone, Contractor, CpCommission, Customer, Demand, Department,
    Employee, Lead, PlanMilestone, PaymentPlan, Project, QualityIssue, Tower, Unit,
)
from app.scoring.scores import (
    ON_TIME_GRACE_DAYS, SALES_ROLES, SITE_ROLES, customer_health, employee_scorecard, rm_stats, sales_stats,
    score_lead,
)
from app.services.common import col, mask_phone, nice, pct, ref, score_cell, status
from app.services.snapshot import num, to_date

STAGE_LABELS = {"foundation": "Foundation", "slab_5": "5th floor slab", "slab_10": "10th floor slab",
                "slab_14": "14th floor slab", "slab_18": "18th floor slab", "top_slab": "Top floor slab",
                "brickwork": "Brickwork", "finishing": "Finishing", "handover": "Handover"}
TABLES: dict[str, tuple[list, callable, str | None]] = {}


def table(name: str, kind: str | None, columns: list[dict], target=None):
    """Register a row builder. `kind` is the entity type a row opens when clicked.

    `target` gives the id of that entity when it is not the row itself. Example: a row in the
    interactions table opens the CUSTOMER, so its target is the interaction's customer_id.
    """
    def register(fn):
        TABLES[name] = (columns, fn, kind, target)
        return fn
    return register


def build(s, name: str, objs) -> tuple[list[dict], list[dict]]:
    columns, fn, kind, target = TABLES[name]
    rows = []
    for obj in objs:
        row = fn(s, obj)
        row["id"] = str(obj.id)  # unique per row
        if kind:
            row["type"] = kind
            row["target_id"] = str(target(obj) if target else obj.id)  # the entity to open
        rows.append(row)
    return columns, rows


def block(s, name: str, objs, title: str | None = None) -> dict:
    """A table block for a drawer tab."""
    columns, rows = build(s, name, objs)
    return {"kind": "table", "title": title, "columns": columns, "rows": rows}


def tower_label(s, tower) -> str:
    return f"{s.one(Project, tower.project_id).name} {tower.name}"


def unit_ref(s, unit):
    return ref("unit", unit, unit.unit_no)


@table("bookings", "booking", [
    col("customer", "Customer", "ref"), col("unit", "Unit", "ref"), col("booked_on", "Booked on", "date"),
    col("value", "Agreement value", "money"), col("paid_pct", "Paid", "percent"), col("overdue", "Overdue", "money"),
    col("status", "Status", "status"), col("project", "Project", default=False), col("plan", "Payment plan", default=False),
    col("sales", "Sales manager", "ref", False), col("partner", "Channel partner", "ref", False)])
def booking_row(s, b: Booking) -> dict:
    unit = s.unit(b)
    return {"customer": ref("customer", s.one(Customer, b.customer_id)), "unit": unit_ref(s, unit),
            "booked_on": b.booked_on, "value": num(b.agreement_value),
            "paid_pct": pct(s.booking_paid(b), num(b.agreement_value)), "overdue": s.booking_overdue(b)[0],
            "status": status(b.status), "project": s.one(Project, unit.project_id).name,
            "plan": s.one(PaymentPlan, b.payment_plan_id).name, "sales": ref("employee", s.one(Employee, b.employee_id)),
            "partner": ref("partner", s.one(ChannelPartner, b.channel_partner_id))}


@table("demands", "demand", [
    col("customer", "Customer", "ref"), col("milestone", "Payment stage"), col("amount", "Amount", "money"),
    col("outstanding", "Unpaid", "money"), col("due_on", "Due date", "date"), col("days_overdue", "Days overdue", "days"),
    col("status", "Status", "status"), col("unit", "Unit", "ref", False), col("bank", "Bank", default=False),
    col("reminders", "Reminders sent", "number", False), col("raised_on", "Raised on", "date", False)])
def demand_row(s, d: Demand) -> dict:
    booking = s.one(Booking, d.booking_id)
    loan = s.loan(booking)
    if d.construction_milestone_id in s.delayed and d.status == "not_raised":
        state = status("blocked", "risk", "Blocked by delay")
    elif s.late(d):
        state = status("overdue")
    elif d.due_on and s.left(d) == 0:
        state = status("paid")
    else:
        state = status(d.status)
    return {"customer": ref("customer", s.one(Customer, booking.customer_id)), "unit": unit_ref(s, s.unit(booking)),
            "milestone": s.one(PlanMilestone, d.plan_milestone_id).name, "amount": num(d.amount), "due_on": d.due_on,
            "days_overdue": s.late(d) or None, "status": state, "outstanding": s.left(d) or None,
            "bank": loan.bank if loan else None, "reminders": d.reminders_sent, "raised_on": d.raised_on}


@table("receipts", None, [
    col("customer", "Customer", "ref"), col("unit", "Unit", "ref"), col("milestone", "Milestone"),
    col("amount", "Amount", "money"), col("received_on", "Received on", "date"), col("mode", "Mode")])
def receipt_row(s, r) -> dict:
    demand = s.one(Demand, r.demand_id)
    booking = s.one(Booking, demand.booking_id)
    return {"customer": ref("customer", s.one(Customer, booking.customer_id)), "unit": unit_ref(s, s.unit(booking)),
            "milestone": s.one(PlanMilestone, demand.plan_milestone_id).name, "amount": num(r.amount),
            "received_on": r.received_on, "mode": nice(r.mode)}


@table("units", "unit", [
    col("unit", "Unit", "ref"), col("project", "Project"), col("config", "Type"), col("facing", "Facing"),
    col("price", "Price", "money"), col("status", "Status", "status"), col("days_unsold", "Days unsold", "days"),
    col("floor", "Floor", "number", False), col("area", "Area", "number", False), col("buyer", "Buyer", "ref", False)])
def unit_row(s, u: Unit) -> dict:
    booking = s.unit_booking.get(u.id)
    return {"unit": unit_ref(s, u), "project": s.one(Project, u.project_id).name, "config": u.config, "facing": u.facing,
            "price": s.price(u), "status": status(u.status, "neutral" if u.status == "available" else None),
            "days_unsold": s.days_unsold(u), "floor": u.floor, "area": num(u.sba_sft or u.plot_sqyd),
            "buyer": ref("customer", s.one(Customer, booking.customer_id)) if booking else None}


@table("customers", "customer", [
    col("name", "Buyer", "ref"), col("kind", "Type"), col("value", "Agreement value", "money"),
    col("paid_pct", "Paid", "percent"), col("overdue", "Overdue", "money"), col("health", "Health", "score"),
    col("rm", "RM", "ref"), col("units", "Units", "number", False), col("last_contact", "Last contact", "date", False),
    col("country", "Country", default=False), col("phone", "Phone", default=False)])
def customer_row(s, c: Customer) -> dict:
    bookings = s.bookings_of(c.id)
    value = sum(num(b.agreement_value) for b in bookings)
    return {"name": ref("customer", c), "kind": "NRI" if c.is_nri else nice(c.type), "value": value,
            "paid_pct": pct(sum(s.booking_paid(b) for b in bookings), value), "overdue": s.customer_overdue(c.id)[0],
            "health": score_cell(customer_health(s, c)["score"]), "rm": ref("employee", s.one(Employee, c.rm_employee_id)),
            "units": len(bookings), "last_contact": s.last_contact(c.id), "country": c.country,
            "phone": mask_phone(c.phone)}


@table("leads", "lead", [
    col("name", "Lead", "ref"), col("stage", "Stage", "status"), col("source", "Source"), col("budget", "Budget", "money"),
    col("project", "Project"), col("owner", "Owner", "ref"), col("idle_days", "Days since activity", "days"),
    col("config", "Wants", default=False), col("score", "Lead score", "score", False),
    col("reason", "Lost reason", default=False), col("created", "Created", "date", False),
    col("phone", "Phone", default=False)])
def lead_row(s, lead: Lead) -> dict:
    return {"name": ref("lead", lead), "stage": status(lead.stage), "source": lead.source, "budget": num(lead.budget_max),
            "project": s.one(Project, lead.preferred_project_id).name,
            "owner": ref("employee", s.one(Employee, lead.owner_employee_id)), "idle_days": s.idle_days(lead),
            "config": lead.preferred_config, "score": score_cell(score_lead(s, lead)["score"], 70, 45),
            "reason": lead.lost_reason, "created": to_date(lead.created_at), "phone": mask_phone(lead.phone)}


def employee_headline(s, emp: Employee) -> str:
    """One line that matters for this person's role."""
    if emp.role_title in SALES_ROLES:
        me = sales_stats(s)["people"][emp.id]
        return f"{len(me['bookings'])} bookings, {me['conversion']:.0f}% conversion, {len(me['idle'])} stalled"
    if emp.role_title == "Relationship Manager":
        me = rm_stats(s)["people"].get(emp.id)
        return f"{len(me['buyers'])} buyers, {me['open_queries']} open queries" if me else "No buyers yet"
    if emp.role_title in SITE_ROLES:
        owned = s.kids(ConstructionMilestone, "owner_employee_id", emp.id)
        issues = sum(q.status == "open" for q in s.kids(QualityIssue, "owner_employee_id", emp.id))
        return f"{len(owned)} milestones, {issues} open quality issues"
    part = employee_scorecard(s, emp)["parts"][0]
    return f"{part['actual']} overdue tasks"


@table("employees", "employee", [
    col("name", "Name", "ref"), col("role", "Role"), col("department", "Department"), col("score", "Score", "score"),
    col("headline", "This period"), col("status", "Status", "status"), col("code", "Code", default=False),
    col("joined", "Joined", "date", False)])
def employee_row(s, e: Employee) -> dict:
    return {"name": ref("employee", e), "role": e.role_title, "department": s.one(Department, e.department_id).name,
            "score": score_cell(employee_scorecard(s, e)["score"], 80, 60), "headline": employee_headline(s, e),
            "status": status(e.status), "code": e.code, "joined": e.joined_on}


@table("milestones", "milestone", [
    col("tower", "Tower", "ref"), col("stage", "Stage"), col("planned", "Planned", "date"), col("actual", "Actual", "date"),
    col("slip", "Slip", "days"), col("contractor", "Contractor", "ref"), col("blocked", "Demands blocked", "money"),
    col("state", "State", "status", False), col("percent", "Complete", "percent", False),
    col("cause", "Delay cause", default=False), col("owner", "Owner", "ref", False)])
def milestone_row(s, m: ConstructionMilestone) -> dict:
    tower = s.one(Tower, m.tower_id)
    state = "done" if m.actual_date else "delayed" if m.id in s.delayed else "scheduled"
    return {"tower": ref("tower", tower, tower_label(s, tower)), "stage": STAGE_LABELS[m.type], "planned": m.planned_date,
            "actual": m.actual_date, "slip": s.slip(m) if m.actual_date or m.id in s.delayed else None,
            "contractor": ref("contractor", s.one(Contractor, m.contractor_id)),
            "blocked": sum(num(d.amount) for d in s.blocked(m)) if m.id in s.delayed else None,
            "state": status(state), "percent": num(m.percent_complete), "cause": m.delay_cause,
            "owner": ref("employee", s.one(Employee, m.owner_employee_id))}


def partner_stats(s, partner: ChannelPartner) -> dict:
    bookings = [b for b in s.kids(Booking, "channel_partner_id", partner.id) if b.status != "cancelled"]
    pending = [c for c in s.kids(CpCommission, "channel_partner_id", partner.id) if c.paid_on is None]
    return {"leads": len(s.kids(Lead, "channel_partner_id", partner.id)), "bookings": bookings, "pending": pending,
            "value": sum(num(b.agreement_value) for b in bookings),
            "pending_amount": sum(num(c.amount) for c in pending),
            "pending_days": max(((s.today - c.due_on).days for c in pending), default=0)}


@table("partners", "partner", [
    col("firm", "Channel partner", "ref"), col("city", "City"), col("leads", "Leads", "number"),
    col("bookings", "Bookings", "number"), col("value", "Booking value", "money"),
    col("pending", "Commission pending", "money"), col("pending_days", "Pending for", "days"),
    col("contact", "Contact", default=False)])
def partner_row(s, p: ChannelPartner) -> dict:
    stats = partner_stats(s, p)
    return {"firm": ref("partner", p), "city": p.city, "leads": stats["leads"], "bookings": len(stats["bookings"]),
            "value": stats["value"], "pending": stats["pending_amount"],
            "pending_days": max(stats["pending_days"], 0) or None, "contact": p.contact_name}


@table("commissions", "booking", [
    col("partner", "Channel partner", "ref"), col("customer", "Customer", "ref"), col("amount", "Commission", "money"),
    col("due_on", "Due on", "date"), col("days", "Days pending", "days"), col("status", "Status", "status")],
    target=lambda c: c.booking_id)
def commission_row(s, c: CpCommission) -> dict:
    booking = s.one(Booking, c.booking_id)
    late = (s.today - c.due_on).days if c.paid_on is None else None
    return {"partner": ref("partner", s.one(ChannelPartner, c.channel_partner_id)),
            "customer": ref("customer", s.one(Customer, booking.customer_id)), "amount": num(c.amount),
            "due_on": c.due_on, "days": late if late and late > 0 else None,
            "status": status("paid") if c.paid_on else status("overdue" if late > 0 else "raised", label="Pending")}


@table("visits", "lead", [
    col("lead", "Lead", "ref"), col("project", "Project"), col("employee", "Sales manager", "ref"),
    col("at", "When", "datetime"), col("status", "Status", "status"), col("feedback", "Feedback", default=False)],
    target=lambda v: v.lead_id)
def visit_row(s, v) -> dict:
    return {"lead": ref("lead", s.one(Lead, v.lead_id)), "project": s.one(Project, v.project_id).name,
            "employee": ref("employee", s.one(Employee, v.employee_id)), "at": v.scheduled_at,
            "status": status(v.status), "feedback": v.feedback}


@table("interactions", "customer", [
    col("customer", "Buyer", "ref"), col("at", "When", "datetime"), col("direction", "Direction"),
    col("channel", "Channel"), col("summary", "Summary"), col("state", "Reply", "status"),
    col("employee", "RM", "ref", False)], target=lambda i: i.customer_id)
def interaction_row(s, i) -> dict:
    waiting = i.direction == "inbound" and i.needs_reply and i.replied_at is None
    return {"customer": ref("customer", s.one(Customer, i.customer_id)), "at": i.occurred_at,
            "direction": "From buyer" if i.direction == "inbound" else "From us", "channel": nice(i.channel),
            "summary": i.summary, "employee": ref("employee", s.one(Employee, i.employee_id)),
            "state": status("waiting", "risk", "Waiting for reply") if waiting else None}


@table("tickets", "customer", [
    col("customer", "Buyer", "ref"), col("unit", "Unit", "ref"), col("category", "Category"),
    col("description", "Issue"), col("raised_on", "Raised", "date"), col("status", "Status", "status"),
    col("resolved_on", "Resolved", "date", False)], target=lambda t: t.customer_id)
def ticket_row(s, t) -> dict:
    return {"customer": ref("customer", s.one(Customer, t.customer_id)), "unit": unit_ref(s, s.one(Unit, t.unit_id)),
            "category": nice(t.category), "description": t.description, "raised_on": t.raised_on,
            "status": status(t.status), "resolved_on": t.resolved_on}


@table("tasks", None, [
    col("title", "Task"), col("owner", "Owner", "ref"), col("priority", "Priority", "status"),
    col("due_on", "Due", "date"), col("status", "Status", "status")])
def task_row(s, t) -> dict:
    late = t.status == "open" and t.due_on < s.today
    return {"title": t.title, "owner": ref("employee", s.one(Employee, t.owner_employee_id)),
            "priority": status(t.priority), "due_on": t.due_on,
            "status": status("overdue") if late else status(t.status, "watch" if t.status == "open" else None)}


@table("quality", None, [
    col("tower", "Tower", "ref"), col("category", "Issue"), col("raised_on", "Raised", "date"),
    col("status", "Status", "status"), col("contractor", "Contractor", "ref"), col("owner", "Site engineer", "ref")])
def quality_row(s, q: QualityIssue) -> dict:
    tower = s.one(Tower, q.tower_id)
    return {"tower": ref("tower", tower, tower_label(s, tower)), "category": q.category, "raised_on": q.raised_on,
            "status": status(q.status, None if q.status == "open" else "good"),
            "contractor": ref("contractor", s.one(Contractor, q.contractor_id)),
            "owner": ref("employee", s.one(Employee, q.owner_employee_id))}


def contractor_stats(s, c: Contractor) -> dict:
    stages = s.kids(ConstructionMilestone, "contractor_id", c.id)
    judged = [m for m in stages if m.actual_date or m.id in s.delayed]
    return {"stages": stages, "open_issues": sum(q.status == "open" for q in s.kids(QualityIssue, "contractor_id", c.id)),
            "on_time_pct": pct(sum(s.slip(m) <= ON_TIME_GRACE_DAYS for m in judged), len(judged)) if judged else None}


@table("contractors", "contractor", [
    col("name", "Contractor", "ref"), col("trade", "Trade"), col("milestones", "Milestones", "number"),
    col("on_time_pct", "On time", "percent"), col("open_issues", "Open quality issues", "number")])
def contractor_row(s, c: Contractor) -> dict:
    stats = contractor_stats(s, c)
    return {"name": ref("contractor", c), "trade": c.trade, "milestones": len(stats["stages"]),
            "on_time_pct": stats["on_time_pct"], "open_issues": stats["open_issues"]}


@table("budgets", None, [
    col("project", "Project", "ref"), col("category", "Category"), col("budget", "Budget to date", "money"),
    col("actual", "Actual", "money"), col("variance", "Variance", "percent")])
def budget_row(s, b) -> dict:
    return {"project": ref("project", s.one(Project, b.project_id)), "category": b.category,
            "budget": num(b.budget_amount), "actual": num(b.actual_amount),
            "variance": round(100 * (num(b.actual_amount) - num(b.budget_amount)) / num(b.budget_amount), 1)}


@table("safety", None, [
    col("project", "Project", "ref"), col("occurred_on", "Date", "date"), col("severity", "Severity", "status"),
    col("description", "What happened")])
def safety_row(s, i) -> dict:
    return {"project": ref("project", s.one(Project, i.project_id)), "occurred_on": i.occurred_on,
            "severity": status(i.severity, "watch" if i.severity == "minor" else None), "description": i.description}


@table("towers", "tower", [
    col("tower", "Tower", "ref"), col("floors", "Floors", "number"), col("units", "Units", "number"),
    col("sold", "Sold", "number"), col("stage", "Current stage"), col("slip", "Slip", "days")])
def tower_row(s, t: Tower) -> dict:
    units = s.kids(Unit, "tower_id", t.id)
    current = current_stage(s, t)
    return {"tower": ref("tower", t, tower_label(s, t)), "floors": t.floors, "units": len(units),
            "sold": sum(u.id in s.unit_booking for u in units), "stage": STAGE_LABELS[current.type] if current else "Complete",
            "slip": s.slip(current) if current and current.id in s.delayed else None}


def current_stage(s, tower: Tower):
    """The first milestone that is not finished yet."""
    todo = [m for m in s.kids(ConstructionMilestone, "tower_id", tower.id) if m.actual_date is None]
    return min(todo, key=lambda m: m.seq, default=None)


@table("activities", None, [
    col("at", "When", "datetime"), col("kind", "Type"), col("summary", "Summary"), col("employee", "By", "ref")])
def activity_row(s, a) -> dict:
    return {"at": a.occurred_at, "kind": nice(a.type), "summary": a.summary,
            "employee": ref("employee", s.one(Employee, a.employee_id))}


def risk_card(s, r) -> dict:
    """A risk as the Risks page and the Overview attention list show it."""
    return {"id": str(r.id), "type": "risk", "rule_id": r.rule_id, "category": r.category, "severity": r.severity,
            "title": r.title, "facts": r.facts_json["items"], "impact": r.facts_json["impact"],
            "refs": r.entity_refs_json, "suggested_action": r.suggested_action, "status": r.status,
            "owner": ref("employee", s.one(Employee, r.owner_employee_id)), "detected_at": r.detected_at}


@table("risks", None, [
    col("title", "Risk"), col("category", "Category"), col("severity", "Severity", "status"),
    col("status", "Status", "status"), col("owner", "Owner", "ref")])
def risk_row(s, r) -> dict:
    return {"title": r.title, "category": r.category, "severity": status(r.severity),
            "status": status(r.status, "good" if r.status == "resolved" else None),
            "owner": ref("employee", s.one(Employee, r.owner_employee_id))}
