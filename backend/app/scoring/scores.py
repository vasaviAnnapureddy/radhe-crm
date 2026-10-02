"""The four scores. Pure formulas first (easy to test), then helpers that gather inputs from the snapshot.

Weights and thresholds come from config/scoring.yaml. Every score returns its parts, so the UI can show them.
"""
from app.core.config import load_config
from app.db.models import (
    Booking, ConstructionMilestone, CustomerInteraction, Employee, EmployeeTarget, Lead, LeadActivity,
    Project, ProjectBudget, QualityIssue, Receipt, Risk, ServiceTicket, SiteVisit, Task, Tower, Unit,
)
from app.services.snapshot import num, to_date

CFG = load_config("scoring.yaml")
SALES_ROLES = ("Sales Manager", "NRI Desk Manager")
SITE_ROLES = ("Site Engineer", "Project Manager")
ON_TIME_GRACE_DAYS = 7  # a stage finished up to a week late still counts as on time
CONVERTED = ("booked", "agreement_signed", "registered", "possession", "cancelled")


def linear(value: float, full_at: float, zero_at: float) -> float:
    """1.0 at `full_at`, 0.0 at `zero_at`, a straight line in between."""
    return min(max((zero_at - value) / (zero_at - full_at), 0.0), 1.0)


def _total(parts: list[dict]) -> int:
    return round(sum(p["points"] for p in parts))


def _part(key: str, label: str, weight: float, share: float, detail: str) -> dict:
    return {"key": key, "label": label, "weight": weight, "points": round(weight * share, 1), "detail": detail}


# ---------- buyer health ----------
def buyer_health(on_time: int, payments: int, worst_overdue_days: int, days_since_contact: int,
                 open_tickets: int, unanswered: int, loan_status: str | None) -> dict:
    cfg, w = CFG["buyer_health"], CFG["buyer_health"]["weights"]
    ratio = on_time / payments if payments else 1.0
    penalty = cfg["complaint_penalty"]
    parts = [
        _part("payment_timeliness", "Payment timeliness", w["payment_timeliness"],
              ratio * linear(worst_overdue_days, 0, cfg["overdue_zero_marks_days"]),
              f"{on_time} of {payments} payments on time; worst overdue {worst_overdue_days} days"),
        _part("engagement_recency", "Engagement", w["engagement_recency"],
              linear(days_since_contact, cfg["engagement_full_marks_days"], cfg["engagement_zero_marks_days"]),
              f"We last contacted the buyer {days_since_contact} days ago"),
        _part("open_complaints", "Complaints and queries", w["open_complaints"],
              max(0.0, 1 - penalty["open_ticket"] * open_tickets - penalty["unanswered_query"] * unanswered),
              f"{open_tickets} open tickets, {unanswered} unanswered queries"),
        _part("loan_status", "Loan status", w["loan_status"], cfg["loan_factor"].get(loan_status or "none", 1.0),
              f"Loan: {(loan_status or 'no loan').replace('_', ' ')}"),
    ]
    score = _total(parts)
    band = "good" if score >= cfg["bands"]["good_min"] else "watch" if score >= cfg["bands"]["watch_min"] else "risk"
    return {"score": score, "band": band, "parts": parts}


def customer_health(s, customer) -> dict:
    def build():
        on_time = payments = worst = 0
        loan_status = None
        for booking in s.bookings_of(customer.id):
            for demand in s.demands(booking):
                worst = max(worst, s.late(demand))
                for receipt in s.kids(Receipt, "demand_id", demand.id):
                    payments += 1
                    on_time += receipt.received_on <= demand.due_on
            loan = s.loan(booking)
            if loan and loan_status != "awaiting_disbursement":
                loan_status = loan.status
        last = s.last_contact(customer.id)
        tickets = [t for t in s.kids(ServiceTicket, "customer_id", customer.id) if t.status != "resolved"]
        return buyer_health(on_time, payments, worst, (s.today - last).days if last else 999, len(tickets),
                            len(s.open_queries(customer.id)), loan_status)
    return s.memo(("health", customer.id), build)


