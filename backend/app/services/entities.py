"""Quick view (hover card) and drawer content for every entity type.

Every entity uses the same shape, so the admin learns the layout once (Section 7.2):
title, subtitle, status, 8 to 12 facts, one attention line, last activity. The drawer adds tabs.
A tab is a list of blocks: facts, table, timeline, score or chart.
"""
from collections import Counter

from app.db.models import (
    Booking, ChannelPartner, ConstructionMilestone, Contractor, CpCommission, Customer, CustomerInteraction,
    Demand, Department, Employee, EmployeeTarget, InteriorProject, Lead, LeadActivity, PaymentPlan,
    PlanMilestone, Project, QualityIssue, Receipt, ServiceTicket, SiteVisit, Task, Tower, Unit,
)
from app.scoring.scores import (
    ON_TIME_GRACE_DAYS, SALES_ROLES, SITE_ROLES, customer_health, employee_scorecard, project_stats, rm_stats,
    sales_stats, score_lead,
)
from app.services.common import chart, fact, inr, nice, pct, ref, status
from app.services.snapshot import num, to_date
from app.services.tables import (
    STAGE_LABELS, block, contractor_stats, current_stage, employee_headline, partner_stats, tower_label,
)

TONE_OF_BAND = {"good": "good", "watch": "watch", "risk": "risk"}


def view(kind, obj, title, subtitle, state, facts, attention=None, last=None, tabs=None) -> dict:
    out = {"type": kind, "id": str(obj.id), "title": title, "subtitle": subtitle, "status": state,
           "facts": [f for f in facts if f["value"] is not None], "attention": attention, "last_activity": last}
    if tabs is not None:
        out["tabs"] = [{"key": key, "label": label, "blocks": blocks} for key, label, blocks in tabs]
    return out


def facts_block(items, title=None) -> dict:
    return {"kind": "facts", "title": title, "items": [f for f in items if f["value"] is not None]}


def score_block(result: dict, title: str, formula: str) -> dict:
    return {"kind": "score", "title": title, "score": result["score"], "parts": result["parts"], "formula": formula}


def timeline(items) -> dict:
    """items: (when, title, text, tone). Newest first."""
    rows = [{"at": at, "title": title, "text": text, "tone": tone} for at, title, text, tone in items]
    return {"kind": "timeline", "items": sorted(rows, key=lambda r: str(r["at"]), reverse=True)}


def schedule(s, booking) -> dict:
    return block(s, "demands", sorted(s.demands(booking), key=lambda d: s.one(PlanMilestone, d.plan_milestone_id).seq),
                 f"Payment schedule, unit {s.unit(booking).unit_no}")


