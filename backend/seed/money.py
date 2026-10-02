"""Payment plans, demands (requests to pay), receipts (money in) and home loans."""
from datetime import timedelta
from decimal import Decimal

from app.db.models import Demand, HomeLoan, PaymentPlan, PlanMilestone, Receipt
from seed.stories import BOTTLENECK_BANK, BOTTLENECK_BUYERS, KARTHIK, OVERDUE_AMOUNT, OVERDUE_BUYERS
from seed.world import rupees

# plan -> (milestone name, percent, construction stage that triggers it, days after booking if time-based)
PLANS = {
    "Construction-linked plan": [
        ("Booking amount", 10, None, 0), ("Agreement", 10, None, 30), ("Foundation complete", 10, "foundation", None),
        ("5th floor slab", 7.5, "slab_5", None), ("10th floor slab", 7.5, "slab_10", None),
        ("14th floor slab", 5, "slab_14", None), ("18th floor slab", 10, "slab_18", None),
        ("Top floor slab", 10, "top_slab", None), ("Brickwork complete", 10, "brickwork", None),
        ("Finishing complete", 10, "finishing", None), ("Possession", 10, "handover", None)],
    "20:80 possession-linked plan": [
        ("Booking amount", 10, None, 0), ("Agreement", 10, None, 30), ("Possession", 80, "handover", None)],
    "Down payment plan": [
        ("Booking amount", 10, None, 0), ("Agreement", 80, None, 45), ("Possession", 10, "handover", None)],
    "Villa instalment plan": [
        ("Booking amount", 10, None, 0), ("Agreement", 20, None, 30), ("Instalment 1", 20, None, 120),
        ("Instalment 2", 20, None, 240), ("Instalment 3", 20, None, 360), ("Possession", 10, None, 480)],
    "Plot plan": [("Booking amount", 20, None, 0), ("Agreement", 30, None, 30), ("Registration", 50, None, 90)],
}
BANKS = [BOTTLENECK_BANK, "Godavari Bank", "Krishna Valley Bank", "Charminar Co-operative Bank",
         "Golconda Finance Bank", "Musi Urban Bank", "Kakatiya Housing Finance", "Nizam Capital Bank"]  # all fictional
# STORY 6: buyers who stopped paying after one of these stages. Their demands are now 71 to 106 days overdue.
OVERDUE_STAGES = [("Radhe Skyline", "Tower A", "slab_14"), ("Radhe Skyline", "Tower C", "slab_5"),
                  ("Radhe Greens", "Tower C", "top_slab")]


def add_plans(w) -> None:
    w.plans, w.plan_offset = {}, {}
    for name, steps in PLANS.items():
        plan = w.add(PaymentPlan(name=name))
        milestones = []
        for seq, (step, percent, stage, offset) in enumerate(steps, start=1):
            pm = w.add(PlanMilestone(payment_plan_id=plan.id, seq=seq, name=step, percent=Decimal(str(percent)),
                                     construction_milestone_type=stage))
            w.plan_offset[pm.id] = offset
            milestones.append(pm)
        w.plans[name] = (plan, milestones)


