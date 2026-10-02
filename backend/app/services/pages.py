"""Charts, summaries and lists for each console page, plus the unit grid and global search."""
from collections import Counter, defaultdict
from datetime import timedelta

from app.db.models import (
    Booking, ChannelPartner, ConstructionMilestone, Contractor, Customer, Demand, Department, Employee,
    Lead, PriceHistory, Project, ProjectBudget, QualityIssue, Receipt, Risk, SafetyIncident, SiteVisit,
    Tower, Unit,
)
from app.scoring.scores import CFG as SCORING
from app.scoring.scores import (
    CONVERTED, ON_TIME_GRACE_DAYS, SITE_ROLES, customer_health, employee_scorecard, project_stats, rm_stats,
    sales_stats,
)
from app.services.common import Filters, chart, col, month_starts, nice, pct, ref, score_cell
from app.services.metrics import bookings_in, buyers_of, demands_of, project_of_booking, stages_of
from app.services.snapshot import num, to_date
from app.services.tables import (
    STAGE_LABELS, block, build, employee_headline, partner_stats, risk_card, tower_label,
)

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
AGEING_BUCKETS = [("0-30 days", 0, 30), ("31-60 days", 31, 60), ("61-90 days", 61, 90), ("90+ days", 91, 10**6)]


def month_label(day) -> str:
    return day.strftime("%b %y")


def open_risks(s) -> list:
    risks = [r for r in s.all(Risk) if r.status != "resolved"]
    return sorted(risks, key=lambda r: (SEVERITY_ORDER[r.severity], -r.facts_json["impact"]))


# ---------- Overview ----------
def overview(s, f: Filters) -> dict:
    months = month_starts(s.today, 12)
    booked, collected = defaultdict(float), defaultdict(float)
    for b in s.active_bookings:
        if f.project_ok(project_of_booking(s, b)):
            booked[b.booked_on.replace(day=1)] += num(b.agreement_value)
    for r in s.all(Receipt):
        if f.project_ok(project_of_booking(s, s.one(Booking, s.one(Demand, r.demand_id).booking_id))):
            collected[r.received_on.replace(day=1)] += num(r.amount)

    health = []
    for project in s.all(Project):
        stats = project_stats(s, project)
        health.append({"project": ref("project", project), "type": nice(project.type), "sold_pct": stats["sold_pct"],
                       "construction_pct": stats["construction_pct"],
                       "collection_efficiency": stats["collection_efficiency"],
                       "health": score_cell(stats["health"]["score"])})

    visits_today = [v for v in s.all(SiteVisit) if to_date(v.scheduled_at) == s.today]
    handovers = [m for m in s.all(ConstructionMilestone) if m.type == "handover" and m.actual_date is None
                 and (m.planned_date - s.today).days <= 180]
    rms = sorted((e for e in s.all(Employee) if e.id in rm_stats(s)["people"]),
                 key=lambda e: -employee_scorecard(s, e)["score"])[:5]
    partners = sorted(s.all(ChannelPartner), key=lambda p: -partner_stats(s, p)["value"])[:5]
    return {
        "monthly": chart("Bookings vs collections, last 12 months", [month_label(m) for m in months],
                         [{"name": "Bookings", "data": [booked[m] for m in months]},
                          {"name": "Collections", "data": [collected[m] for m in months]}], kind="money"),
        "attention": [risk_card(s, r) for r in open_risks(s)[:5]],
        "project_health": health,
        "funnel": sales_funnel(s, f)["funnel"],
        "site_visits_today": block(s, "visits", visits_today, "Site visits today"),
        "handovers": block(s, "milestones", handovers, "Handovers in the next 6 months"),
        "top_rms": block(s, "employees", rms, "Top 5 relationship managers"),
        "top_partners": block(s, "partners", partners, "Top 5 channel partners"),
    }