# ---------- customer ----------
def customer(s, c: Customer, quick: bool) -> dict:
    bookings = s.bookings_of(c.id)
    health = customer_health(s, c)
    value = sum(num(b.agreement_value) for b in bookings)
    overdue, days = s.customer_overdue(c.id)
    queries = s.open_queries(c.id)
    tickets = s.kids(ServiceTicket, "customer_id", c.id)
    open_tickets = [t for t in tickets if t.status != "resolved"]
    talks = sorted(s.kids(CustomerInteraction, "customer_id", c.id), key=lambda i: i.occurred_at)
    rm = s.one(Employee, c.rm_employee_id)
    demands = [d for b in bookings for d in s.demands(b)]
    upcoming = min((d.due_on for d in demands if d.due_on and d.due_on >= s.today and s.left(d) > 0), default=None)
    blocked = [d for d in demands if d.construction_milestone_id in s.delayed and d.status == "not_raised"]

    attention = None
    if overdue:
        attention = f"{inr(overdue)} overdue for {days} days"
    elif queries:
        oldest = max((s.today - to_date(q.occurred_at)).days for q in queries)
        attention = f"{len(queries)} queries waiting for a reply, oldest {oldest} days"
    elif blocked:
        attention = f"Next demand of {inr(sum(num(d.amount) for d in blocked))} is blocked by a construction delay"
    last = talks[-1] if talks else None
    facts = [
        fact("Units", ", ".join(s.unit(b).unit_no for b in bookings) or "None (cancelled)"),
        fact("Agreement value", value, "money"), fact("Paid", pct(sum(s.booking_paid(b) for b in bookings), value), "percent"),
        fact("Next due", upcoming, "date"), fact("Overdue", overdue, "money"),
        fact("Last contact from us", s.last_contact(c.id), "date"), fact("Open complaints", len(open_tickets), "number"),
        fact("Health", health["score"], "score"), fact("RM", rm.name, ref=ref("employee", rm)),
    ]
    place = f"{c.city}, {c.country}" if c.city else c.country
    out = view("customer", c, c.name, f"{'NRI' if c.is_nri else nice(c.type)} buyer, {place}",
               status(health["band"], TONE_OF_BAND[health["band"]], f"Health {health['score']}"), facts, attention,
               {"at": last.occurred_at, "text": f"{nice(last.channel)}: {last.summary}"} if last else None,
               None if quick else [])
    if quick:
        return out
    # Phone and email are shown in full only here, inside the pinned drawer.
    profile = facts_block([fact("Phone", c.phone), fact("Email", c.email), fact("Type", nice(c.type)),
                           fact("Country", c.country), fact("City", c.city),
                           fact("Relationship manager", rm.name, ref=ref("employee", rm))])
    units = [block(s, "bookings", bookings, "Units")] + [schedule(s, b) for b in bookings]
    talk_items = [(i.occurred_at, f"{'Buyer' if i.direction == 'inbound' else 'Us'}, {i.channel}", i.summary,
                   "risk" if i in queries else "neutral") for i in talks]
    out["tabs"] = [{"key": k, "label": label, "blocks": blocks} for k, label, blocks in [
        ("profile", "Profile", [profile, facts_block(facts, "At a glance")]),
        ("payments", "Units and payments", units),
        ("interactions", "Interactions", [timeline(talk_items)]),
        ("complaints", "Complaints", [block(s, "tickets", tickets, "Service tickets and complaints")]),
        ("health", "Health breakdown", [score_block(health, "Buyer health", "Health = payments 40 + engagement 25 + complaints 20 + loan 15")]),
    ]]
    return out


# ---------- unit ----------
def unit(s, u: Unit, quick: bool) -> dict:
    project, tower = s.one(Project, u.project_id), s.one(Tower, u.tower_id)
    booking = s.unit_booking.get(u.id)
    buyer = s.one(Customer, booking.customer_id) if booking else None
    overdue, days = s.booking_overdue(booking) if booking else (0.0, 0)
    facts = [
        fact("Type", u.config), fact("Carpet area", num(u.carpet_sft) or None, "sqft"),
        fact("Super built-up area", num(u.sba_sft) or None, "sqft"), fact("Plot area", num(u.plot_sqyd) or None, "sqyd"),
        fact("Facing", u.facing), fact("Floor", u.floor, "number"), fact("Price", s.price(u), "money"),
        fact("Rate", num(u.base_price_psf), "money"), fact("Days unsold", s.days_unsold(u), "days"),
        fact("Buyer", buyer.name if buyer else None, ref=ref("customer", buyer)),
        fact("Paid", pct(s.booking_paid(booking), num(booking.agreement_value)) if booking else None, "percent"),
        fact("Overdue", overdue or None, "money"),
    ]
    where = f"{project.name}, {tower.name}" if tower else project.name
    out = view("unit", u, f"Unit {u.unit_no}", where, status(u.status, "neutral" if u.status == "available" else None),
               facts, f"{inr(overdue)} overdue for {days} days" if overdue else None, None, None if quick else [])
    if quick:
        return out
    links = facts_block([fact("Project", project.name, ref=ref("project", project)),
                         fact("Tower", tower.name if tower else None, ref=ref("tower", tower, tower_label(s, tower)) if tower else None),
                         fact("Preferred location charge", num(u.plc_amount), "money"),
                         fact("Floor rise charge", num(u.floor_rise_amount), "money"), fact("Listed on", u.listed_on, "date")])
    tickets = s.kids(ServiceTicket, "unit_id", u.id)
    out["tabs"] = [{"key": "summary", "label": "Summary", "blocks": [facts_block(facts), links]},
                   {"key": "payments", "label": "Payments", "blocks": [schedule(s, booking)] if booking else []},
                   {"key": "service", "label": "Service", "blocks": [block(s, "tickets", tickets, "Service tickets")]}]
    return out