def add_payments(w) -> None:
    rng = w.rng
    plan_steps = {plan.id: steps for plan, steps in w.plans.values()}
    receipts, paid_by = {}, {}  # demand id -> receipt, demand id -> its deal

    for deal in w.deals:
        booking = deal.booking
        is_karthik = deal.customer.name == KARTHIK
        if deal.project.type != "plots" and not deal.cancelled and not is_karthik and rng.random() < 0.55:
            deal.loan = w.add(HomeLoan(booking_id=booking.id, bank=rng.choice(BANKS), status="disbursing",
                                       sanctioned_amount=rupees(booking.agreement_value * Decimal("0.75")),
                                       disbursed_amount=Decimal(0)))

        for pm in plan_steps[booking.payment_plan_id]:
            if deal.cancelled and pm.seq > 1:
                break  # a cancelled booking only ever paid the booking amount
            demand = w.add(Demand(booking_id=booking.id, plan_milestone_id=pm.id, construction_milestone_id=None,
                                  amount=rupees(booking.agreement_value * pm.percent / 100), raised_on=None,
                                  due_on=None, status="not_raised", reminders_sent=0))
            stage = None
            if pm.construction_milestone_type and deal.unit.tower_id:
                stage = w.milestones[(deal.unit.tower_id, pm.construction_milestone_type)]
                if stage.actual_date is None:  # the stage is not finished, so this demand cannot be raised yet
                    demand.construction_milestone_id = stage.id
                    continue
                raised = max(stage.actual_date + timedelta(days=3), booking.booked_on + timedelta(days=30))
            else:
                raised = booking.booked_on + timedelta(days=w.plan_offset[pm.id] or 0)
            if raised > w.today:
                continue
            if stage:
                demand.construction_milestone_id = stage.id
            due = raised + timedelta(days=7 if pm.seq == 1 else 21)
            demand.raised_on, demand.due_on, demand.status = raised, due, "raised"

            days_over = (w.today - due).days
            if days_over < 0:
                pays = rng.random() < 0.3  # some buyers pay before the due date
            elif deal.cancelled or is_karthik:
                pays = True
            else:  # a few small recent demands are late; nothing here is ever 60+ days late (story 6 adds those)
                roll, chance = rng.random(), (0.04 if days_over <= 30 else 0.02 if days_over <= 58 else 0)
                pays = roll >= chance or demand.amount > 3_000_000
            if not pays:
                if days_over >= 0:
                    demand.status, demand.reminders_sent = "overdue", days_over // 15 + 1
                continue

            late = pm.seq in (3, 5) if is_karthik else rng.random() < 0.2  # STORY 2: Karthik paid 2 of 5 late
            received = due + timedelta(days=rng.randint(5, 25)) if late else due - timedelta(days=rng.randint(0, 6))
            received = min(max(received, raised), w.today)
            by_loan = bool(deal.loan) and pm.seq > 2 and rng.random() < 0.7
            demand.status = "paid"
            receipts[demand.id] = w.add(Receipt(
                demand_id=demand.id, amount=demand.amount, received_on=received, from_bank_loan=by_loan,
                mode="loan_disbursement" if by_loan else rng.choice(["neft", "neft", "cheque", "upi"])))
            paid_by[demand.id] = (demand, deal, stage)

    dropped = _plant_bank_bottleneck(w, receipts, paid_by)

    disbursed = {}  # loan totals follow the receipts that came from the bank
    for demand_id, receipt in receipts.items():
        if receipt.from_bank_loan and id(receipt) not in dropped:
            deal = paid_by[demand_id][1]
            disbursed[id(deal)] = disbursed.get(id(deal), Decimal(0)) + receipt.amount
    for deal in w.deals:
        if deal.loan:
            from_bank = disbursed.get(id(deal), Decimal(0))
            deal.loan.disbursed_amount = from_bank
            if deal.loan.status != "awaiting_disbursement":
                deal.loan.status = ("closed" if deal.booking.status == "possession"
                                    else "disbursing" if from_bank else "sanctioned")


def _plant_bank_bottleneck(w, receipts, paid_by) -> set:
    """STORY 6: 18 buyers are 60+ days overdue for about Rs 4.2 Cr; 6 of them wait on the same bank."""
    rng = w.rng
    stages = {w.milestones[(w.towers[(p, t)].id, kind)].id for p, t, kind in OVERDUE_STAGES}
    bookings_per_customer = {}
    for deal in w.deals:
        bookings_per_customer[deal.customer.id] = bookings_per_customer.get(deal.customer.id, 0) + 1
    pool = [(demand, deal) for demand, deal, stage in paid_by.values()
            if stage is not None and stage.id in stages and bookings_per_customer[deal.customer.id] == 1
            and demand.raised_on == stage.actual_date + timedelta(days=3)]
    rng.shuffle(pool)
    picks, spare = pool[:OVERDUE_BUYERS], sorted(pool[OVERDUE_BUYERS:], key=lambda x: x[0].amount)
    while sum(d.amount for d, _ in picks) < OVERDUE_AMOUNT:  # swap the smallest for a bigger one
        picks.remove(min(picks, key=lambda x: x[0].amount))
        picks.append(spare.pop())

    excess = sum(d.amount for d, _ in picks) - Decimal(int(OVERDUE_AMOUNT))
    dropped = set()
    for n, (demand, deal) in enumerate(picks):
        receipt = receipts[demand.id]
        part_paid = min(excess, demand.amount * Decimal("0.6")).quantize(Decimal(1))
        if part_paid > 0:  # a part payment brings the total down to the target
            receipt.amount, excess = part_paid, excess - part_paid
        else:
            dropped.add(id(receipt))
        demand.status = "overdue"
        demand.reminders_sent = (w.today - demand.due_on).days // 15 + 1
        if n < BOTTLENECK_BUYERS:
            if deal.loan is None:
                deal.loan = w.add(HomeLoan(booking_id=deal.booking.id, disbursed_amount=Decimal(0),
                                           sanctioned_amount=rupees(deal.booking.agreement_value * Decimal("0.75"))))
            deal.loan.bank, deal.loan.status = BOTTLENECK_BANK, "awaiting_disbursement"
    w.rows = [row for row in w.rows if id(row) not in dropped]
    return dropped