# ---------- lead score ----------
def lead_score(budget_fit: float, source_quality: float, engagement: float, days_since_contact: int) -> dict:
    cfg, w = CFG["lead_score"], CFG["lead_score"]["weights"]
    parts = [
        _part("budget_fit", "Budget fit", w["budget_fit"], budget_fit,
              f"Budget covers {round(budget_fit * 100)}% of the cheapest matching home"),
        _part("source_quality", "Source quality", w["source_quality"], source_quality,
              f"This source converts at {round(source_quality * 100)}% of the best source"),
        _part("engagement", "Engagement", w["engagement"], engagement, "Calls, messages and site visits so far"),
        _part("contact_recency", "Recent contact", w["contact_recency"],
              linear(days_since_contact, 3, cfg["contact_zero_marks_days"]),
              f"Last contact {days_since_contact} days ago"),
    ]
    return {"score": _total(parts), "parts": parts}


def score_lead(s, lead: Lead) -> dict:
    def source_rates():
        seen, won = {}, {}
        for item in s.all(Lead):
            seen[item.source] = seen.get(item.source, 0) + 1
            won[item.source] = won.get(item.source, 0) + (item.stage in CONVERTED)
        rates = {source: won[source] / seen[source] for source in seen}
        best = max(rates.values()) or 1
        return {source: rate / best for source, rate in rates.items()}

    def cheapest():
        out = {}
        for unit in s.all(Unit):
            if unit.status == "available":
                key = (unit.project_id, unit.config)
                out[key] = min(out.get(key, float("inf")), s.price(unit))
        return out

    def build():
        floor_price = s.memo("cheapest", cheapest).get((lead.preferred_project_id, lead.preferred_config))
        fit = min(num(lead.budget_max) / floor_price, 1.0) if floor_price else 0.3
        visits = sum(v.status == "done" for v in s.kids(SiteVisit, "lead_id", lead.id))
        touches = len(s.kids(LeadActivity, "lead_id", lead.id)) + 2 * visits
        return lead_score(fit, s.memo("source_rates", source_rates).get(lead.source, 0.5),
                          min(touches / 8, 1.0), s.idle_days(lead))
    return s.memo(("lead_score", lead.id), build)


# ---------- project health ----------
def project_health(slip_days: float, cost_variance_pct: float, sold_vs_plan: float, collection_efficiency: float,
                   open_high_risks: int) -> dict:
    cfg, w = CFG["project_health"], CFG["project_health"]["weights"]
    parts = [
        _part("schedule_variance", "Schedule", w["schedule_variance"],
              linear(slip_days, 0, cfg["schedule_zero_marks_slip_days"]), f"Worst open slip {round(slip_days)} days"),
        _part("cost_variance", "Cost", w["cost_variance"],
              linear(cost_variance_pct, 0, cfg["cost_zero_marks_variance_pct"]),
              f"Actual cost is {cost_variance_pct:+.1f}% vs budget"),
        _part("sales_velocity", "Sales velocity", w["sales_velocity"], min(sold_vs_plan, 1.0),
              f"Sold {round(sold_vs_plan * 100)}% of the plan for this stage"),
        _part("collection_efficiency", "Collections", w["collection_efficiency"],
              linear(100 - collection_efficiency, 0, 20), f"{collection_efficiency:.1f}% of due demands collected"),
        _part("open_high_risks", "Open high risks", w["open_high_risks"], max(0.0, 1 - 0.5 * open_high_risks),
              f"{open_high_risks} open high risks"),
    ]
    return {"score": _total(parts), "parts": parts}