# ---------- tower and project ----------
def tower(s, t: Tower, quick: bool) -> dict:
    project = s.one(Project, t.project_id)
    units = s.kids(Unit, "tower_id", t.id)
    stages = sorted(s.kids(ConstructionMilestone, "tower_id", t.id), key=lambda m: m.seq)
    now = current_stage(s, t)
    late = [m for m in stages if m.id in s.delayed]
    blocked = sum(num(d.amount) for m in late for d in s.blocked(m))
    issues = s.kids(QualityIssue, "tower_id", t.id)
    facts = [
        fact("Project", project.name, ref=ref("project", project)), fact("Floors", t.floors, "number"),
        fact("Units", len(units), "number"), fact("Sold", sum(u.id in s.unit_booking for u in units), "number"),
        fact("Construction", round(sum(num(m.percent_complete) for m in stages) / len(stages), 1), "percent"),
        fact("Current stage", STAGE_LABELS[now.type] if now else "Complete"),
        fact("Slip", s.slip(late[0]) if late else 0, "days"), fact("Demands blocked", blocked or None, "money"),
        fact("Open quality issues", sum(q.status == "open" for q in issues), "number"),
    ]
    attention = f"{STAGE_LABELS[late[0].type]} is {s.slip(late[0])} days late and blocks {inr(blocked)}" if late else None
    out = view("tower", t, tower_label(s, t), f"{t.floors} floors, {len(units)} units",
               status("delayed") if late else status("on_time", label="On schedule"), facts, attention, None,
               None if quick else [])
    if not quick:
        out["tabs"] = [{"key": "summary", "label": "Summary", "blocks": [facts_block(facts)]},
                       {"key": "milestones", "label": "Milestones", "blocks": [block(s, "milestones", stages, "Milestones")]},
                       {"key": "units", "label": "Units", "blocks": [block(s, "units", units, "Units")]},
                       {"key": "quality", "label": "Quality", "blocks": [block(s, "quality", issues, "Quality issues")]}]
    return out


def project(s, p: Project, quick: bool) -> dict:
    stats = project_stats(s, p)
    towers = s.kids(Tower, "project_id", p.id)
    bookings = [b for b in s.active_bookings if s.unit(b).project_id == p.id]
    demands = [d for b in bookings for d in s.demands(b)]
    overdue = sum(s.left(d) for d in demands if s.late(d))
    facts = [
        fact("Type", nice(p.type)), fact("Locality", p.locality), fact("RERA no. (demo)", p.rera_no),
        fact("Launched", p.launch_date, "date"), fact("Expected possession", p.expected_possession, "date"),
        fact("Sold", f"{stats['sold']} of {stats['units']} ({stats['sold_pct']}%)"),
        fact("Construction", stats["construction_pct"], "percent"),
        fact("Collection efficiency", stats["collection_efficiency"], "percent"), fact("Overdue", overdue, "money"),
        fact("Health", stats["health"]["score"], "score"),
    ]
    late = stats["slip_days"] and any(m.id in s.delayed for t in towers for m in s.kids(ConstructionMilestone, "tower_id", t.id))
    out = view("project", p, p.name, f"{nice(p.type)}, {p.locality}", status(p.status, "neutral"), facts,
               f"A construction stage is {stats['slip_days']} days late" if late else None, None, None if quick else [])
    if quick:
        return out
    stages = [m for t in towers for m in s.kids(ConstructionMilestone, "tower_id", t.id)]
    team_ids = {b.employee_id for b in bookings} | {m.owner_employee_id for m in stages}
    team = [e for e in s.all(Employee) if e.id in team_ids]
    out["tabs"] = [
        {"key": "summary", "label": "Summary", "blocks": [facts_block(facts), score_block(stats["health"], "Project health", "Health = schedule 25 + cost 15 + sales velocity 25 + collections 25 + open high risks 10")]},
        {"key": "towers", "label": "Towers", "blocks": [block(s, "towers", towers, "Towers")]},
        {"key": "sales", "label": "Sales", "blocks": [block(s, "bookings", sorted(bookings, key=lambda b: b.booked_on, reverse=True)[:50], "Latest 50 bookings")]},
        {"key": "collections", "label": "Collections", "blocks": [block(s, "demands", [d for d in demands if s.late(d)], "Overdue demands")]},
        {"key": "construction", "label": "Construction", "blocks": [block(s, "milestones", sorted(stages, key=lambda m: m.planned_date), "Milestones")]},
        {"key": "team", "label": "Team", "blocks": [block(s, "employees", team, "People working on this project")]},
    ]
    return out


