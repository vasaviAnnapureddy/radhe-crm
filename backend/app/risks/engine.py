"""Risk rule engine. Reads config/risk_rules.yaml and returns the risks found in the data.

Each risk keeps facts ("Observed") apart from the suggested action, and links to the entities involved.
The seed stores the result in the `risks` table; the admin can then change a risk's status.
"""
from app.core.config import load_config
from app.db.models import (
    Booking, ChannelPartner, ConstructionMilestone, Contractor, CpCommission, Customer, Employee,
    InteriorProject, Project, Tower, Unit,
)
from app.scoring.scores import customer_health, rm_stats, sales_stats
from app.services.common import fact, inr, ref
from app.services.snapshot import num

RULES = {rule["id"]: rule for rule in load_config("risk_rules.yaml")["rules"]}


def _risk(rule_id: str, severity: str, impact: float, facts: list, refs: list, owner=None, **words) -> dict:
    rule = RULES[rule_id]
    return {"rule_id": rule_id, "category": rule["category"], "severity": severity,
            "title": rule["title"].format(**words), "suggested_action": rule["suggested_action"].format(**words),
            "facts_json": {"impact": round(impact), "items": facts},
            "entity_refs_json": [r for r in refs if r], "owner_employee_id": owner}


def overdue_60_plus(s, min_days: int = 60) -> dict:
    """customer id -> (rupees overdue, worst days) for buyers overdue at least `min_days`."""
    out = {}
    for customer in s.active_customers:
        amount, days = s.customer_overdue(customer.id)
        if days >= min_days:
            late = [d for b in s.bookings_of(customer.id) for d in s.demands(b) if s.late(d) >= min_days]
            out[customer.id] = (sum(s.left(d) for d in late), days)
    return out


def possession_soon(s, within_days: int) -> list:
    """(tower, buyers without an interior package) for towers handing over soon."""
    with_package = {p.customer_id for p in s.all(InteriorProject)}
    out = []
    for stage in s.all(ConstructionMilestone):
        days = (stage.planned_date - s.today).days
        if stage.type == "handover" and stage.actual_date is None and days <= within_days:
            buyers = {s.unit_booking[u.id].customer_id for u in s.kids(Unit, "tower_id", stage.tower_id)
                      if u.id in s.unit_booking}
            out.append((s.one(Tower, stage.tower_id), [s.one(Customer, c) for c in buyers - with_package]))
    return out


