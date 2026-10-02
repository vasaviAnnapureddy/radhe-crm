"""After the sale: buyer interactions, service tickets, interior projects and staff tasks."""
from datetime import timedelta
from decimal import Decimal

from app.db.models import CustomerInteraction, InteriorProject, ServiceTicket, Task
from seed.stories import KARTHIK_EMAIL_DAYS_AGO, KARTHIK_LAST_CONTACT_DAYS_AGO, LAKH, UPSELL_BUYERS

OUTBOUND = ["Shared construction progress photos", "Called to confirm the payment schedule",
            "Sent the demand letter and receipt", "Shared the possession timeline", "Follow-up call on documents"]
INBOUND = ["Asked about the possession date", "Asked for a copy of the agreement", "Query on loan disbursement",
           "Asked for a site visit slot", "Query on the interiors package"]
SNAGS = ["Bathroom tap leaking", "Hairline crack in bedroom wall", "Balcony door not closing properly",
         "Kitchen tile chipped", "Switchboard loose", "Paint patch in living room"]
COMPLAINTS = ["Delay in sharing the receipt", "Car park allotment not confirmed", "No update on construction progress",
              "Wrong amount in the demand letter"]
PACKAGES = [("Essential", 9), ("Signature", 14), ("Signature", 14), ("Bespoke", 22), ("Signature", 14)]  # Rs lakh
TASKS = ["Send demand letter", "Collect KYC documents", "Follow up on loan sanction", "Schedule site visit",
         "Prepare agreement draft", "Update milestone photos", "Close quality issue", "Call buyer about overdue amount",
         "Share cost sheet", "Verify registration papers"]


def add_care(w) -> None:
    _interactions(w)
    _tickets(w)
    _interiors(w)
    _tasks(w)


def _say(w, customer, ago, direction, summary, channel=None, open_query=False):
    when = w.at(ago)
    inbound = direction == "inbound"
    w.add(CustomerInteraction(
        customer_id=customer.id, employee_id=customer.rm_employee_id, direction=direction, summary=summary,
        channel=channel or w.rng.choice(["call", "email", "whatsapp"]), occurred_at=when, needs_reply=inbound,
        replied_at=when + timedelta(hours=w.rng.randint(1, 30)) if inbound and not open_query else None))


def _interactions(w) -> None:
    rng = w.rng
    others = [c for c in w.active_customers if c is not w.karthik]
    # Buyers with an open query and no contact from us for 21+ days. Four of the five are Sneha's (she is overloaded).
    # Only buyers who booked 40+ days ago can have gone 24 to 35 days without contact.
    long_standing = [c for c in others if w.first_ago[c.id] >= 40]
    sneha_others = [c for c in w.sneha_buyers if c in long_standing]
    not_sneha = [c for c in long_standing if c not in w.sneha_buyers]
    silent = {c.id: rng.randint(24, 35) for c in rng.sample(sneha_others, 4) + rng.sample(not_sneha, 1)}
    silent[w.karthik.id] = KARTHIK_LAST_CONTACT_DAYS_AGO
    recent_query = {c.id for c in rng.sample([c for c in others if c.id not in silent], 20)}
    w.waiting_buyers = [c for c in w.active_customers if c.id in silent or c.id in recent_query]

    for customer in w.active_customers:
        first_ago = w.first_ago[customer.id]
        last_contact = min(silent.get(customer.id, rng.randint(1, 18)), first_ago)
        for _ in range(rng.randint(2, 4)):  # older history
            ago = rng.randint(last_contact, max(last_contact, first_ago))
            direction = rng.choice(["inbound", "outbound"])
            _say(w, customer, ago, direction, rng.choice(INBOUND if direction == "inbound" else OUTBOUND))
        _say(w, customer, last_contact, "outbound", rng.choice(OUTBOUND))

        if customer is w.karthik:  # STORY 2: three emails about possession, none answered
            for ago in KARTHIK_EMAIL_DAYS_AGO:
                _say(w, customer, ago, "inbound", "Asked for the revised possession date for Tower B",
                     channel="email", open_query=True)
        elif customer.id in silent:
            _say(w, customer, rng.randint(9, 15), "inbound", rng.choice(INBOUND), open_query=True)
        elif customer.id in recent_query:
            _say(w, customer, min(rng.randint(1, 6), last_contact), "inbound", rng.choice(INBOUND), open_query=True)

    active_ids = {c.id for c in w.active_customers}
    for deal in w.deals:
        if deal.customer.id not in active_ids:
            _say(w, deal.customer, max(deal.ago - 40, 1), "inbound", "Asked to cancel the booking")
            _say(w, deal.customer, max(deal.ago - 45, 0), "outbound", "Confirmed cancellation and refund steps")


