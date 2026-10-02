"""Channel partners, 850 bookings with their customers, 4,000 leads, activities, site visits, commissions."""
from collections import Counter, defaultdict
from decimal import Decimal

from app.db.models import (
    Booking,
    ChannelPartner,
    CpCommission,
    Customer,
    Lead,
    LeadActivity,
    SiteVisit,
)
from seed.names import email_for, person
from seed.stories import (
    ARJUN,
    ARJUN_BOOKINGS,
    ARJUN_CONVERSION,
    ARJUN_IDLE_BUDGETS_CR,
    CR,
    DELAY_BLOCKED_AMOUNT,
    DELAY_BLOCKED_BOOKINGS,
    DELAY_PROJECT,
    DELAY_TOWER,
    KARTHIK,
    SKYWAY,
    SKYWAY_VILLA_SHARE,
    SNEHA,
    SNEHA_BUYERS,
    TOTAL_BOOKINGS,
    TOTAL_LEADS,
)
from seed.world import Deal, list_price, rupees

CLP, PLAN_20_80, PLAN_DOWN = "Construction-linked plan", "20:80 possession-linked plan", "Down payment plan"

# project, tower, bookings, how many of them cancelled, (newest, oldest) booking age in days. Totals: 850 and 36.
ALLOCATION = [
    ("Radhe Skyline", "Tower A", 130, 8, (5, 530)),
    ("Radhe Skyline", "Tower B", 75, 0, (5, 530)),
    ("Radhe Skyline", "Tower C", 95, 6, (5, 500)),
    ("Radhe Greens", "Tower A", 150, 0, (300, 540)),
    ("Radhe Greens", "Tower B", 110, 0, (60, 540)),
    ("Radhe Greens", "Tower C", 70, 6, (10, 500)),
    ("Radhe Aranya", "Tower 1", 35, 2, (3, 115)),
    ("Radhe Aranya", "Tower 2", 25, 2, (3, 115)),
    ("Radhe Vanam Villas", None, 70, 4, (10, 530)),
    ("Radhe Bhoomi", None, 90, 8, (10, 530)),
]
REPEAT_BUYERS = 16  # investors who already own a home and also buy a plot

CP_AREAS = ["Hitech", "Cyber", "Gachibowli", "Kondapur", "Madhapur", "Jubilee", "Banjara", "Kokapet", "Manikonda",
            "Nallagandla", "Tellapur", "Narsingi", "Miyapur", "Kukatpally", "Secunderabad", "Begumpet", "Ameerpet",
            "Uppal", "LB Nagar", "Kompally", "Shamshabad", "Attapur", "Mehdipatnam", "Somajiguda", "Himayatnagar",
            "Tarnaka", "Bachupally", "Nizampet", "Kollur"]
CP_KINDS = ["Realty", "Homes", "Property Consultants", "Estates", "Realtors", "Housing Advisors"]
SOURCES = ["Website", "Property portal", "Digital ads", "Walk-in", "Property expo", "Referral", "Corporate tie-up",
           "NRI roadshow"]
SOURCE_WEIGHTS = [18, 22, 15, 10, 6, 8, 3, 3]
NRI_PLACES = [("USA", "Dallas"), ("USA", "Bay Area"), ("UK", "London"), ("UAE", "Dubai"), ("Singapore", "Singapore")]
LOST_REASONS = ["Budget too low", "Bought from another builder", "Location not suitable", "Possession date too far",
                "Loan not approved", "Postponed the decision", "Not reachable"]
CANCEL_REASONS = ["Loan rejected", "Job change or relocation", "Family decision", "Financial difficulty",
                  "Moved to another project"]
ACTIVITY_NOTES = {"call": ["Intro call; shared brochure", "Follow-up call on pricing", "Discussed payment plan"],
                  "whatsapp": ["Sent floor plans and price sheet", "Shared site location and photos"],
                  "email": ["Emailed cost sheet", "Emailed the draft agreement"],
                  "meeting": ["Met at the sales office", "Met family at the model flat"],
                  "note": ["Wants a higher floor", "Comparing with a project nearby", "Spouse to decide"]}