def project_stats(s, project: Project) -> dict:
    """Sold %, construction %, collections and health for one project."""
    def build():
        units = s.kids(Unit, "project_id", project.id)
        sold = [u for u in units if u.id in s.unit_booking]
        towers = s.kids(Tower, "project_id", project.id)
        stages = [m for t in towers for m in s.kids(ConstructionMilestone, "tower_id", t.id)]
        open_slips = [s.slip(m) for m in stages if m.id in s.delayed]
        done_slips = [s.slip(m) for m in stages if m.actual_date]
        slip = max(open_slips) if open_slips else (sum(done_slips) / len(done_slips) if done_slips else 0)
        budgets = s.kids(ProjectBudget, "project_id", project.id)
        budget = sum(num(b.budget_amount) for b in budgets)
        variance = 100 * (sum(num(b.actual_amount) for b in budgets) - budget) / budget if budget else 0.0
        demands = [d for u in sold for d in s.demands(s.unit_booking[u.id])]
        efficiency = s.efficiency(demands)
        expected = min(0.95, (s.today - project.launch_date).days / 1000 + 0.1)  # plan: sell out over about 3 years
        sold_pct = len(sold) / len(units) if units else 0
        risks = sum(1 for r in s.all(Risk) if r.severity == "high" and r.status != "resolved"
                    and any(e["type"] == "project" and e["id"] == str(project.id) for e in r.entity_refs_json))
        health = project_health(slip, variance, sold_pct / expected, efficiency if efficiency is not None else 100, risks)
        return {"units": len(units), "sold": len(sold), "sold_pct": round(100 * sold_pct, 1),
                "construction_pct": round(sum(num(m.percent_complete) for m in stages) / len(stages), 1) if stages else None,
                "collection_efficiency": efficiency, "cost_variance_pct": round(variance, 1), "slip_days": round(slip),
                "health": health}
    return s.memo(("project", project.id), build)


# ---------- team numbers used by scorecards and risks ----------
def sales_stats(s) -> dict:
    """Per sales person: bookings, site visits done, conversion, idle negotiations. Plus the team conversion."""
    def build():
        stall = CFG["sales"]["stalled_negotiation_days"]
        people = {}
        for emp in s.all(Employee):
            if emp.role_title in SALES_ROLES:
                bookings = s.kids(Booking, "employee_id", emp.id)
                visits = [v for v in s.kids(SiteVisit, "employee_id", emp.id) if v.status == "done"]
                idle = [lead for lead in s.kids(Lead, "owner_employee_id", emp.id)
                        if lead.stage == "negotiation" and s.idle_days(lead) >= stall]
                people[emp.id] = {"bookings": bookings, "visits": visits, "idle": idle,
                                  "conversion": 100 * len(bookings) / len(visits) if visits else 0.0,
                                  "idle_value": sum(num(lead.budget_max) for lead in idle)}
        total_visits = sum(len(p["visits"]) for p in people.values())
        team = 100 * sum(len(p["bookings"]) for p in people.values()) / total_visits if total_visits else 0.0
        return {"people": people, "team_conversion": team}
    return s.memo("sales_stats", build)


def rm_stats(s) -> dict:
    """Per relationship manager: active buyers, open queries, collection efficiency, reply time."""
    def build():
        people = {}
        for customer in s.active_customers:
            people.setdefault(customer.rm_employee_id, {"buyers": []})["buyers"].append(customer)
        for stats in people.values():
            demands, hours, queries = [], [], 0
            for customer in stats["buyers"]:
                demands += [d for b in s.bookings_of(customer.id) for d in s.demands(b)]
                queries += len(s.open_queries(customer.id))
                for item in s.kids(CustomerInteraction, "customer_id", customer.id):
                    if item.direction == "inbound" and item.needs_reply:
                        if item.replied_at:
                            hours.append((item.replied_at - item.occurred_at).total_seconds() / 3600)
                        else:  # still waiting: count the time so far
                            hours.append((s.today - to_date(item.occurred_at)).days * 24)
            stats.update(open_queries=queries, efficiency=s.efficiency(demands),
                         response_hours=round(sum(hours) / len(hours), 1) if hours else 0.0)
        average = sum(len(p["buyers"]) for p in people.values()) / len(people) if people else 0
        return {"people": people, "average_buyers": average}
    return s.memo("rm_stats", build)


