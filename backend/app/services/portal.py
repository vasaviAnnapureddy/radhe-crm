"""The employee and customer portals: each person sees only their own records.

Two safety pieces sit here:
  * `scope()` lists exactly which records a signed-in person may open.
  * `scrub()` removes every clickable link to a record outside that list before a reply is sent.
A buyer never receives the admin's customer view (it holds health scores and risk notes).
"""
from datetime import timedelta

from app.db.models import (
    Booking, ConstructionMilestone, Customer, CustomerInteraction, Demand, Department, Employee,
    InteriorProject, Lead, PaymentPlan, PlanMilestone, Project, QualityIssue, Receipt, ServiceTicket,
    SiteVisit, Task, Tower, Unit, User,
)
from app.scoring.scores import (
    ON_TIME_GRACE_DAYS, SALES_ROLES, SITE_ROLES, employee_scorecard, rm_stats, sales_stats,
)
from app.services.common import col, fact, inr, nice, pct, ref, status
from app.services.entities import ENTITIES, _trend, facts_block, get_entity, timeline
from app.services.snapshot import num, to_date
from app.services.tables import STAGE_LABELS, block, table, tower_label

# What each kind of person may open as a hover card or drawer.
EMPLOYEE_TYPES = {"customer", "lead", "booking", "unit", "demand", "milestone", "tower"}
CUSTOMER_TYPES = {"unit", "demand"}  # never "customer": that view is the admin's


# ---------- safety ----------
def scope(s, user: User) -> set[tuple[str, str]]:
    """Every (type, id) this person may open."""
    def build():
        allowed = set()
        add = lambda kind, obj: allowed.add((kind, str(obj.id)))  # noqa: E731
        if user.role == "customer":
            for booking in s.bookings_of(user.customer_id):
                add("unit", s.unit(booking))
                for demand in s.demands(booking):
                    add("demand", demand)
        elif user.role == "employee":
            for lead in s.kids(Lead, "owner_employee_id", user.employee_id):
                add("lead", lead)
            mine = [b for b in s.kids(Booking, "employee_id", user.employee_id)]
            mine += [b for c in s.kids(Customer, "rm_employee_id", user.employee_id) for b in s.kids(Booking, "customer_id", c.id)]
            for booking in mine:
                add("booking", booking)
                add("unit", s.unit(booking))
                add("customer", s.one(Customer, booking.customer_id))
                for demand in s.demands(booking):
                    add("demand", demand)
            for stage in s.kids(ConstructionMilestone, "owner_employee_id", user.employee_id):
                add("milestone", stage)
                add("tower", s.one(Tower, stage.tower_id))
        return allowed
    return s.memo(("scope", user.id), build)


def scrub(value, allowed: set):
    """Turn every link to a record outside `allowed` into plain text, all the way down a reply."""
    if isinstance(value, list):
        return [scrub(item, allowed) for item in value]
    if not isinstance(value, dict):
        return value
    if set(value) >= {"type", "id", "label"} and value["type"] in ENTITIES:
        return value if (value["type"], value["id"]) in allowed else value["label"]
    out = {key: scrub(item, allowed) for key, item in value.items()}
    if "target_id" in out and (out.get("type"), out["target_id"]) not in allowed:
        out.pop("type", None)       # the row is no longer clickable
        out.pop("target_id", None)
    if isinstance(out.get("ref"), str):  # a fact whose link was removed
        out.pop("ref")
    return out


def portal_entity(s, user: User, kind: str, id, quick: bool) -> dict | None:
    """A hover card or drawer inside a portal. None means "not yours" (the API answers 403)."""
    types = CUSTOMER_TYPES if user.role == "customer" else EMPLOYEE_TYPES
    allowed = scope(s, user)
    if kind not in types or (kind, str(id)) not in allowed:
        return None
    view = get_entity(s, kind, id, quick)
    return scrub(view, allowed) if view else None


def kpi(label: str, value, kind: str = "number", note: str | None = None) -> dict:
    return {"label": label, "value": value, "kind": kind, "note": note}