VISIT_FEEDBACK = ["Liked the model flat", "Wants an east-facing home", "Asked for a better price", "Liked the clubhouse",
                  "Will come back with family", "Concerned about the possession date"]
TYPICAL_CR = {"Radhe Skyline": 3.3, "Radhe Greens": 2.3, "Radhe Aranya": 4.2, "Radhe Vanam Villas": 9.0, "Radhe Bhoomi": 2.0}
# stage, how many leads, (newest, oldest) age in days. "lost" takes whatever is left to reach 4,000.
OPEN_STAGES = [("new", 340, (0, 10)), ("contacted", 700, (3, 60)), ("visit_scheduled", 250, (5, 60)),
               ("visit_done", 360, (10, 150)), ("negotiation", 180, (20, 150)), ("blocked", 25, (5, 30))]


def add_sales(w) -> None:
    _partners(w)
    _bookings(w)
    _assign_rms(w)
    _open_leads(w)
    _site_visits(w)


def _partners(w) -> None:
    names = [SKYWAY] + [f"{area} {CP_KINDS[i % len(CP_KINDS)]}" for i, area in enumerate(CP_AREAS)]
    w.partners = [w.add(ChannelPartner(
        firm_name=name, contact_name=person(w), phone=w.phone(), status="active",
        city=w.rng.choice(["Hyderabad"] * 8 + ["Bengaluru", "Dubai"]),
        commission_pct=Decimal(str(w.rng.choice([1.5, 2.0, 2.0, 2.5]))),
    )) for name in names]


def _lead(w, owner, stage, created_ago, project, budget_cr, **extra) -> Lead:
    rng = w.rng
    name = extra.pop("name", None) or person(w)
    fields = dict(
        name=name, phone=w.phone(), email=email_for(name, rng.randint(10, 999)),
        source=rng.choices(SOURCES, SOURCE_WEIGHTS)[0], channel_partner_id=None,
        budget_min=rupees(budget_cr * CR * 0.85), budget_max=rupees(budget_cr * CR),
        preferred_config=rng.choice(sorted({u.config for u in w.units[project.id]})),
        preferred_project_id=project.id, country=rng.choice(NRI_PLACES)[0] if rng.random() < 0.12 else "India",
        owner_employee_id=owner.id, stage=stage, lost_reason=None, created_at=w.at(created_ago),
    )
    return w.add(Lead(**{**fields, **extra}))


def _activities(w, lead, owner, first_ago: int, last_ago: int, count: int) -> None:
    """`count` activities spread evenly between two dates; the last one lands on `last_ago`."""
    for i in range(count):
        ago = last_ago if count == 1 else round(first_ago - (first_ago - last_ago) * i / (count - 1))
        kind = w.rng.choice(list(ACTIVITY_NOTES))
        w.add(LeadActivity(lead_id=lead.id, employee_id=owner.id, type=kind,
                           summary=w.rng.choice(ACTIVITY_NOTES[kind]), occurred_at=w.at(ago)))