# ---------- Projects and inventory ----------
def projects(s) -> list[dict]:
    out = []
    for p in s.all(Project):
        stats = project_stats(s, p)
        out.append({"id": str(p.id), "type": "project", "name": p.name, "kind": nice(p.type), "locality": p.locality,
                    "rera_no": p.rera_no, "launch_date": p.launch_date, "expected_possession": p.expected_possession,
                    "status": nice(p.status), "hero_image": p.hero_image, "units": stats["units"], "sold": stats["sold"],
                    "sold_pct": stats["sold_pct"], "construction_pct": stats["construction_pct"],
                    "health": score_cell(stats["health"]["score"]),
                    "towers": [{"id": str(t.id), "name": t.name} for t in s.kids(Tower, "project_id", p.id)]})
    return out


def inventory(s, project: Project, tower_id=None) -> dict:
    """The unit grid: floors as rows, units as cells. Each cell carries what the four colourings need."""
    towers = s.kids(Tower, "project_id", project.id)
    tower = s.one(Tower, tower_id) if tower_id else (towers[0] if towers else None)
    units = s.kids(Unit, "tower_id", tower.id) if tower else s.kids(Unit, "project_id", project.id)

    def cell(u: Unit) -> dict:
        booking = s.unit_booking.get(u.id)
        health = customer_health(s, s.one(Customer, booking.customer_id))["score"] if booking else None
        return {"id": str(u.id), "unit_no": u.unit_no, "config": u.config, "facing": u.facing, "status": u.status,
                "price_psf": num(u.base_price_psf), "days_unsold": s.days_unsold(u), "payment_health": health}

    rows = defaultdict(list)
    for index, u in enumerate(sorted(units, key=lambda u: u.unit_no)):
        rows[u.floor if u.floor is not None else index // 10 + 1].append(cell(u))
    labelled = "Floor" if tower else "Row"
    floors = [{"label": f"{labelled} {key}", "units": rows[key]} for key in sorted(rows, reverse=bool(tower))]

    history = s.kids(PriceHistory, "project_id", project.id)
    days = sorted({h.effective_from for h in history})
    trend = chart(f"Price per sq {'yd' if project.type == 'plots' else 'ft'}, {project.name}",
                  [d.strftime("%b %y") for d in days],
                  [{"name": config, "data": [next((num(h.price_psf) for h in history
                                                   if h.config == config and h.effective_from == d), None) for d in days]}
                   for config in sorted({h.config for h in history})], kind="money", type="line")
    psf = [num(u.base_price_psf) for u in units]
    return {"project": ref("project", project), "tower": ref("tower", tower) if tower else None,
            "towers": [{"id": str(t.id), "name": t.name} for t in towers], "floors": floors,
            "price_range": [min(psf), max(psf)] if psf else None,
            "status_counts": dict(Counter(u.status for u in units)), "price_trend": trend,
            "towers_table": block(s, "towers", towers, "Towers")}


# ---------- Sales ----------
def leads_in(s, f: Filters) -> list:
    """Leads created in the chosen period, for the chosen project."""
    return [x for x in s.all(Lead) if f.project_ok(x.preferred_project_id) and f.covers(to_date(x.created_at))]


def sales_funnel(s, f: Filters) -> dict:
    leads = leads_in(s, f)
    visited = {v.lead_id for v in s.all(SiteVisit) if v.status == "done"}
    late_stages = CONVERTED + ("negotiation", "blocked")
    steps = [("New leads", len(leads)), ("Contacted", sum(x.stage != "new" for x in leads)),
             ("Site visit done", sum(x.id in visited for x in leads)),
             ("Negotiation", sum(x.stage in late_stages for x in leads)),
             ("Booked", sum(x.stage in CONVERTED for x in leads))]
    seen, won = Counter(x.source for x in leads), Counter(x.source for x in leads if x.stage in CONVERTED)
    sources = [name for name, _ in seen.most_common()]
    return {
        "funnel": chart("Sales funnel, leads created in this period", [name for name, _ in steps],
                        [{"name": "Leads", "data": [count for _, count in steps]}], type="funnel"),
        "sources": chart("Lead sources, leads created in this period", sources,
                         [{"name": "Leads", "data": [seen[x] for x in sources]},
                          {"name": "Bookings", "data": [won[x] for x in sources]}],
                         conversion_pct=[pct(won[x], seen[x]) for x in sources]),
    }


def sales_lost(s, f: Filters) -> dict:
    lost = Counter(x.lost_reason for x in leads_in(s, f) if x.stage == "lost")
    cancelled = Counter(b.cancel_reason for b in bookings_in(s, f, active_only=False) if b.status == "cancelled")
    def bar(title, counter):
        names = [name for name, _ in counter.most_common()]
        return chart(title, names, [{"name": "Count", "data": [counter[n] for n in names]}])
    return {"lost": bar("Why leads were lost, leads created in this period", lost),
            "cancelled": bar("Why bookings were cancelled, booked in this period", cancelled)}


# ---------- Customers ----------
def customers_summary(s, f: Filters) -> dict:
    buyers = buyers_of(s, f)
    bands = [("Below 40", 0, 39), ("40-59", 40, 59), ("60-74", 60, 74), ("75-89", 75, 89), ("90-100", 90, 100)]
    scores = [customer_health(s, c)["score"] for c in buyers]
    kinds = Counter("NRI" if c.is_nri else nice(c.type) for c in buyers)
    countries = Counter(c.country for c in buyers)
    return {
        "health": chart("Buyers by health score", [name for name, _, _ in bands],
                        [{"name": "Buyers", "data": [sum(lo <= x <= hi for x in scores) for _, lo, hi in bands]}]),
        "types": chart("Buyers by type", list(kinds), [{"name": "Buyers", "data": list(kinds.values())}]),
        "countries": chart("Buyers by country", [n for n, _ in countries.most_common()],
                           [{"name": "Buyers", "data": [c for _, c in countries.most_common()]}]),
    }


# ---------- Collections ----------
def collections_summary(s, f: Filters) -> dict:
    late = [d for d in demands_of(s, f) if s.late(d)]
    names = [p.name for p in s.all(Project) if f.project_ok(p.id)]
    by_project, by_bank = defaultdict(lambda: defaultdict(float)), defaultdict(float)
    for d in late:
        booking = s.one(Booking, d.booking_id)
        bucket = next(name for name, lo, hi in AGEING_BUCKETS if lo <= s.late(d) <= hi)
        by_project[s.one(Project, project_of_booking(s, booking)).name][bucket] += s.left(d)
        loan = s.loan(booking)
        by_bank[loan.bank if loan else "No loan"] += s.left(d)
    banks = sorted(by_bank, key=by_bank.get, reverse=True)
    return {
        "ageing": chart("Overdue amount by age and project", names,
                        [{"name": name, "data": [by_project[p][name] for p in names]} for name, _, _ in AGEING_BUCKETS],
                        kind="money", type="stacked"),
        "by_bank": chart("Overdue amount by buyer's bank", banks,
                         [{"name": "Overdue", "data": [by_bank[b] for b in banks]}], kind="money"),
    }


# ---------- Construction ----------
def delay_impact(s, f: Filters) -> list[dict]:
    """For each late stage: the demands it blocks, the buyers affected and the money not yet raised."""
    out = []
    for stage in s.delayed.values():
        tower = s.one(Tower, stage.tower_id)
        if not f.project_ok(tower.project_id):
            continue
        blocked = s.blocked(stage)
        buyers = {s.one(Booking, d.booking_id).customer_id for d in blocked}
        out.append({"milestone": ref("milestone", stage, STAGE_LABELS[stage.type]),
                    "tower": ref("tower", tower, tower_label(s, tower)), "stage": STAGE_LABELS[stage.type],
                    "planned": stage.planned_date, "slip_days": s.slip(stage),
                    "contractor": ref("contractor", s.one(Contractor, stage.contractor_id)), "cause": stage.delay_cause,
                    "bookings": len({d.booking_id for d in blocked}), "amount": sum(num(d.amount) for d in blocked),
                    "buyers": [ref("customer", s.one(Customer, c)) for c in buyers],
                    "demands": block(s, "demands", blocked, "Blocked demands")})
    return sorted(out, key=lambda x: -x["amount"])


def construction_summary(s, f: Filters) -> dict:
    timeline = []
    for tower in s.all(Tower):
        if f.project_ok(tower.project_id):
            stages = sorted(s.kids(ConstructionMilestone, "tower_id", tower.id), key=lambda m: m.seq)
            timeline.append({"tower": ref("tower", tower, tower_label(s, tower)), "stages": [
                {"id": str(m.id), "type": "milestone", "label": STAGE_LABELS[m.type], "planned": m.planned_date,
                 "actual": m.actual_date, "slip_days": s.slip(m) if m.actual_date or m.id in s.delayed else 0,
                 "state": "done" if m.actual_date else "delayed" if m.id in s.delayed else "upcoming"}
                for m in stages]})
    return {"timeline": {"title": "Planned vs actual milestones, by tower", "today": s.today, "towers": timeline},
            "delay_impact": delay_impact(s, f)}


# ---------- Employees ----------
def _board(title: str, columns: list, rows: list, key, top: int = 5) -> dict:
    """A small ranking table. Each row opens that employee."""
    rows = sorted(rows, key=key)[:top]
    for row in rows:
        row.update(id=row["name"]["id"], type="employee", target_id=row["name"]["id"])
    return {"kind": "table", "title": title, "columns": columns, "rows": rows}


def leaderboards(s, f: Filters) -> list[dict]:
    """Who did best. Sales and RM boards count only what happened in the chosen period."""
    sales = []
    for emp_id, me in sales_stats(s)["people"].items():
        bookings = [b for b in me["bookings"] if b.status != "cancelled" and f.covers(b.booked_on)]
        visits = sum(1 for v in me["visits"] if f.covers(to_date(v.scheduled_at)))
        sales.append({"name": ref("employee", s.one(Employee, emp_id)), "bookings": len(bookings),
                      "value": sum(num(b.agreement_value) for b in bookings), "visits": visits,
                      "conversion": pct(len(bookings), visits)})
    managers = []
    for emp_id, me in rm_stats(s)["people"].items():
        collected = sum(num(r.amount) for c in me["buyers"] for b in s.bookings_of(c.id) for d in s.demands(b)
                        for r in s.kids(Receipt, "demand_id", d.id) if f.covers(r.received_on))
        managers.append({"name": ref("employee", s.one(Employee, emp_id)), "collected": collected,
                         "buyers": len(me["buyers"]), "queries": me["open_queries"], "hours": me["response_hours"]})
    site = []
    for e in s.all(Employee):
        owned = s.kids(ConstructionMilestone, "owner_employee_id", e.id)
        done = [m for m in owned if m.actual_date]
        if e.role_title in SITE_ROLES and done:
            site.append({"name": ref("employee", e), "owned": len(owned),
                         "on_time": pct(sum(s.slip(m) <= ON_TIME_GRACE_DAYS for m in done), len(done)),
                         "issues": sum(q.status == "open" for q in s.kids(QualityIssue, "owner_employee_id", e.id))})
    who = col("name", "Name", "ref")
    return [
        _board("Top sales managers, by booking value in this period",
               [who, col("bookings", "Bookings", "number"), col("value", "Booking value", "money"),
                col("visits", "Site visits", "number"), col("conversion", "Conversion", "percent")],
               sales, key=lambda r: -r["value"]),
        _board("Top relationship managers, by money collected in this period",
               [who, col("collected", "Collected", "money"), col("buyers", "Buyers", "number"),
                col("queries", "Open queries", "number"), col("hours", "Reply time (hours)", "number")],
               managers, key=lambda r: -r["collected"]),
        _board("Site team, by milestones finished on time",
               [who, col("owned", "Milestones owned", "number"), col("on_time", "On time", "percent"),
                col("issues", "Open quality issues", "number")],
               site, key=lambda r: (-r["on_time"], r["issues"])),
    ]


def teams(s, f: Filters) -> list[dict]:
    """Every department with its people: who leads it, who is in it, how each one is doing."""
    out = []
    for dept in s.all(Department):
        team = [e for e in s.kids(Employee, "department_id", dept.id) if e.status != "exited"]
        team.sort(key=lambda e: (e.manager_id is not None, e.role_title, -employee_scorecard(s, e)["score"], e.name))
        scores = [employee_scorecard(s, e)["score"] for e in team]
        head = next((e for e in team if e.manager_id is None), None)
        out.append({
            "name": dept.name, "headcount": len(team), "head": ref("employee", head),
            "avg_score": score_cell(sum(scores) / len(scores), 80, 60),
            "needs_attention": sum(employee_scorecard(s, e)["needs_attention"] for e in team),
            "joined_in_period": sum(f.covers(e.joined_on) for e in team),
            "roles": [{"role": role, "count": count} for role, count in Counter(e.role_title for e in team).most_common()],
            "members": [{"ref": ref("employee", e), "role": e.role_title, "headline": employee_headline(s, e),
                         "score": score_cell(employee_scorecard(s, e)["score"], 80, 60), "joined_on": e.joined_on,
                         "is_new": f.covers(e.joined_on) and (s.today - e.joined_on).days <= 180,
                         "is_head": e.manager_id is None, "on_leave": e.status == "on_leave"} for e in team],
        })
    return out


def employees_summary(s, f: Filters) -> dict:
    by_department = defaultdict(list)
    for e in s.all(Employee):
        by_department[s.one(Department, e.department_id).name].append(employee_scorecard(s, e)["score"])
    names = list(by_department)
    rms = rm_stats(s)
    people = sorted(rms["people"].items(), key=lambda kv: -len(kv[1]["buyers"]))
    return {
        "teams": teams(s, f),
        "leaderboards": leaderboards(s, f),
        "by_department": chart("Average scorecard score by department", names,
                               [{"name": "Score", "data": [round(sum(v) / len(v)) for v in by_department.values()]}],
                               kind="score"),
        "workload": chart("Active buyers per relationship manager", [s.one(Employee, i).name for i, _ in people],
                          [{"name": "Buyers", "data": [len(v["buyers"]) for _, v in people]}],
                          average=round(rms["average_buyers"], 1),
                          refs=[ref("employee", s.one(Employee, i)) for i, _ in people]),
    }


# ---------- Lists (the main table on each page and in each tab) ----------
def list_rows(s, name: str, f: Filters, args: dict) -> tuple[list, list]:
    """Returns (columns, rows) for a named list. `args` are extra query parameters like stage or tab."""
    def has(key):
        return args.get(key) or None

    if name == "customers":
        objs = buyers_of(s, f)
        if has("band"):
            objs = [c for c in objs if customer_health(s, c)["band"] == args["band"]]
        if has("health_min") or has("health_max"):  # one bar of the health chart
            low, high = int(args.get("health_min") or 0), int(args.get("health_max") or 100)
            objs = [c for c in objs if low <= customer_health(s, c)["score"] <= high]
        return build(s, "customers", objs)
    if name == "stalled":  # a "right now" list: it does not follow the date range
        stall = SCORING["sales"]["stalled_negotiation_days"]
        objs = [x for x in s.all(Lead) if f.project_ok(x.preferred_project_id) and x.stage == "negotiation"
                and s.idle_days(x) >= stall]
        return build(s, "leads", sorted(objs, key=lambda x: -s.idle_days(x)))
    if name in ("leads", "lost"):  # leads created in the chosen period
        objs = leads_in(s, f)
        if name == "lost":
            objs = [x for x in objs if x.stage in ("lost", "cancelled")]
        elif has("stage"):
            objs = [x for x in objs if x.stage == args["stage"]]
        return build(s, "leads", sorted(objs, key=lambda x: x.created_at, reverse=True))
    if name == "bookings":  # bookings made in the chosen period
        objs = bookings_in(s, f, active_only=False)
        if has("status"):
            objs = [b for b in objs if b.status == args["status"]]
        return build(s, "bookings", sorted(objs, key=lambda b: b.booked_on, reverse=True))
    if name == "demands":
        tab = args.get("tab", "all")
        objs = demands_of(s, f)
        if tab == "blocked":
            objs = [d for d in objs if d.construction_milestone_id in s.delayed and d.status == "not_raised"]
        elif tab == "awaiting_bank":
            objs = [d for d in objs if s.late(d) and getattr(s.loan(s.one(Booking, d.booking_id)), "status", "")
                    == "awaiting_disbursement"]
        elif tab == "overdue":
            objs = [d for d in objs if s.late(d)]
        else:  # "all": demands raised in the chosen period
            objs = [d for d in objs if f.covers(d.raised_on)]
        return build(s, "demands", sorted(objs, key=lambda d: -s.late(d)))
    if name == "units":
        objs = [u for u in s.all(Unit) if f.project_ok(u.project_id)]
        if has("ageing"):
            objs = sorted((u for u in objs if u.status == "available"), key=lambda u: u.listed_on)
        elif has("status"):
            objs = [u for u in objs if u.status == args["status"]]
        return build(s, "units", objs)
    if name == "milestones":
        return build(s, "milestones", sorted(stages_of(s, f), key=lambda m: m.planned_date))
    if name == "employees":
        objs = sorted(s.all(Employee), key=lambda e: employee_scorecard(s, e)["score"])
        if has("department"):
            objs = [e for e in objs if s.one(Department, e.department_id).name == args["department"]]
        return build(s, "employees", objs)
    if name == "safety":  # incidents in the chosen period
        objs = [i for i in s.all(SafetyIncident) if f.project_ok(i.project_id) and f.covers(i.occurred_on)]
        return build(s, "safety", sorted(objs, key=lambda i: i.occurred_on, reverse=True))
    if name == "quality":  # issues raised in the chosen period
        objs = [q for q in s.all(QualityIssue) if f.project_ok(s.project_id_of_tower(q.tower_id)) and f.covers(q.raised_on)]
        return build(s, "quality", sorted(objs, key=lambda q: (q.status != "open", -q.raised_on.toordinal())))
    simple = {"partners": (ChannelPartner, None), "contractors": (Contractor, None),
              "budgets": (ProjectBudget, "project_id"), "safety": (SafetyIncident, "project_id"),
              "towers": (Tower, "project_id")}
    model, project_attr = simple[name]
    return build(s, name, [o for o in s.all(model) if not project_attr or f.project_ok(getattr(o, project_attr))])


LIST_NAMES = ["customers", "leads", "stalled", "lost", "bookings", "demands", "units", "milestones", "employees",
              "quality", "partners", "contractors", "budgets", "safety", "towers"]


def risks_page(s, category=None, status_filter=None, severity=None) -> dict:
    risks = sorted(s.all(Risk), key=lambda r: (r.status == "resolved", SEVERITY_ORDER[r.severity], -r.facts_json["impact"]))
    shown = [r for r in risks if (not category or r.category == category) and (not severity or r.severity == severity)
             and (not status_filter or r.status == status_filter)]
    return {"high_open": sum(r.severity == "high" and r.status != "resolved" for r in risks),
            "categories": dict(Counter(r.category for r in risks if r.status != "resolved")),
            "items": [risk_card(s, r) for r in shown]}


# ---------- Search ----------
def search(s, q: str, limit: int = 6) -> list[dict]:
    """Ctrl+K search. Returns groups of clickable entities."""
    needle = q.strip().lower()
    if len(needle) < 2:
        return []

    def find(label, kind, objs, text, subtitle):
        hits = [o for o in objs if needle in text(o).lower()][:limit]
        return {"label": label, "items": [{**ref(kind, o, text(o)), "subtitle": subtitle(o)} for o in hits]}

    project_name = lambda pid: s.one(Project, pid).name  # noqa: E731
    groups = [
        find("Customers", "customer", s.all(Customer), lambda c: c.name, lambda c: f"{nice(c.type)} buyer, {c.city}"),
        find("Units", "unit", s.all(Unit), lambda u: u.unit_no, lambda u: f"{project_name(u.project_id)}, {u.config}"),
        find("Projects", "project", s.all(Project), lambda p: p.name, lambda p: f"{nice(p.type)}, {p.locality}"),
        find("Employees", "employee", s.all(Employee), lambda e: e.name, lambda e: e.role_title),
        find("Channel partners", "partner", s.all(ChannelPartner), lambda p: p.firm_name, lambda p: p.city),
        find("Leads", "lead", s.all(Lead), lambda x: x.name, lambda x: f"{nice(x.stage)}, {x.source}"),
    ]
    return [g for g in groups if g["items"]]