def notice(text: str, tone: str = "risk") -> dict:
    return {"kind": "notice", "tone": tone, "text": text}


def page(title: str, subtitle: str, blocks: list, kpis: list | None = None) -> dict:
    return {"title": title, "subtitle": subtitle, "kpis": kpis or [], "blocks": [b for b in blocks if b]}


LINKED = {"lead": Lead, "customer": Customer, "milestone": ConstructionMilestone}


@table("my_tasks", None, [
    col("title", "Task"), col("about", "About", "ref"), col("priority", "Priority", "status"),
    col("due_on", "Due", "date"), col("status", "Status", "status")])
def my_task_row(s, t: Task) -> dict:
    target = s.one(LINKED[t.entity_type], t.entity_id) if t.entity_type in LINKED else None
    label = STAGE_LABELS.get(target.type) if t.entity_type == "milestone" and target else None
    late = t.status == "open" and t.due_on < s.today
    return {"title": t.title, "about": ref(t.entity_type, target, label) if target else None,
            "priority": status(t.priority), "due_on": t.due_on,
            # "Overdue" is kept for money. A late task says "Past due date".
            "status": status("overdue", label="Past due date") if late else status(t.status, "watch" if t.status == "open" else None)}


# ---------- employee portal ----------
EMPLOYEE_PAGES = ["day", "work", "meetings", "scorecard", "profile"]


def _calls(s, emp) -> list:
    """Scheduled calls with buyers: open tasks tied to a customer that start with "Call with"."""
    return sorted((t for t in s.kids(Task, "owner_employee_id", emp.id)
                   if t.status == "open" and t.entity_type == "customer" and t.title.startswith("Call with")),
                  key=lambda t: t.due_on)


def _visits(s, emp, upcoming: bool) -> list:
    visits = [v for v in s.kids(SiteVisit, "employee_id", emp.id)
              if (v.status == "scheduled") == upcoming and (upcoming or v.status == "done")]
    return sorted(visits, key=lambda v: v.scheduled_at, reverse=not upcoming)