# ---------- employee ----------
def employee(s, e: Employee, quick: bool) -> dict:
    card = employee_scorecard(s, e)
    department = s.one(Department, e.department_id)
    facts = [fact("Role", e.role_title), fact("Department", department.name), fact("Score", card["score"], "score")]
    attention, work = None, []
    if e.role_title in SALES_ROLES:
        me, team = sales_stats(s)["people"][e.id], sales_stats(s)["team_conversion"]
        facts += [fact("Bookings", len(me["bookings"]), "number"), fact("Site visits done", len(me["visits"]), "number"),
                  fact("Conversion", round(me["conversion"], 1), "percent"), fact("Team conversion", round(team, 1), "percent"),
                  fact("Stalled deals", len(me["idle"]), "number"), fact("Pipeline at risk", me["idle_value"], "money")]
        if me["idle"]:
            attention = f"{len(me['idle'])} negotiations idle 14+ days, {inr(me['idle_value'])} at risk"
        work = [block(s, "leads", me["idle"], "Stalled negotiations"),
                block(s, "bookings", sorted(me["bookings"], key=lambda b: b.booked_on, reverse=True)[:30], "Latest bookings")]
    elif e.role_title == "Relationship Manager":
        stats = rm_stats(s)
        me = stats["people"].get(e.id, {"buyers": [], "open_queries": 0, "efficiency": None, "response_hours": 0})
        facts += [fact("Buyers handled", len(me["buyers"]), "number"), fact("Team average", round(stats["average_buyers"]), "number"),
                  fact("Open queries", me["open_queries"], "number"), fact("Average reply time (hours)", me["response_hours"], "number"),
                  fact("Collection efficiency", me["efficiency"], "percent")]
        if len(me["buyers"]) > 1.5 * stats["average_buyers"]:
            attention = f"Handles {len(me['buyers'])} buyers; the team average is {round(stats['average_buyers'])}"
        waiting = [q for c in me["buyers"] for q in s.open_queries(c.id)]
        work = [block(s, "interactions", waiting, "Queries waiting for a reply"), block(s, "customers", me["buyers"], "Buyers")]
    elif e.role_title in SITE_ROLES:
        owned = s.kids(ConstructionMilestone, "owner_employee_id", e.id)
        issues = [q for q in s.kids(QualityIssue, "owner_employee_id", e.id)]
        done = [m for m in owned if m.actual_date]
        facts += [fact("Milestones owned", len(owned), "number"),
                  fact("On time", pct(sum(s.slip(m) <= ON_TIME_GRACE_DAYS for m in done), len(done)) if done else None, "percent"),
                  fact("Open quality issues", sum(q.status == "open" for q in issues), "number")]
        late = [m for m in owned if m.id in s.delayed]
        if late:
            attention = f"{STAGE_LABELS[late[0].type]} is {s.slip(late[0])} days late"
        work = [block(s, "milestones", owned, "Milestones owned"), block(s, "quality", issues, "Quality issues")]
    tasks = s.kids(Task, "owner_employee_id", e.id)
    manager = s.one(Employee, e.manager_id)
    reports = s.kids(Employee, "manager_id", e.id)
    facts.append(fact("Overdue tasks", sum(t.status == "open" and t.due_on < s.today for t in tasks), "number"))
    facts.append(fact("Reports to", manager.name if manager else None, ref=ref("employee", manager)))
    facts.append(fact("Team size", len(reports) or None, "number"))
    tone = "risk" if card["needs_attention"] else "good" if card["score"] >= 80 else "watch"
    out = view("employee", e, e.name, f"{e.role_title}, {department.name}", status(e.status, tone, f"Score {card['score']}"),
               facts, attention, {"at": None, "text": employee_headline(s, e)}, None if quick else [])
    if quick:
        return out
    # Who this person works with: their manager, their team, and the colleagues they share buyers with.
    shared, shared_title = Counter(), None
    if e.role_title in SALES_ROLES:
        shared_title = "Relationship managers who look after this person's buyers"
        shared = Counter(s.one(Customer, b.customer_id).rm_employee_id for b in s.kids(Booking, "employee_id", e.id) if b.status != "cancelled")
    elif e.role_title == "Relationship Manager":
        shared_title = "Sales managers whose buyers this person looks after"
        shared = Counter(b.employee_id for c in s.active_customers if c.rm_employee_id == e.id for b in s.bookings_of(c.id))
    peers = [p for p in s.kids(Employee, "manager_id", e.manager_id) if p.id != e.id and p.role_title == e.role_title] if manager else []
    connections = [facts_block([fact("Reports to", manager.name if manager else "Nobody (team head)", ref=ref("employee", manager)),
                                fact("Department", department.name), fact("People reporting to them", len(reports), "number"),
                                fact("Colleagues in the same role", len(peers), "number")])]
    if reports:
        connections.append(block(s, "employees", reports, "Their team"))
    if shared:
        connections.append(block(s, "employees", [s.one(Employee, i) for i, _ in shared.most_common(6)], shared_title))
    if peers:
        connections.append(block(s, "employees", peers, "Colleagues in the same role"))
    profile = facts_block([fact("Employee code", e.code), fact("Email", e.email), fact("Phone", e.phone),
                           fact("Joined", e.joined_on, "date"), fact("Status", nice(e.status)),
                           fact("Reports to", manager.name if manager else None, ref=ref("employee", manager))])
    activity = [(a.occurred_at, nice(a.type), a.summary, "neutral")
                for a in sorted(s.kids(LeadActivity, "employee_id", e.id), key=lambda a: a.occurred_at)[-25:]]
    activity += [(i.occurred_at, nice(i.channel), i.summary, "neutral")
                 for i in sorted(s.kids(CustomerInteraction, "employee_id", e.id), key=lambda i: i.occurred_at)[-25:]
                 if i.direction == "outbound"]
    out["tabs"] = [
        {"key": "profile", "label": "Profile", "blocks": [profile, facts_block(facts, "At a glance")]},
        {"key": "connections", "label": "Connections", "blocks": connections},
        {"key": "scorecard", "label": "Scorecard", "blocks": [{"kind": "scorecard", **card}]},
        {"key": "work", "label": "Work", "blocks": work + [block(s, "tasks", tasks, "Tasks")]},
        {"key": "activity", "label": "Activity", "blocks": [timeline(activity)]},
        {"key": "trend", "label": "Trend", "blocks": _trend(s, e)},
    ]
    return out