def detect(s) -> list[dict]:
    risks = []
    p = {rule_id: rule.get("params", {}) for rule_id, rule in RULES.items()}

    # 1. A late construction stage that blocks demands
    rule = p["milestone_slip_blocks_demands"]
    for stage in s.delayed.values():
        blocked = s.blocked(stage)
        amount, slip = sum(num(d.amount) for d in blocked), s.slip(stage)
        if slip > rule["min_slip_days"] and amount > rule["min_blocked_amount"]:
            tower, contractor = s.one(Tower, stage.tower_id), s.one(Contractor, stage.contractor_id)
            project = s.one(Project, tower.project_id)
            risks.append(_risk(
                "milestone_slip_blocks_demands", "high", amount,
                [fact("Slip", slip, "days"), fact("Demands blocked", amount, "money"),
                 fact("Bookings affected", len({d.booking_id for d in blocked}), "number"),
                 fact("Contractor", contractor.name if contractor else "-"), fact("Cause", stage.delay_cause or "-")],
                [ref("tower", tower, f"{project.name} {tower.name}"),
                 ref("milestone", stage, f"{stage.type.replace('slab_', '').replace('_', ' ')}th floor slab" if stage.type.startswith("slab_") else stage.type.replace("_", " ").capitalize()),
                 ref("contractor", contractor), ref("project", project)],
                owner=stage.owner_employee_id, tower=tower.name, blocked_amount=inr(amount),
                contractor=contractor.name if contractor else "the contractor"))

    # 2. Buyers overdue 60+ days, and 3. many of them waiting on one bank
    late = overdue_60_plus(s)
    waiting = {}
    for customer_id, (amount, days) in late.items():
        customer = s.one(Customer, customer_id)
        booking = max(s.bookings_of(customer_id), key=lambda b: s.booking_overdue(b)[1])
        loan = s.loan(booking)
        severity = next(band["severity"] for band in RULES["buyer_overdue"]["severity_by_days"] if days >= band["min_days"])
        risks.append(_risk(
            "buyer_overdue", severity, amount,
            [fact("Overdue", amount, "money"), fact("Days overdue", days, "days"),
             fact("Loan", f"{loan.bank}, {loan.status.replace('_', ' ')}" if loan else "No loan")],
            [ref("customer", customer), ref("unit", s.unit(booking))],
            owner=customer.rm_employee_id, customer=customer.name, overdue_amount=inr(amount), days=days,
            bank=loan.bank if loan else "the bank"))
        if loan and loan.status == "awaiting_disbursement":
            waiting.setdefault(loan.bank, []).append(customer)
    for bank, customers in waiting.items():
        if len(customers) >= p["bank_disbursement_bottleneck"]["min_buyers_same_bank"]:
            total = sum(amount for amount, _ in late.values())
            risks.append(_risk(
                "bank_disbursement_bottleneck", "high", total,
                [fact("Buyers overdue 60+ days", len(late), "number"), fact("Total overdue 60+ days", total, "money"),
                 fact(f"Waiting on {bank}", len(customers), "number"),
                 fact("Their overdue amount", sum(late[c.id][0] for c in customers), "money")],
                [ref("customer", c) for c in customers], count=len(customers), bank=bank))

    # 4. A buyer with an open query and no contact from us
    rule = p["buyer_query_unanswered"]
    for customer in s.active_customers:
        queries, last = s.open_queries(customer.id), s.last_contact(customer.id)
        days = (s.today - last).days if last else 999
        if queries and days > rule["no_contact_days"]:
            health = customer_health(s, customer)["score"]
            rm = s.one(Employee, customer.rm_employee_id)
            unpaid = sum(num(b.agreement_value) - s.booking_paid(b) for b in s.bookings_of(customer.id))
            risks.append(_risk(
                "buyer_query_unanswered", "high" if health < rule["high_if_health_below"] else "medium", unpaid,
                [fact("Unanswered queries", len(queries), "number"), fact("Days since we contacted them", days, "days"),
                 fact("Buyer health", health, "score"), fact("Still to be collected", unpaid, "money")],
                [ref("customer", customer), ref("employee", rm)], owner=rm.id, customer=customer.name, days=days,
                rm=rm.name))

    # 5. Idle negotiations, and 8. low conversion
    sales = sales_stats(s)
    idle_rule, conv_rule = p["negotiation_idle_high_value"], p["sales_low_conversion"]
    for emp_id, me in sales["people"].items():
        emp = s.one(Employee, emp_id)
        if me["idle"] and me["idle_value"] > idle_rule["min_value"]:
            risks.append(_risk(
                "negotiation_idle_high_value", "high", me["idle_value"],
                [fact("Idle negotiations", len(me["idle"]), "number"), fact("Pipeline at risk", me["idle_value"], "money"),
                 fact("Longest idle", max(s.idle_days(lead) for lead in me["idle"]), "days")],
                [ref("employee", emp)] + [ref("lead", lead) for lead in me["idle"]], owner=emp_id,
                count=len(me["idle"]), idle_days=idle_rule["idle_days"], value=inr(me["idle_value"]), owner_name=emp.name))
        if (len(me["visits"]) >= conv_rule["min_site_visits"]
                and me["conversion"] < conv_rule["conversion_ratio"] * sales["team_conversion"]):
            risks.append(_risk(
                "sales_low_conversion", "medium", me["idle_value"],
                [fact("Conversion", round(me["conversion"], 1), "percent"),
                 fact("Team conversion", round(sales["team_conversion"], 1), "percent"),
                 fact("Site visits done", len(me["visits"]), "number"), fact("Bookings", len(me["bookings"]), "number")],
                [ref("employee", emp)], owner=emp_id, employee=emp.name, conversion=round(me["conversion"], 1),
                team_conversion=round(sales["team_conversion"], 1)))

    # 6. Homes unsold for a long time
    rule = p["unit_unsold_ageing"]
    for project in s.all(Project):
        old = [u for u in s.kids(Unit, "project_id", project.id)
               if u.status == "available" and (s.today - u.listed_on).days > rule["min_days_unsold"]]
        if old:
            value = sum(s.price(u) for u in old)
            risks.append(_risk(
                "unit_unsold_ageing", "medium", value,
                [fact("Units", len(old), "number"), fact("Value locked", value, "money"),
                 fact("Oldest", max((s.today - u.listed_on).days for u in old), "days"),
                 fact("Facing", ", ".join(sorted({u.facing for u in old}))),
                 fact("Floors", f"{min(u.floor or 0 for u in old)} to {max(u.floor or 0 for u in old)}")],
                [ref("project", project)] + [ref("unit", u) for u in old], count=len(old), project=project.name,
                min_days_unsold=rule["min_days_unsold"]))

    # 7. An overloaded relationship manager
    rms = rm_stats(s)
    for emp_id, me in rms["people"].items():
        if len(me["buyers"]) > p["rm_workload_high"]["workload_ratio"] * rms["average_buyers"]:
            emp = s.one(Employee, emp_id)
            risks.append(_risk(
                "rm_workload_high", "medium", 0,
                [fact("Active buyers", len(me["buyers"]), "number"),
                 fact("Team average", round(rms["average_buyers"]), "number"),
                 fact("Open buyer queries", me["open_queries"], "number")],
                [ref("employee", emp)], owner=emp_id, employee=emp.name, count=len(me["buyers"]),
                average=round(rms["average_buyers"])))

    # 9. Channel partner commission pending
    rule = p["cp_commission_pending"]
    for partner in s.all(ChannelPartner):
        pending = [c for c in s.kids(CpCommission, "channel_partner_id", partner.id)
                   if c.paid_on is None and (s.today - c.due_on).days >= rule["min_pending_days"]]
        if pending:
            amount = sum(num(c.amount) for c in pending)
            villas = [b for b in s.active_bookings if b.booked_on.year == s.today.year
                      and s.one(Project, s.unit(b).project_id).type == "villas"]
            share = round(100 * sum(b.channel_partner_id == partner.id for b in villas) / len(villas)) if villas else 0
            days = max((s.today - c.due_on).days for c in pending)
            risks.append(_risk(
                "cp_commission_pending", "medium", amount,
                [fact("Commissions pending", len(pending), "number"), fact("Amount pending", amount, "money"),
                 fact("Oldest pending", days, "days"), fact("Share of this year's villa bookings", share, "percent")],
                [ref("partner", partner)] + [ref("booking", s.one(Booking, c.booking_id),
                                             f"Booking {s.unit(s.one(Booking, c.booking_id)).unit_no}") for c in pending],
                partner=partner.firm_name, days=days, amount=inr(amount)))

    # 10. Interiors upsell (an opportunity, shown as low severity)
    packages = s.all(InteriorProject)
    average = sum(num(x.value) for x in packages) / len(packages) if packages else 0
    for tower, buyers in possession_soon(s, p["interiors_upsell"]["possession_within_days"]):
        if buyers:
            project = s.one(Project, tower.project_id)
            risks.append(_risk(
                "interiors_upsell", "low", len(buyers) * average,
                [fact("Buyers without a package", len(buyers), "number"),
                 fact("Average package value", average, "money"), fact("Opportunity", len(buyers) * average, "money")],
                [ref("tower", tower, f"{project.name} {tower.name}")] + [ref("customer", c) for c in buyers],
                count=len(buyers), value=inr(len(buyers) * average)))

    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(risks, key=lambda r: (order[r["severity"]], -r["facts_json"]["impact"]))