def employee_page(s, user: User, name: str) -> dict:
    emp = s.one(Employee, user.employee_id)
    first = emp.name.split()[0]
    tasks = s.kids(Task, "owner_employee_id", emp.id)
    open_tasks = [t for t in tasks if t.status == "open"]
    overdue = sorted((t for t in open_tasks if t.due_on < s.today), key=lambda t: t.due_on)
    this_week = sorted((t for t in open_tasks if s.today <= t.due_on <= s.today + timedelta(days=7)), key=lambda t: t.due_on)
    is_sales, is_rm, is_site = emp.role_title in SALES_ROLES, emp.role_title == "Relationship Manager", emp.role_title in SITE_ROLES
    visits_today = [v for v in _visits(s, emp, True) if to_date(v.scheduled_at) == s.today]
    calls = _calls(s, emp)

    if name == "day":
        blocks, kpis = [], [kpi("Open tasks", len(open_tasks)), kpi("Overdue tasks", len(overdue))]
        if is_sales:
            me, team = sales_stats(s)["people"][emp.id], sales_stats(s)["team_conversion"]
            recent = lambda day: 0 <= (s.today - to_date(day)).days < 90  # noqa: E731
            kpis = [kpi("Bookings, last 90 days", sum(recent(b.booked_on) for b in me["bookings"])),
                    kpi("Site visits, last 90 days", sum(recent(v.scheduled_at) for v in me["visits"])),
                    kpi("My conversion", round(me["conversion"], 1), "percent", f"Team average {team:.1f}%"),
                    kpi("Stalled deals", len(me["idle"]), note=f"{inr(me['idle_value'])} at risk" if me["idle"] else None)]
            if me["idle"]:
                blocks.append(notice(f"{len(me['idle'])} of your negotiations have had no activity for 14 days or more."))
        elif is_rm:
            me = rm_stats(s)["people"].get(emp.id, {"buyers": [], "open_queries": 0, "response_hours": 0})
            owed = sum(s.customer_overdue(c.id)[0] for c in me["buyers"])
            kpis = [kpi("My buyers", len(me["buyers"]), note=f"Team average {round(rm_stats(s)['average_buyers'])}"),
                    kpi("Queries waiting for my reply", me["open_queries"]),
                    kpi("Overdue from my buyers", owed, "money"), kpi("My average reply time", me["response_hours"], note="hours")]
            if me["open_queries"]:
                blocks.append(notice(f"{me['open_queries']} buyer queries are waiting for your reply."))
        elif is_site:
            owned = s.kids(ConstructionMilestone, "owner_employee_id", emp.id)
            done = [m for m in owned if m.actual_date]
            late = [m for m in owned if m.id in s.delayed]
            kpis = [kpi("Milestones I own", len(owned)),
                    kpi("Finished on time", pct(sum(s.slip(m) <= ON_TIME_GRACE_DAYS for m in done), len(done)), "percent"),
                    kpi("Open quality issues", sum(q.status == "open" for q in s.kids(QualityIssue, "owner_employee_id", emp.id))),
                    kpi("Late right now", len(late))]
            for m in late:
                blocks.append(notice(f"{STAGE_LABELS[m.type]} at {tower_label(s, s.one(Tower, m.tower_id))} is {s.slip(m)} days late."))
        blocks += [block(s, "my_tasks", overdue, f"Overdue ({len(overdue)})"),
                   block(s, "my_tasks", this_week, "Due in the next 7 days")]
        if visits_today:
            blocks.append(block(s, "visits", visits_today, "Today's site visits"))
        if calls:
            blocks.append(block(s, "my_tasks", [c for c in calls if c.due_on <= s.today + timedelta(days=1)], "Calls today and tomorrow"))
        return page(f"Hello, {first}", f"{emp.role_title}. Here is your day.", blocks, kpis)

    if name == "work":
        if is_sales:
            me = sales_stats(s)["people"][emp.id]
            leads = [x for x in s.kids(Lead, "owner_employee_id", emp.id) if x.stage in ("visit_scheduled", "visit_done", "negotiation", "blocked")]
            blocks = [block(s, "leads", sorted(me["idle"], key=lambda x: -s.idle_days(x)), "Stalled negotiations"),
                      block(s, "leads", sorted(leads, key=lambda x: -s.idle_days(x)), "My open leads"),
                      block(s, "bookings", sorted(me["bookings"], key=lambda b: b.booked_on, reverse=True), "My bookings")]
        elif is_rm:
            buyers = rm_stats(s)["people"].get(emp.id, {"buyers": []})["buyers"]
            waiting = [q for c in buyers for q in s.open_queries(c.id)]
            owing = sorted((c for c in buyers if s.customer_overdue(c.id)[0] > 0), key=lambda c: -s.customer_overdue(c.id)[0])
            late = sorted((d for c in owing for b in s.bookings_of(c.id) for d in s.demands(b) if s.late(d)), key=lambda d: -s.late(d))
            total = sum(s.left(d) for d in late)
            blocks = [block(s, "interactions", waiting, "Queries waiting for my reply"),
                      block(s, "demands", late, f"Overdue payments of my buyers: {inr(total)} unpaid across {len(late)} payments"),
                      block(s, "customers", owing, f"My buyers with overdue payments ({len(owing)})"),
                      block(s, "customers", buyers, "All my buyers")]
        elif is_site:
            blocks = [block(s, "milestones", sorted(s.kids(ConstructionMilestone, "owner_employee_id", emp.id), key=lambda m: m.planned_date), "My milestones"),
                      block(s, "quality", s.kids(QualityIssue, "owner_employee_id", emp.id), "My quality issues")]
        else:
            blocks = [block(s, "my_tasks", sorted(open_tasks, key=lambda t: t.due_on), "My open tasks"),
                      block(s, "my_tasks", [t for t in tasks if t.status == "done"], "Finished tasks")]
        return page("My work", "Only records that are assigned to you.", blocks)

    if name == "meetings":
        blocks = []
        if is_sales:
            blocks = [block(s, "visits", _visits(s, emp, True), "Upcoming site visits"),
                      block(s, "visits", _visits(s, emp, False)[:15], "My last 15 site visits")]
        if calls:
            blocks.append(block(s, "my_tasks", calls, "Scheduled calls with buyers"))
        if not blocks:
            blocks = [notice("You have no meetings with customers scheduled.", "neutral")]
        return page("My meetings", "Site visits and calls with customers.", blocks)

    if name == "scorecard":
        card = employee_scorecard(s, emp)
        peers = sorted((e for e in s.all(Employee) if e.role_title == emp.role_title),
                       key=lambda e: -employee_scorecard(s, e)["score"])
        rank = next(i for i, e in enumerate(peers, start=1) if e.id == emp.id)
        average = round(sum(employee_scorecard(s, e)["score"] for e in peers) / len(peers))
        kpis = [kpi("My score", card["score"], "score"), kpi(f"Average for {emp.role_title}s", average, "score"),
                kpi("My position", rank, note=f"of {len(peers)} in this role")]
        return page("My scorecard", "How your score is worked out.", [{"kind": "scorecard", **card}] + _trend(s, emp), kpis)

    manager = s.one(Employee, emp.manager_id)
    team = s.kids(Employee, "manager_id", emp.id)
    profile = facts_block([fact("Employee code", emp.code), fact("Role", emp.role_title),
                           fact("Department", s.one(Department, emp.department_id).name), fact("Email", emp.email),
                           fact("Phone", emp.phone), fact("Joined", emp.joined_on, "date"),
                           fact("Reports to", manager.name if manager else "Nobody (team head)"),
                           fact("Manager's email", manager.email if manager else None)])
    blocks = [profile]
    if team:
        blocks.append(facts_block([fact(person.role_title, person.name) for person in team[:30]], f"My team ({len(team)})"))
    return page("My profile", "Your details as the company holds them.", blocks)