def _trend(s, e: Employee) -> list:
    """Bookings per quarter against target, for sales people (the only role with quarterly targets)."""
    targets = sorted((t for t in s.kids(EmployeeTarget, "employee_id", e.id) if t.metric == "bookings"),
                     key=lambda t: t.period_start)
    if not targets:
        return []
    bookings = s.kids(Booking, "employee_id", e.id)
    return [{"kind": "chart", "chart": chart(
        "Bookings per quarter vs target", [t.period_start.strftime("%b %y") for t in targets],
        [{"name": "Bookings", "data": [sum(t.period_start <= b.booked_on <= t.period_end for b in bookings) for t in targets]},
         {"name": "Target", "data": [num(t.target_value) for t in targets]}])}]


# ---------- lead and booking ----------
def lead(s, x: Lead, quick: bool) -> dict:
    result = score_lead(s, x)
    owner = s.one(Employee, x.owner_employee_id)
    acts = sorted(s.kids(LeadActivity, "lead_id", x.id), key=lambda a: a.occurred_at)
    idle = s.idle_days(x)
    best = max(result["parts"], key=lambda p: p["points"] / p["weight"])
    worst = min(result["parts"], key=lambda p: p["points"] / p["weight"])
    facts = [
        fact("Budget", num(x.budget_max), "money"), fact("Wants", x.preferred_config),
        fact("Project", s.one(Project, x.preferred_project_id).name, ref=ref("project", s.one(Project, x.preferred_project_id))),
        fact("Source", x.source), fact("Owner", owner.name, ref=ref("employee", owner)), fact("Stage", nice(x.stage)),
        fact("Days since activity", idle, "days"), fact("Lead score", result["score"], "score"),
        fact("Strongest", best["label"]), fact("Weakest", worst["label"]), fact("Lost reason", x.lost_reason),
    ]
    stuck = x.stage == "negotiation" and idle >= 14
    out = view("lead", x, x.name, f"Lead, {x.country}", status(x.stage), facts,
               f"No activity for {idle} days" if stuck else None,
               {"at": acts[-1].occurred_at, "text": f"{nice(acts[-1].type)}: {acts[-1].summary}"} if acts else None,
               None if quick else [])
    if not quick:
        out["tabs"] = [
            {"key": "profile", "label": "Profile", "blocks": [facts_block([fact("Phone", x.phone), fact("Email", x.email), fact("Created", to_date(x.created_at), "date")]), facts_block(facts, "At a glance")]},
            {"key": "activity", "label": "Activity", "blocks": [timeline([(a.occurred_at, nice(a.type), a.summary, "neutral") for a in acts])]},
            {"key": "visits", "label": "Site visits", "blocks": [block(s, "visits", s.kids(SiteVisit, "lead_id", x.id), "Site visits")]},
            {"key": "score", "label": "Lead score", "blocks": [score_block(result, "Lead score", "Score = budget fit 35 + source quality 25 + engagement 25 + recent contact 15")]},
        ]
    return out