def _bookings(w) -> None:
    rng = w.rng
    arjun = w.by_name[ARJUN]
    others = [e for e in w.sales_team if e is not arjun]
    # STORY 3: Arjun closes only 12 of the 850 bookings; the rest are shared evenly.
    owners = [arjun] * ARJUN_BOOKINGS + [others[i % len(others)] for i in range(TOTAL_BOOKINGS - ARJUN_BOOKINGS)]
    rng.shuffle(owners)
    skyway, other_partners = w.partners[0], w.partners[1:]
    day_of_year = w.today.timetuple().tm_yday
    w.deals, w.visit_pool, w.booking_count, w.first_ago = [], defaultdict(list), Counter(), {}
    n = 0

    for project_name, tower_name, count, cancelled_count, (newest, oldest) in ALLOCATION:
        project = w.projects[project_name]
        tower = w.towers.get((project_name, tower_name))
        pool = [u for u in w.units[project.id]
                if (tower is None or u.tower_id == tower.id) and u.id not in w.protected_units]
        units = rng.sample(pool, count)
        agos = [rng.randint(newest, oldest) for _ in range(count)]
        first_cancelled = count - cancelled_count
        for i in range(first_cancelled, count):
            agos[i] = rng.randint(60, min(400, oldest))

        is_delay_tower = (project_name, tower_name) == (DELAY_PROJECT, DELAY_TOWER)
        if is_delay_tower:  # STORY 2: Karthik gets a 4 BHK here, booked 480 days ago
            k = next(i for i, u in enumerate(units) if u.config == "4 BHK")
            units[0], units[k] = units[k], units[0]
            agos[0] = 480

        skyway_picks = set()
        if project.type == "villas":  # STORY 4: Skyway brings 31% of this year's villa bookings
            this_year = [i for i in range(first_cancelled) if agos[i] < day_of_year]
            picks = rng.sample(this_year, round(SKYWAY_VILLA_SHARE * len(this_year)))
            skyway_picks = set(picks)
            for i in picks[:5]:  # old enough that their commission is now 45+ days late
                agos[i] = rng.randint(80, max(80, min(140, day_of_year - 1)))

        repeat_buyers = []
        if project.type == "plots":
            owners_of_homes = [d.customer for d in w.deals if not d.cancelled and d.customer.name != KARTHIK
                               and (d.project.type == "villas" or d.unit.unit_no.startswith("A-"))]
            repeat_buyers = rng.sample(owners_of_homes, REPEAT_BUYERS)

        tower_deals = []
        for i, (unit, ago) in enumerate(zip(units, agos)):
            cancelled = i >= first_cancelled
            owner = owners[n]
            n += 1
            w.booking_count[owner.id] += 1
            value = Decimal(int(round(float(list_price(unit)) * rng.uniform(0.96, 1.0), -3)))

            if project.type == "villas":
                plan = "Villa instalment plan"
            elif project.type == "plots":
                plan = "Plot plan"
            elif is_delay_tower:  # STORY 1: exactly 41 Tower B bookings are construction-linked
                plan = CLP if i < DELAY_BLOCKED_BOOKINGS else (PLAN_20_80 if i % 2 else PLAN_DOWN)
            else:
                plan = rng.choices([CLP, PLAN_20_80, PLAN_DOWN], [80, 12, 8])[0]

            if cancelled:
                status = "cancelled"
            elif (project_name, tower_name) == ("Radhe Greens", "Tower A"):
                status = "possession"
            elif ago > 150:
                status = "registered" if rng.random() < 0.7 else "agreement_signed"
            else:
                status = "agreement_signed" if ago > 30 else "booked"

            partner = skyway if i in skyway_picks else (rng.choice(other_partners) if rng.random() < 0.33 else None)
            is_karthik = is_delay_tower and i == 0
            if is_karthik:
                partner = None

            if i < len(repeat_buyers) and not cancelled:
                customer = repeat_buyers[i]
            else:
                name = KARTHIK if is_karthik else person(w, unique=True)
                roll = rng.random()
                country, city, kind = "India", "Hyderabad", "end_user"
                if is_karthik or roll < 0.22:
                    country, city = ("USA", "Dallas") if is_karthik else rng.choice(NRI_PLACES)
                    kind = "nri"
                elif project.type == "villas":
                    kind = "hni"
                elif project.type == "plots" or roll < 0.30:
                    kind = "investor"
                elif roll < 0.33:
                    kind = "corporate"
                created_ago = ago + rng.randint(20, 90)
                lead = _lead(w, owner, status, created_ago, project, float(value) / CR, name=name,
                             country=country, preferred_config=unit.config,
                             source="Channel partner" if partner else rng.choices(SOURCES, SOURCE_WEIGHTS)[0],
                             channel_partner_id=partner.id if partner else None,
                             lost_reason=None)
                _activities(w, lead, owner, created_ago, ago, rng.randint(3, 5))
                w.visit_pool[owner.id].append((lead, created_ago, ago))
                if is_karthik:  # a plain email, so his portal login is easy to remember
                    lead.email = email_for(name, "")
                customer = w.add(Customer(lead_id=lead.id, name=name, phone=lead.phone, email=lead.email, type=kind,
                                          is_nri=kind == "nri", country=country, city=city,
                                          rm_employee_id=owner.id))  # the real RM is set in _assign_rms
                if is_karthik:
                    w.karthik = customer
            w.first_ago[customer.id] = max(ago, w.first_ago.get(customer.id, 0))

            done = status in ("registered", "possession")
            booking = w.add(Booking(
                unit_id=unit.id, customer_id=customer.id, employee_id=owner.id,
                channel_partner_id=partner.id if partner else None, booked_on=w.ago(ago), agreement_value=value,
                payment_plan_id=w.plans[plan][0].id, status=status,
                cancel_reason=rng.choice(CANCEL_REASONS) if cancelled else None,
                agreement_on=w.ago(ago - 30) if status not in ("booked", "cancelled") else None,
                registered_on=w.ago(ago - 120) if done else None,
                possession_on=w.ago(rng.randint(150, 195)) if status == "possession" else None,
            ))
            deal = Deal(booking=booking, unit=unit, customer=customer, project=project, ago=ago, cancelled=cancelled)
            w.deals.append(deal)
            tower_deals.append(deal)

            if not cancelled:  # a cancelled home goes back on sale
                unit.status = {"registered": "registered", "possession": "handed_over"}.get(status, "booked")
                unit.status_changed_at = w.at(ago)
                unit.listed_on = w.ago(ago + rng.randint(20, 200))
                if partner:
                    due_ago = ago - 30
                    if partner is skyway:  # STORY 4: recent Skyway commissions are left unpaid
                        paid_ago = due_ago - rng.randint(5, 25) if due_ago > 120 else None
                    else:
                        paid_ago = due_ago - rng.randint(3, 30)
                    w.add(CpCommission(booking_id=booking.id, channel_partner_id=partner.id, due_on=w.ago(due_ago),
                                       amount=rupees(value * partner.commission_pct / 100),
                                       paid_on=w.ago(paid_ago) if paid_ago is not None and paid_ago >= 0 else None))

        if is_delay_tower:  # STORY 1: nudge prices so the blocked 5% demands add up to Rs 6.8 Cr
            linked = tower_deals[:DELAY_BLOCKED_BOOKINGS]
            factor = DELAY_BLOCKED_AMOUNT / (sum(float(d.booking.agreement_value) for d in linked) * 0.05)
            for d in linked:
                d.booking.agreement_value = Decimal(int(round(float(d.booking.agreement_value) * factor, -3)))