# ---------- customer portal ----------
CUSTOMER_PAGES = ["journey", "payments", "construction", "requests", "profile"]


def _step(key, label, state, date=None, text=None) -> dict:
    return {"key": key, "label": label, "state": state, "date": date, "text": text}


def _journey(s, booking: Booking) -> dict:
    """The buyer's path from booking to living in the home, with one step marked "you are here"."""
    unit = s.unit(booking)
    project = s.one(Project, unit.project_id)
    demands = sorted(s.demands(booking), key=lambda d: s.one(PlanMilestone, d.plan_milestone_id).seq)
    paid = pct(s.booking_paid(booking), num(booking.agreement_value))
    overdue, days = s.booking_overdue(booking)
    stages = sorted(s.kids(ConstructionMilestone, "tower_id", unit.tower_id), key=lambda m: m.seq) if unit.tower_id else []
    done_stages = [m for m in stages if m.actual_date]
    late = next((m for m in stages if m.id in s.delayed), None)
    upcoming = next((d for d in demands if d.due_on and s.left(d) > 0), None)
    waiting = next((d for d in demands if d.status == "not_raised"), None)
    loan = s.loan(booking)
    interior = next((p for p in s.kids(InteriorProject, "unit_id", unit.id) if p.customer_id == booking.customer_id), None)
    handover = next((m for m in stages if m.type == "handover"), None)
    planned_possession = handover.planned_date if handover else project.expected_possession

    steps = [_step("booking", "Booking", "done", booking.booked_on, "Your home is reserved and the booking amount is paid."),
             _step("agreement", "Agreement for sale", "done" if booking.agreement_on else "upcoming", booking.agreement_on,
                   "Signed." if booking.agreement_on else "We will invite you to sign the agreement for sale.")]
    if loan:
        stuck = loan.status == "awaiting_disbursement"
        steps.append(_step("loan", "Home loan", "issue" if stuck else "done", None,
                           f"{loan.bank}: {nice(loan.status).lower()}." + (" Please check with your bank; a payment is waiting on it." if stuck else "")))

    if overdue:
        pay_text = f"{inr(overdue)} is overdue by {days} days. Please pay or speak to your relationship manager."
    elif upcoming:
        pay_text = f"Your next payment of {inr(s.left(upcoming))} is due on {upcoming.due_on:%d %b %Y}."
    elif waiting:
        name = s.one(PlanMilestone, waiting.plan_milestone_id).name
        pay_text = f"Nothing is due now. Your next payment of {inr(num(waiting.amount))} will be asked for when this stage is finished: {name}."
        if waiting.construction_milestone_id in s.delayed:
            pay_text += f" That stage is running {s.slip(s.delayed[waiting.construction_milestone_id])} days late, so the payment is on hold."
    else:
        pay_text = "All payments are complete. Thank you."
    all_paid = not upcoming and not waiting
    if stages:
        build_text = f"{len(done_stages)} of {len(stages)} construction stages are complete."
        if late:
            build_text += (f" The {STAGE_LABELS[late.type].lower()} is running {s.slip(late)} days late."
                           " We will ask for the payment linked to it only after it is complete.")
        state = "done" if all_paid and handover and handover.actual_date else "issue" if (late or overdue) else "current"
        steps.append(_step("build", "Construction and payments", state, None, f"{build_text} You have paid {paid:g}%. {pay_text}"))
    else:
        steps.append(_step("build", "Payments", "done" if all_paid else "issue" if overdue else "current", None,
                           f"You have paid {paid:g}%. {pay_text}"))
    steps[-1]["next"] = pay_text  # the short "what happens next" line at the top of the page
    steps.append(_step("registration", "Registration", "done" if booking.registered_on else "upcoming", booking.registered_on,
                       "Your home is registered in your name." if booking.registered_on
                       else "We will book a slot at the registrar's office once the payments due before registration are complete."))
    steps.append(_step("possession", "Possession", "done" if booking.possession_on else "upcoming",
                       booking.possession_on or planned_possession,
                       "You have the keys." if booking.possession_on else "Planned date for handing over the keys."))
    steps.append(_step("interiors", "Interiors (optional)", "done" if interior and interior.stage == "done" else "current" if interior else "upcoming",
                       interior.target_date if interior else None,
                       f"{interior.package} package: {nice(interior.stage).lower()}." if interior
                       else "Ask your relationship manager about our interior packages."))
    open_tickets = sum(t.status != "resolved" for t in s.kids(ServiceTicket, "unit_id", unit.id))
    steps.append(_step("care", "After-sales care", "current" if booking.possession_on else "upcoming", None,
                       f"{open_tickets} open service requests." if booking.possession_on else "Starts on the day you get the keys."))

    # "You are here" = the first step that is not finished.
    here = next((i for i, step in enumerate(steps) if step["state"] != "done"), len(steps) - 1)
    for i, step in enumerate(steps):
        step["here"] = i == here
        if step["state"] == "current" and i != here:
            step["state"] = "upcoming"
        elif step["state"] == "upcoming" and i == here:
            step["state"] = "current"
    where = f"{project.name}, {s.one(Tower, unit.tower_id).name}" if unit.tower_id else project.name
    return {"kind": "journey", "title": f"Unit {unit.unit_no}, {where}", "unit": ref("unit", unit, unit.unit_no),
            "next_step": steps[here].get("next") or steps[here]["text"], "steps": steps}