def booking(s, b: Booking, quick: bool) -> dict:
    u, buyer = s.unit(b), s.one(Customer, b.customer_id)
    rm, partner = s.one(Employee, buyer.rm_employee_id), s.one(ChannelPartner, b.channel_partner_id)
    overdue, days = s.booking_overdue(b)
    loan = s.loan(b)
    facts = [
        fact("Buyer", buyer.name, ref=ref("customer", buyer)), fact("Unit", u.unit_no, ref=ref("unit", u, u.unit_no)),
        fact("Agreement value", num(b.agreement_value), "money"), fact("Payment plan", s.one(PaymentPlan, b.payment_plan_id).name),
        fact("Paid", pct(s.booking_paid(b), num(b.agreement_value)), "percent"), fact("Overdue", overdue or None, "money"),
        fact("Booked on", b.booked_on, "date"), fact("RM", rm.name, ref=ref("employee", rm)),
        fact("Sales manager", s.one(Employee, b.employee_id).name, ref=ref("employee", s.one(Employee, b.employee_id))),
        fact("Channel partner", partner.firm_name if partner else "Direct", ref=ref("partner", partner)),
        fact("Home loan", f"{loan.bank}, {nice(loan.status)}" if loan else "No loan"), fact("Cancel reason", b.cancel_reason),
    ]
    out = view("booking", b, f"Booking, unit {u.unit_no}", buyer.name, status(b.status), facts,
               f"{inr(overdue)} overdue for {days} days" if overdue else None, None, None if quick else [])
    if not quick:
        commissions = s.kids(CpCommission, "booking_id", b.id)
        receipts = [r for d in s.demands(b) for r in s.kids(Receipt, "demand_id", d.id)]
        out["tabs"] = [{"key": "summary", "label": "Summary", "blocks": [facts_block(facts)]},
                       {"key": "schedule", "label": "Payment schedule", "blocks": [schedule(s, b), block(s, "receipts", receipts, "Receipts")]},
                       {"key": "commission", "label": "Commission", "blocks": [block(s, "commissions", commissions, "Channel partner commission")]}]
    return out