# ---------- employee scorecard ----------
def scorecard(role_group: str, parts: list[tuple]) -> dict:
    """parts: (key, label, target, actual, achievement 0..1, kind). Weights come from the config."""
    weights = CFG["employee_scorecard"]["roles"][role_group]
    rows = [{"key": key, "label": label, "target": target, "actual": actual, "kind": kind, "weight": weights[key],
             "achievement_pct": round(100 * min(max(share, 0.0), 1.0)),
             "points": round(weights[key] * min(max(share, 0.0), 1.0), 1)}
            for key, label, target, actual, share, kind in parts]
    score = round(sum(r["points"] for r in rows))
    return {"role_group": role_group, "score": score, "parts": rows,
            "needs_attention": score < CFG["employee_scorecard"]["attention_below_pct"],
            "formula": "Score = sum of (weight x achievement). Achievement is actual vs target, capped at 100%."}


def employee_scorecard(s, emp: Employee) -> dict:
    def target(metric, default):
        for t in s.kids(EmployeeTarget, "employee_id", emp.id):
            if t.metric == metric and t.period_start <= s.today <= t.period_end:
                return num(t.target_value)
        return default

    def build():
        if emp.role_title in SALES_ROLES:
            stats, me = sales_stats(s), sales_stats(s)["people"][emp.id]
            recent = lambda day: 0 <= (s.today - to_date(day)).days < 90  # noqa: E731
            bookings = sum(recent(b.booked_on) for b in me["bookings"])
            visits = sum(recent(v.scheduled_at) for v in me["visits"])
            t_book, t_visit = target("bookings", 9), target("site_visits", 75)
            return scorecard("sales", [
                ("bookings_vs_target", "Bookings, last 90 days", t_book, bookings, bookings / t_book, "number"),
                ("site_visits", "Site visits, last 90 days", t_visit, visits, visits / t_visit, "number"),
                ("conversion", "Visit-to-booking conversion", round(stats["team_conversion"], 1),
                 round(me["conversion"], 1), me["conversion"] / stats["team_conversion"], "percent"),
                ("stalled_deals", "Stalled negotiations", 0, len(me["idle"]), 1 - len(me["idle"]) / 5, "number"),
            ])
        if emp.role_title == "Relationship Manager":
            stats = rm_stats(s)
            me = stats["people"].get(emp.id, {"buyers": [], "open_queries": 0, "efficiency": None, "response_hours": 0})
            eff, hours, cap = me["efficiency"] or 0, me["response_hours"], stats["average_buyers"] * 1.2
            t_eff, t_hours = target("collection_efficiency_pct", 90), target("response_hours", 24)
            return scorecard("rm_crm", [
                ("collection_efficiency", "Collection efficiency", t_eff, eff, eff / t_eff, "percent"),
                ("avg_response_time", "Average reply time (hours)", t_hours, hours,
                 t_hours / hours if hours else 1, "number"),
                ("open_queries", "Open buyer queries", 0, me["open_queries"], 1 - me["open_queries"] / 5, "number"),
                ("buyers_handled", "Buyers handled", round(cap), len(me["buyers"]),
                 cap / len(me["buyers"]) if len(me["buyers"]) > cap else 1, "number"),
            ])
        if emp.role_title in SITE_ROLES:
            owned = s.kids(ConstructionMilestone, "owner_employee_id", emp.id)
            done = [m for m in owned if m.actual_date]
            on_time = 100 * sum(s.slip(m) <= ON_TIME_GRACE_DAYS for m in done) / len(done) if done else 100.0
            issues = sum(q.status == "open" for q in s.kids(QualityIssue, "owner_employee_id", emp.id))
            t_time = target("milestones_on_time_pct", 85)
            return scorecard("site", [
                ("milestones_on_time", "Milestones on time", t_time, round(on_time), on_time / t_time, "percent"),
                ("open_quality_issues", "Open quality issues", 0, issues, 1 - issues / 5, "number"),
                ("milestones_owned", "Milestones owned", len(owned), len(owned), 1, "number"),
            ])
        tasks = s.kids(Task, "owner_employee_id", emp.id)
        late = sum(t.status == "open" and t.due_on < s.today for t in tasks)
        return scorecard("default", [("tasks_on_time", "Overdue tasks", 0, late, 1 - late / 5, "number")])
    return s.memo(("scorecard", emp.id), build)