def _home_facts(s, booking: Booking) -> dict:
    """Everything about the home itself: which project, tower and floor, how big, which way it faces."""
    unit = s.unit(booking)
    project, tower = s.one(Project, unit.project_id), s.one(Tower, unit.tower_id)
    return facts_block([
        fact("Project", f"{project.name}, {project.locality}"), fact("Tower", tower.name if tower else None),
        fact("Floor", f"{unit.floor} of {tower.floors}" if tower and unit.floor else None), fact("Unit number", unit.unit_no),
        fact("Type", unit.config), fact("Facing", unit.facing),
        fact("Carpet area", num(unit.carpet_sft) or None, "sqft"), fact("Super built-up area", num(unit.sba_sft) or None, "sqft"),
        fact("Plot area", num(unit.plot_sqyd) or None, "sqyd"), fact("Agreement value", num(booking.agreement_value), "money"),
        fact("Payment plan", s.one(PaymentPlan, booking.payment_plan_id).name), fact("Booked on", booking.booked_on, "date"),
    ], f"My home: unit {unit.unit_no}")


def _payment_stages(s, booking: Booking) -> list:
    """The payment plan in plain words, then every payment in order with what has happened to it."""
    plan = s.one(PaymentPlan, booking.payment_plan_id)
    demands = sorted(s.demands(booking), key=lambda d: s.one(PlanMilestone, d.plan_milestone_id).seq)
    rows, paid_count, linked = [], 0, 0
    for n, d in enumerate(demands, start=1):
        step = s.one(PlanMilestone, d.plan_milestone_id)
        linked += bool(step.construction_milestone_type)
        receipts = s.kids(Receipt, "demand_id", d.id)
        if d.due_on and s.left(d) == 0:
            paid_count += 1
            state, when = status("paid"), max(r.received_on for r in receipts) if receipts else d.due_on
        elif s.late(d):
            state, when = status("overdue", label=f"Overdue by {s.late(d)} days"), d.due_on
        elif d.due_on:
            state, when = status("raised", label="Due"), d.due_on
        elif d.construction_milestone_id in s.delayed:
            state, when = status("blocked", "risk", "Held: this stage is running late"), None
        else:
            state, when = status("not_raised", "neutral", "Not due yet: asked for when this stage is reached"), None
        rows.append({"id": str(d.id), "type": "demand", "target_id": str(d.id), "n": n, "stage": step.name,
                     "share": num(step.percent), "amount": num(d.amount), "when": when, "state": state})
    text = (f"Your payment plan is the {plan.name.lower()}, with {len(demands)} payments. "
            + (f"{linked} of them are tied to construction: each one is asked for only when that stage of the building is finished. " if linked else "")
            + f"You have made {paid_count} of the {len(demands)} payments.")
    return [notice(text, "neutral"),
            {"kind": "table", "title": f"All {len(demands)} payments, in order", "rows": rows,
             "columns": [col("n", "No.", "number"), col("stage", "Payment stage"), col("share", "Share", "percent"),
                         col("amount", "Amount", "money"), col("when", "Paid or due on", "date"), col("state", "Status", "status")]}]