# ---------- partner, demand, milestone, contractor ----------
def partner(s, p: ChannelPartner, quick: bool) -> dict:
    stats = partner_stats(s, p)
    late = [c for c in stats["pending"] if (s.today - c.due_on).days >= 45]
    facts = [
        fact("City", p.city), fact("Contact", p.contact_name), fact("Leads", stats["leads"], "number"),
        fact("Bookings", len(stats["bookings"]), "number"), fact("Booking value", stats["value"], "money"),
        fact("Commission rate", num(p.commission_pct), "percent"), fact("Commission pending", stats["pending_amount"], "money"),
        fact("Pending for", max(stats["pending_days"], 0), "days"),
    ]
    out = view("partner", p, p.firm_name, f"Channel partner, {p.city}", status(p.status), facts,
               f"{len(late)} commissions pending 45+ days, {inr(sum(num(c.amount) for c in late))}" if late else None,
               None, None if quick else [])
    if not quick:
        out["tabs"] = [{"key": "summary", "label": "Summary", "blocks": [facts_block(facts + [fact("Phone", p.phone)])]},
                       {"key": "bookings", "label": "Bookings", "blocks": [block(s, "bookings", stats["bookings"], "Bookings")]},
                       {"key": "commissions", "label": "Commissions", "blocks": [block(s, "commissions", s.kids(CpCommission, "channel_partner_id", p.id), "Commissions")]}]
    return out


def demand(s, d: Demand, quick: bool) -> dict:
    b = s.one(Booking, d.booking_id)
    buyer, u, loan = s.one(Customer, b.customer_id), s.unit(b), s.loan(b)
    step = s.one(PlanMilestone, d.plan_milestone_id)
    stage = s.one(ConstructionMilestone, d.construction_milestone_id)
    is_blocked = d.status == "not_raised" and stage is not None and stage.id in s.delayed
    facts = [
        fact("Buyer", buyer.name, ref=ref("customer", buyer)), fact("Unit", u.unit_no, ref=ref("unit", u, u.unit_no)),
        fact("Milestone", step.name), fact("Amount", num(d.amount), "money"), fact("Unpaid", s.left(d) or None, "money"),
        fact("Raised on", d.raised_on, "date"), fact("Due date", d.due_on, "date"),
        fact("Days overdue", s.late(d) or None, "days"), fact("Bank", loan.bank if loan else "No loan"),
        fact("Loan status", nice(loan.status) if loan else None), fact("Reminders sent", d.reminders_sent, "number"),
        fact("Waiting for", STAGE_LABELS[stage.type] if is_blocked else None, ref=ref("milestone", stage, STAGE_LABELS[stage.type]) if is_blocked else None),
    ]
    if is_blocked:
        state, attention = status("blocked", "risk", "Blocked by delay"), f"Cannot be raised: {STAGE_LABELS[stage.type]} is {s.slip(stage)} days late"
    elif s.late(d):
        state, attention = status("overdue"), f"{inr(s.left(d))} overdue for {s.late(d)} days"
    else:
        state, attention = status("paid" if d.due_on and s.left(d) == 0 else d.status), None
    out = view("demand", d, f"{step.name}, unit {u.unit_no}", buyer.name, state, facts, attention, None, None if quick else [])
    if not quick:
        out["tabs"] = [{"key": "summary", "label": "Summary", "blocks": [facts_block(facts), block(s, "receipts", s.kids(Receipt, "demand_id", d.id), "Receipts")]}]
    return out