def _assign_rms(w) -> None:
    """STORY 2: Sneha Rao looks after 62 active buyers; the other 20 RMs share the rest (about 37 each)."""
    sneha = w.by_name[SNEHA]
    rest = [r for r in w.staff["Relationship Manager"] if r is not sneha]
    active = list({d.customer.id: d.customer for d in w.deals if not d.cancelled}.values())
    active_ids = {c.id for c in active}
    others = [c for c in active if c is not w.karthik]
    w.rng.shuffle(others)
    w.sneha_buyers = [w.karthik] + others[:SNEHA_BUYERS - 1]
    for customer in w.sneha_buyers:
        customer.rm_employee_id = sneha.id
    for i, customer in enumerate(others[SNEHA_BUYERS - 1:]):
        customer.rm_employee_id = rest[i % len(rest)].id
    for i, deal in enumerate(d for d in w.deals if d.customer.id not in active_ids):
        deal.customer.rm_employee_id = rest[i % len(rest)].id
    w.active_customers = active


def _open_leads(w) -> None:
    """Leads that have not become bookings: new, contacted, visited, negotiating, blocked or lost."""
    rng = w.rng
    arjun = w.by_name[ARJUN]
    others = [e for e in w.sales_team if e is not arjun]
    projects = list(w.projects.values())
    made = sum(1 for row in w.rows if isinstance(row, Lead))

    def any_project():
        return rng.choices(projects, [30, 25, 15, 12, 18])[0]

    def budget(project):
        return TYPICAL_CR[project.name] * rng.uniform(0.85, 1.25)

    # STORY 3: negotiations as (owner, days since last activity, budget in Cr or None).
    idle = lambda: rng.randint(15, 40)  # noqa: E731
    deals = [(arjun, idle(), cr) for cr in ARJUN_IDLE_BUDGETS_CR] + [(arjun, rng.randint(2, 8), None)] * 3
    deals += [(others[0], idle(), 2.4), (others[0], idle(), 2.8)]  # a second, smaller cluster of stalled deals
    deals += [(others[i], idle(), rng.uniform(1.2, 1.9)) for i in range(1, 7)]
    # Active deals were touched 1 to 8 days ago, so they stay "active" even if the demo is a few days after seeding.
    deals += [(others[i % len(others)], rng.randint(1, 8), None) for i in range(180 - len(deals))]

    free_units = [u for p in ("Radhe Skyline", "Radhe Aranya") for u in w.units[w.projects[p].id]
                  if u.status == "available"]
    w.negotiations = []  # (lead, days since last activity); the task generator uses it
    for stage, count, (newest, oldest) in OPEN_STAGES:
        for i in range(count):
            project, created_ago = any_project(), rng.randint(newest, oldest)
            if stage in ("new", "contacted"):
                owner = rng.choice(w.presales_team)
                lead = _lead(w, owner, stage, created_ago, project, budget(project))
                _activities(w, lead, owner, created_ago, rng.randint(0, created_ago), 1 if stage == "new" else 2)
                continue
            if stage == "negotiation":
                owner, last_ago, cr = deals[i]
                created_ago = max(created_ago, last_ago + 5)
                lead = _lead(w, owner, stage, created_ago, project, cr or budget(project))
                w.negotiations.append((lead, last_ago))
            else:
                owner, last_ago = w.sales_team[i % len(w.sales_team)], rng.randint(0, min(created_ago, 12))
                if stage == "blocked":  # a token is paid and one home is held for this lead
                    unit = free_units.pop(rng.randrange(len(free_units)))
                    unit.status, unit.status_changed_at = "blocked", w.at(last_ago)
                    project = next(p for p in projects if p.id == unit.project_id)
                lead = _lead(w, owner, stage, created_ago, project, budget(project))
            _activities(w, lead, owner, created_ago, last_ago, rng.randint(2, 4))
            if stage == "visit_scheduled":  # the first six are today's visits on the Overview page
                w.add(SiteVisit(lead_id=lead.id, project_id=project.id, employee_id=owner.id, status="scheduled",
                                scheduled_at=w.at(0 if i < 6 else -rng.randint(1, 10)), feedback=None))
            else:
                w.visit_pool[owner.id].append((lead, created_ago, last_ago))

    for i in range(TOTAL_LEADS - made - sum(count for _, count, _ in OPEN_STAGES)):
        project, created_ago = any_project(), rng.randint(30, 540)
        visited = rng.random() < 0.6
        owner = w.sales_team[i % len(w.sales_team)] if visited else rng.choice(w.presales_team)
        last_ago = rng.randint(max(0, created_ago - 60), created_ago)
        lead = _lead(w, owner, "lost", created_ago, project, budget(project), lost_reason=rng.choice(LOST_REASONS))
        _activities(w, lead, owner, created_ago, last_ago, rng.randint(1, 3))
        if visited:
            w.visit_pool[owner.id].append((lead, created_ago, last_ago))


def _site_visits(w) -> None:
    """Conversion = bookings / site visits done. STORY 3: Arjun converts 4%, the others 10.5% to 13%."""
    rng = w.rng
    arjun = w.by_name[ARJUN]
    for emp in w.sales_team:
        pool = w.visit_pool[emp.id]
        conversion = ARJUN_CONVERSION if emp is arjun else rng.uniform(0.105, 0.13)
        target = max(len(pool), round(w.booking_count[emp.id] / conversion))
        visits = pool + rng.choices(pool, k=target - len(pool))  # every visited lead once, then repeat visits
        no_shows = rng.choices(pool, k=round(target * 0.06))
        for n, (lead, first_ago, last_ago) in enumerate(visits + no_shows):
            done = n < len(visits)
            w.add(SiteVisit(lead_id=lead.id, project_id=lead.preferred_project_id, employee_id=emp.id,
                            scheduled_at=w.at(rng.randint(last_ago, first_ago)), status="done" if done else "no_show",
                            feedback=rng.choice(VISIT_FEEDBACK) if done else None))