def _tickets(w) -> None:
    rng = w.rng

    def ticket(deal, category, text, raised_ago, is_open, sla_hours):
        days_to_fix = rng.choice([1, 2, 2, 3, 5, 9])  # 5 and 9 days break a 72-hour SLA
        w.add(ServiceTicket(
            unit_id=deal.unit.id, customer_id=deal.customer.id, category=category, description=text,
            status="open" if is_open else "resolved", raised_on=w.ago(raised_ago), sla_hours=sla_hours,
            resolved_on=None if is_open else w.ago(max(raised_ago - days_to_fix, 0)),
            assigned_employee_id=deal.customer.rm_employee_id))

    handed_over = [d for d in w.deals if d.booking.status == "possession"]
    for deal in handed_over:  # snags found after handover at Greens Tower A
        for _ in range(rng.choice([0, 1, 1, 2])):
            ticket(deal, "snag", rng.choice(SNAGS), rng.randint(20, 190), False, 72)
    for deal in rng.sample(handed_over, 15):
        ticket(deal, "snag", rng.choice(SNAGS), rng.randint(1, 12), True, 72)

    live = [d for d in w.deals if not d.cancelled and d.customer is not w.karthik]
    for deal in rng.sample(live, 40):
        ticket(deal, "complaint", rng.choice(COMPLAINTS), rng.randint(15, min(300, max(deal.ago, 16))), False, 48)
    for deal in rng.sample(live, 12):
        ticket(deal, "complaint", rng.choice(COMPLAINTS), rng.randint(1, 9), True, 48)
    karthik_deal = next(d for d in w.deals if d.customer is w.karthik)
    ticket(karthik_deal, "complaint", "No response on the revised possession date for Tower B", 10, True, 48)


def _interiors(w) -> None:
    rng = w.rng
    designers = w.staff["Interior Designer"]
    made = 0

    def project(deal, stage, start_ago):
        nonlocal made
        package, lakh = PACKAGES[made % len(PACKAGES)]
        w.add(InteriorProject(customer_id=deal.customer.id, unit_id=deal.unit.id, package=package,
                              designer_employee_id=designers[made % len(designers)].id, value=Decimal(lakh * LAKH),
                              stage=stage, start_date=w.ago(start_ago), target_date=w.ago(start_ago - 150)))
        made += 1

    greens = w.projects["Radhe Greens"]
    tower_a, tower_b = (w.towers[("Radhe Greens", t)].id for t in ("Tower A", "Tower B"))
    for deal in rng.sample([d for d in w.deals if d.unit.tower_id == tower_a], 55):
        project(deal, rng.choice(["execution", "handover", "done", "done"]), rng.randint(120, 190))
    # STORY 7: Greens Tower B hands over in about 4 months. All but 63 of its buyers have an interior package.
    soon = [d for d in w.deals if d.unit.tower_id == tower_b and d.project is greens]
    for deal in rng.sample(soon, len(soon) - UPSELL_BUYERS):
        project(deal, rng.choice(["design", "approval", "execution"]), rng.randint(10, 90))


def _tasks(w) -> None:
    """General office tasks for everyone, plus tasks tied to a real lead, buyer or tower for the people who own them."""
    rng = w.rng

    def task(owner_id, title, due_ago, done=None, kind=None, entity=None, priority=None):
        if done is None:  # most past tasks are done; a few are overdue
            done = rng.random() < (0.85 if due_ago > 0 else 0.25)
        w.add(Task(title=title, owner_employee_id=owner_id, entity_type=kind, entity_id=entity.id if entity else None,
                   priority=priority or rng.choice(["low", "medium", "medium", "high"]), due_on=w.ago(due_ago),
                   status="done" if done else "open"))

    everyone = [e for team in w.staff.values() for e in team]
    for _ in range(220):
        task(rng.choice(everyone).id, rng.choice(TASKS), rng.randint(-20, 25))

    # Sales: a follow-up for every negotiation. Stalled ones are already overdue.
    for lead, idle_days in w.negotiations:
        stalled = idle_days >= 14
        task(lead.owner_employee_id, f"Follow up with {lead.name}", rng.randint(1, 9) if stalled else -rng.randint(1, 6),
             done=False, kind="lead", entity=lead, priority="high" if stalled else "medium")

    # Relationship managers: reply to waiting buyers today, and three scheduled calls each in the coming week.
    for buyer in w.waiting_buyers:
        task(buyer.rm_employee_id, f"Reply to {buyer.name}'s query", rng.randint(0, 3), done=False, kind="customer",
             entity=buyer, priority="high")
    by_rm = {}
    for buyer in w.active_customers:
        by_rm.setdefault(buyer.rm_employee_id, []).append(buyer)
    for rm_id, buyers in by_rm.items():
        for buyer in rng.sample(buyers, min(3, len(buyers))):
            task(rm_id, f"Call with {buyer.name}: construction and payment update", -rng.randint(0, 7), done=False,
                 kind="customer", entity=buyer, priority="medium")

    # Site team: keep the stage they are working on up to date.
    for stage in w.milestones.values():
        if stage.actual_date is None and stage.percent_complete > 0:
            task(stage.owner_employee_id, f"Update progress photos: {stage.type.replace('_', ' ')}", -rng.randint(0, 4),
                 done=False, kind="milestone", entity=stage, priority="medium")