def milestone(s, m: ConstructionMilestone, quick: bool) -> dict:
    t = s.one(Tower, m.tower_id)
    contractor_, owner = s.one(Contractor, m.contractor_id), s.one(Employee, m.owner_employee_id)
    blocked = s.blocked(m) if m.id in s.delayed else []
    amount = sum(num(d.amount) for d in blocked)
    facts = [
        fact("Tower", tower_label(s, t), ref=ref("tower", t, tower_label(s, t))), fact("Planned", m.planned_date, "date"),
        fact("Actual", m.actual_date, "date"), fact("Slip", s.slip(m) if m.actual_date or m.id in s.delayed else None, "days"),
        fact("Complete", num(m.percent_complete), "percent"),
        fact("Contractor", contractor_.name if contractor_ else None, ref=ref("contractor", contractor_)),
        fact("Owner", owner.name if owner else None, ref=ref("employee", owner)), fact("Cause", m.delay_cause),
        fact("Demands blocked", amount or None, "money"), fact("Bookings affected", len({d.booking_id for d in blocked}) or None, "number"),
    ]
    state = status("done") if m.actual_date else status("delayed") if m.id in s.delayed else status("scheduled", "neutral", "Upcoming")
    out = view("milestone", m, f"{STAGE_LABELS[m.type]}, {t.name}", s.one(Project, t.project_id).name, state, facts,
               f"{s.slip(m)} days late; blocks {inr(amount)} from {len({d.booking_id for d in blocked})} bookings" if blocked else None,
               None, None if quick else [])
    if not quick:
        out["tabs"] = [{"key": "summary", "label": "Summary", "blocks": [facts_block(facts)]},
                       {"key": "blocked", "label": "Blocked demands", "blocks": [block(s, "demands", blocked, "Demands waiting for this stage")]}]
    return out


def contractor(s, c: Contractor, quick: bool) -> dict:
    stats = contractor_stats(s, c)
    late = [m for m in stats["stages"] if m.id in s.delayed]
    facts = [fact("Trade", c.trade), fact("Milestones", len(stats["stages"]), "number"),
             fact("On time", stats["on_time_pct"], "percent"), fact("Open quality issues", stats["open_issues"], "number"),
             fact("Late right now", len(late), "number")]
    out = view("contractor", c, c.name, c.trade, status("delayed") if late else status("on_time", label="On schedule"), facts,
               f"{STAGE_LABELS[late[0].type]} at {tower_label(s, s.one(Tower, late[0].tower_id))} is {s.slip(late[0])} days late" if late else None,
               None, None if quick else [])
    if not quick:
        out["tabs"] = [{"key": "milestones", "label": "Milestones", "blocks": [facts_block(facts), block(s, "milestones", stats["stages"], "Milestones")]},
                       {"key": "quality", "label": "Quality", "blocks": [block(s, "quality", s.kids(QualityIssue, "contractor_id", c.id), "Quality issues")]}]
    return out


# kind -> (model, builder). The API uses this for /customers/{id}, /units/{id} and so on.
ENTITIES = {"customer": (Customer, customer), "unit": (Unit, unit), "tower": (Tower, tower), "project": (Project, project),
            "employee": (Employee, employee), "lead": (Lead, lead), "booking": (Booking, booking),
            "partner": (ChannelPartner, partner), "demand": (Demand, demand), "milestone": (ConstructionMilestone, milestone),
            "contractor": (Contractor, contractor)}


def get_entity(s, kind: str, id, quick: bool = False) -> dict | None:
    model, builder = ENTITIES[kind]
    obj = s.one(model, id)
    return builder(s, obj, quick) if obj else None