def customer_page(s, user: User, name: str) -> dict:
    me = s.one(Customer, user.customer_id)
    bookings = s.bookings_of(me.id)
    rm = s.one(Employee, me.rm_employee_id)
    demands = [d for b in bookings for d in s.demands(b)]

    if name == "journey":
        blocks = []
        for b in bookings:
            blocks += [_journey(s, b), _home_facts(s, b)] + _payment_stages(s, b)
        return page(f"Welcome, {me.name.split()[0]}", "Where you are, and what comes next.", blocks)

    if name == "payments":
        value = sum(num(b.agreement_value) for b in bookings)
        paid = sum(s.booking_paid(b) for b in bookings)
        overdue = sum(s.left(d) for d in demands if s.late(d))
        coming = min((d for d in demands if d.due_on and d.due_on >= s.today and s.left(d) > 0), key=lambda d: d.due_on, default=None)
        kpis = [kpi("Agreement value", value, "money"), kpi("Paid so far", paid, "money", f"{pct(paid, value):g}% of the total"),
                kpi("Next payment", s.left(coming) if coming else 0, "money", f"Due {coming.due_on:%d %b %Y}" if coming else "Nothing due right now"),
                kpi("Overdue", overdue, "money", "Please contact your relationship manager" if overdue else "Nothing overdue")]
        blocks = []
        for b in bookings:
            rows = sorted(s.demands(b), key=lambda d: s.one(PlanMilestone, d.plan_milestone_id).seq)
            blocks.append(block(s, "demands", rows, f"Payment schedule, unit {s.unit(b).unit_no} ({s.one(PaymentPlan, b.payment_plan_id).name})"))
        receipts = sorted((r for d in demands for r in s.kids(Receipt, "demand_id", d.id)), key=lambda r: r.received_on, reverse=True)
        blocks.append(block(s, "receipts", receipts, "Payments we have received"))
        return page("Payments", "Your full payment schedule and every payment received.", blocks, kpis)

    if name == "construction":
        blocks = []
        for b in bookings:
            unit = s.unit(b)
            if not unit.tower_id:
                blocks.append(notice(f"Unit {unit.unit_no} is not in a tower, so it has no stage-by-stage tracker. "
                                     "Your relationship manager can share the latest site photos.", "neutral"))
                continue
            tower = s.one(Tower, unit.tower_id)
            stages = sorted(s.kids(ConstructionMilestone, "tower_id", tower.id), key=lambda m: m.seq)
            done = sum(1 for m in stages if m.actual_date)
            blocks.append(notice(
                f"{tower.name} has {tower.floors} floors; your home is on floor {unit.floor}. We track the building in "
                f"{len(stages)} stages: {', '.join(STAGE_LABELS[m.type].lower() for m in stages)}. "
                f"{done} of {len(stages)} are complete. A floor slab is the concrete floor of that storey; "
                "we report the slabs that your payments are tied to, not every floor.", "neutral"))
            for m in stages:
                if m.id in s.delayed:
                    blocks.append(notice(f"The {STAGE_LABELS[m.type].lower()} was planned for {m.planned_date:%d %b %Y} and is "
                                         f"running {s.slip(m)} days late. We are sorry for the delay."))
            rows = [{"id": str(m.id), "stage": STAGE_LABELS[m.type], "planned": m.planned_date, "actual": m.actual_date,
                     "state": status("done") if m.actual_date else status("delayed", label="Running late") if m.id in s.delayed
                     else status("in_progress") if num(m.percent_complete) > 0 else status("scheduled", "neutral", "Upcoming")}
                    for m in stages]
            blocks.append({"kind": "table", "title": f"{tower_label(s, tower)}: construction stages",
                           "columns": [col("stage", "Stage"), col("planned", "Planned", "date"),
                                       col("actual", "Finished", "date"), col("state", "Status", "status")], "rows": rows})
        return page("Construction progress", "How the building of your home is going.", blocks)

    if name == "requests":
        talks = s.kids(CustomerInteraction, "customer_id", me.id)
        waiting = s.open_queries(me.id)
        items = [(i.occurred_at, ("You" if i.direction == "inbound" else rm.name) + f", by {i.channel}", i.summary,
                  "risk" if i in waiting else "neutral") for i in talks]
        tickets = s.kids(ServiceTicket, "customer_id", me.id)
        blocks = [notice(f"{len(waiting)} of your messages are still waiting for our reply. We are sorry for the delay.")] if waiting else []
        blocks += [block(s, "tickets", tickets, "Service requests and complaints"), timeline(items)]
        return page("Requests", "Your messages to us and our replies.", blocks,
                    [kpi("Waiting for our reply", len(waiting)), kpi("Open service requests", sum(t.status != "resolved" for t in tickets))])

    return page("My profile", "Your details and your home, as we hold them.", [
        facts_block([fact("Name", me.name), fact("Phone", me.phone), fact("Email", me.email), fact("City", me.city),
                     fact("Country", me.country)], "About me"),
        *[_home_facts(s, b) for b in bookings],
        facts_block([fact("Name", rm.name), fact("Email", rm.email), fact("Phone", rm.phone)], "My relationship manager"),
    ])
