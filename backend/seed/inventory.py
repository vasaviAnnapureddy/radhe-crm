"""Projects, towers, 1,600 units, prices, contractors, construction milestones, budgets, quality, safety."""
from decimal import Decimal

from app.db.models import (
    ConstructionMilestone,
    Contractor,
    PriceHistory,
    Project,
    ProjectBudget,
    QualityIssue,
    SafetyIncident,
    Tower,
    Unit,
)
from seed.stories import (
    AGEING_PROJECT,
    AGEING_UNITS,
    CR,
    DELAY_CAUSE,
    DELAY_CONTRACTOR,
    DELAY_MILESTONE,
    DELAY_PROJECT,
    DELAY_SLIP_DAYS,
    DELAY_TOWER,
)
from seed.world import rupees

# launch = days since launch, possession = days until expected possession.
# psf is rupees per sq ft (per sq yd for plots). layout and facing go position by position on a floor.
PROJECTS = [
    dict(name="Radhe Skyline", type="apartments", locality="Narsingi", launch=540, possession=600, acres=9.5,
         status="under_construction", psf=11000, towers=[("Tower A", 30, 6), ("Tower B", 30, 6), ("Tower C", 30, 6)],
         sizes={"3 BHK": 2400, "4 BHK": 3600}, layout=["3 BHK", "4 BHK"] * 3,
         facing=["East", "East", "North", "West", "West", "South"]),
    dict(name="Radhe Greens", type="apartments", locality="Tellapur", launch=1200, possession=300, acres=12.0,
         status="partly_delivered", psf=8800, towers=[("Tower A", 20, 8), ("Tower B", 20, 8), ("Tower C", 20, 8)],
         sizes={"3 BHK": 2200, "4 BHK": 3200},
         layout=["3 BHK", "4 BHK", "3 BHK", "3 BHK", "4 BHK", "3 BHK", "4 BHK", "3 BHK"],
         facing=["East", "East", "West", "West", "West", "West", "North", "South"]),
    dict(name="Radhe Aranya", type="apartments", locality="Gachibowli", launch=120, possession=1100, acres=6.0,
         status="launched", psf=13000, towers=[("Tower 1", 25, 6), ("Tower 2", 25, 6)],
         sizes={"3 BHK": 2600, "4 BHK": 4000}, layout=["3 BHK", "4 BHK"] * 3,
         facing=["East", "East", "North", "West", "West", "South"]),
    dict(name="Radhe Vanam Villas", type="villas", locality="Kokapet", launch=560, possession=400, acres=42.0,
         status="under_construction", psf=13000, count=100),
    dict(name="Radhe Bhoomi", type="plots", locality="Kollur", launch=600, possession=90, acres=58.0,
         status="launched", psf=60000, count=180),
]

MILESTONE_TYPES = ["foundation", "slab_5", "slab_10", "slab_14", "slab_18", "top_slab",
                   "brickwork", "finishing", "handover"]
# One entry per milestone type: (planned days ago, actual days ago or None, percent complete if not done).
# Negative = in the future. Actual smaller than planned means it finished late.
SCHEDULES = {
    ("Radhe Skyline", "Tower A"): [(430, 428), (330, 326), (230, 224), (135, 130), (40, 36), (-150, None),
                                   (-270, None), (-420, None), (-600, None)],
    # STORY 1: the 14th floor slab was planned 23 days ago and is still not finished.
    ("Radhe Skyline", "Tower B"): [(425, 420), (305, 300), (156, 150), (DELAY_SLIP_DAYS, None, 80), (-70, None),
                                   (-190, None), (-310, None), (-450, None), (-600, None)],
    ("Radhe Skyline", "Tower C"): [(250, 247), (104, 100), (-25, None, 60), (-120, None), (-210, None),
                                   (-330, None), (-420, None), (-540, None), (-660, None)],
    ("Radhe Greens", "Tower A"): [(1100, 1096), (1000, 994), (900, 897), (820, 815), (740, 731), (640, 636),
                                  (520, 511), (360, 352), (215, 200)],
    ("Radhe Greens", "Tower B"): [(900, 897), (800, 795), (700, 698), (620, 612), (540, 536), (440, 433),
                                  (320, 314), (45, 40), (-120, None, 70)],
    ("Radhe Greens", "Tower C"): [(640, 636), (540, 537), (440, 432), (360, 356), (270, 266), (99, 95),
                                  (-25, None, 55), (-170, None), (-300, None)],
    ("Radhe Aranya", "Tower 1"): [(-30, None, 65), (-150, None), (-260, None), (-350, None), (-440, None),
                                  (-560, None), (-680, None), (-830, None), (-1100, None)],
    ("Radhe Aranya", "Tower 2"): [(-90, None, 20), (-210, None), (-320, None), (-410, None), (-500, None),
                                  (-620, None), (-740, None), (-890, None), (-1160, None)],
}

CONTRACTORS = [
    (DELAY_CONTRACTOR, "Shuttering"), ("Krishna Shuttering Works", "Shuttering"),
    ("Telangana Earthmovers", "Excavation and foundation"), ("Deccan Steel Fixers", "Steel"),
    ("Musi RMC Supplies", "Concrete"), ("Kakatiya Electricals", "Electrical"),
    ("Godavari Plumbing Works", "Plumbing"), ("Nizam Facades", "Facade and glazing"),
    ("Srinidhi Masonry & Finishing", "Masonry"), ("Charminar Painters", "Painting and finishing"),
    ("Varun Lifts & Escalators", "Lifts"), ("Pragati Landscapes", "Landscaping"),
]
SLIP_CAUSES = ["Heavy rain stopped work", "Material delivery delay", "Labour shortage after the festival season"]
BUDGET_SHARES = [("Structure", 0.45), ("Finishing", 0.20), ("MEP (electrical and plumbing)", 0.15),
                 ("Landscaping and amenities", 0.08), ("Approvals and overheads", 0.12)]
# project: (total budget in Cr, share spent so far, actual vs budget)
BUDGETS = {"Radhe Skyline": (620, 0.42, 1.06), "Radhe Greens": (480, 0.85, 1.02), "Radhe Aranya": (410, 0.06, 0.99),
           "Radhe Vanam Villas": (350, 0.50, 1.03), "Radhe Bhoomi": (60, 0.80, 1.00)}
QUALITY_CATEGORIES = ["Honeycombing in concrete", "Cover blocks missing", "Plaster cracks", "Waterproofing leak",
                      "Hollow tiles", "Electrical conduit misaligned", "Door frame alignment"]
SAFETY_NOTES = ["Worker without harness at height; work stopped and briefing held", "Loose scaffolding plank found in inspection",
                "Minor cut during bar bending; first aid given", "Material hoist overloaded; operator warned",
                "Unbarricaded lift shaft opening found and closed"]


def add_inventory(w) -> None:
    rng = w.rng
    w.projects, w.towers, w.units, w.protected_units = {}, {}, {}, set()
    for n, spec in enumerate(PROJECTS, start=1):
        project = w.add(Project(
            name=spec["name"], type=spec["type"], locality=spec["locality"], rera_no=f"DEMO/TS/P024/{n:04d}",
            launch_date=w.ago(spec["launch"]), expected_possession=w.ago(-spec["possession"]),
            total_acres=Decimal(str(spec["acres"])), status=spec["status"],
            hero_image=f"/images/{spec['name'].lower().replace(' ', '-')}.webp",
        ))
        w.projects[project.name] = project
        w.units[project.id] = []

        def unit(**fields):
            base = dict(project_id=project.id, status="available", plc_amount=Decimal(0), floor_rise_amount=Decimal(0),
                        listed_on=w.ago(rng.randint(20, min(250, spec["launch"]))))
            w.units[project.id].append(w.add(Unit(**{**base, **fields})))

        if spec["type"] == "apartments":
            for tower_name, floors, per_floor in spec["towers"]:
                tower = w.add(Tower(project_id=project.id, name=tower_name, floors=floors, units_per_floor=per_floor))
                w.towers[(project.name, tower_name)] = tower
                for floor in range(1, floors + 1):
                    for pos in range(per_floor):
                        config = spec["layout"][pos]
                        sba = spec["sizes"][config] + 50 * rng.randint(-2, 2)
                        unit(tower_id=tower.id, unit_no=f"{tower_name[-1]}-{floor:02d}{pos + 1:02d}", floor=floor,
                             config=config, sba_sft=Decimal(sba), carpet_sft=Decimal(round(sba * 0.7)),
                             facing=spec["facing"][pos], base_price_psf=Decimal(spec["psf"] + 100 * rng.randint(-2, 2)),
                             plc_amount=Decimal(500_000 if pos in (0, per_floor - 1) else 0),  # corner homes
                             floor_rise_amount=Decimal(30 * (floor - 1) * sba))
        elif spec["type"] == "villas":
            for i in range(1, spec["count"] + 1):
                sba = 50 * rng.randint(100, 180)  # 5,000 to 9,000 sq ft
                unit(unit_no=f"V-{i:03d}", config="Villa", sba_sft=Decimal(sba), carpet_sft=Decimal(round(sba * 0.75)),
                     plot_sqyd=Decimal(rng.choice([400, 500, 600, 800])), facing=rng.choice(["East", "West", "North"]),
                     base_price_psf=Decimal(spec["psf"] + 250 * rng.randint(-4, 4)),
                     plc_amount=Decimal(rng.choice([0, 0, 1_500_000, 4_000_000])))
        else:
            for i in range(1, spec["count"] + 1):
                unit(unit_no=f"P-{i:03d}", config="Plot", plot_sqyd=Decimal(rng.choice([200, 267, 300, 400, 500])),
                     facing=rng.choice(["East", "West", "North", "South"]),
                     base_price_psf=Decimal(spec["psf"] + 1000 * rng.randint(-5, 10)),
                     plc_amount=Decimal(rng.choice([0, 0, 0, 500_000])))

        for config in sorted({u.config for u in w.units[project.id]}):
            for quarter in range(6):  # price rose about 2.5% each quarter
                if quarter * 90 <= spec["launch"]:
                    w.add(PriceHistory(project_id=project.id, config=config, effective_from=w.ago(quarter * 90),
                                       price_psf=rupees(spec["psf"] * (1 - 0.025 * quarter))))

    # STORY 5: west-facing homes on floors 2 to 4 in Greens Towers B and C that nobody has bought for 300+ days.
    greens = w.projects[AGEING_PROJECT]
    slow_towers = {w.towers[(AGEING_PROJECT, "Tower B")].id, w.towers[(AGEING_PROJECT, "Tower C")].id}
    slow = [u for u in w.units[greens.id] if u.tower_id in slow_towers and u.facing == "West" and 2 <= u.floor <= 4]
    for u in slow[:AGEING_UNITS]:
        u.listed_on = w.ago(rng.randint(300, 420))
        w.protected_units.add(u.id)


def add_construction(w) -> None:
    rng = w.rng
    contractors = {name: w.add(Contractor(name=name, trade=trade)) for name, trade in CONTRACTORS}
    w.contractors = contractors
    engineers = w.staff["Site Engineer"]
    w.milestones = {}
    for n, ((project_name, tower_name), schedule) in enumerate(SCHEDULES.items()):
        tower = w.towers[(project_name, tower_name)]
        for seq, (kind, entry) in enumerate(zip(MILESTONE_TYPES, schedule), start=1):
            planned, actual = entry[0], entry[1]
            if kind == "foundation":
                contractor = contractors["Telangana Earthmovers"]
            elif kind.startswith("slab") or kind == "top_slab":
                balaji_job = project_name == DELAY_PROJECT and tower_name != "Tower A"
                contractor = contractors[DELAY_CONTRACTOR if balaji_job else "Krishna Shuttering Works"]
            else:
                contractor = {"brickwork": contractors["Srinidhi Masonry & Finishing"],
                              "finishing": contractors["Charminar Painters"]}.get(kind)
            cause = None
            if (project_name, tower_name, kind) == (DELAY_PROJECT, DELAY_TOWER, DELAY_MILESTONE):
                cause = DELAY_CAUSE
            elif actual is not None and planned - actual >= 5:
                cause = rng.choice(SLIP_CAUSES)
            done = actual is not None
            w.milestones[(tower.id, kind)] = w.add(ConstructionMilestone(
                tower_id=tower.id, type=kind, seq=seq, planned_date=w.ago(planned),
                actual_date=w.ago(actual) if done else None,
                percent_complete=Decimal(100 if done else (entry[2] if len(entry) > 2 else 0)),
                contractor_id=contractor.id if contractor else None,
                owner_employee_id=engineers[(n + seq // 4) % len(engineers)].id, delay_cause=cause,
            ))

        # Quality log. Aranya has barely started; the delayed Tower B has a few extra open issues.
        is_delayed_tower = (project_name, tower_name) == (DELAY_PROJECT, DELAY_TOWER)
        count = rng.randint(0, 2) if project_name == "Radhe Aranya" else rng.randint(8, 14)
        for i in range(count + (6 if is_delayed_tower else 0)):
            is_open = i >= count or rng.random() < 0.18
            w.add(QualityIssue(tower_id=tower.id, raised_on=w.ago(rng.randint(2, 40) if is_open else rng.randint(20, 300)),
                               category=rng.choice(QUALITY_CATEGORIES), status="open" if is_open else "closed",
                               contractor_id=rng.choice(list(contractors.values())).id,
                               owner_employee_id=rng.choice(engineers).id))

    for name, (total_cr, spent, variance) in BUDGETS.items():
        for category, share in BUDGET_SHARES:
            budget = total_cr * CR * share * spent
            w.add(ProjectBudget(project_id=w.projects[name].id, category=category, as_of=w.today,
                                budget_amount=rupees(budget), actual_amount=rupees(budget * variance * rng.uniform(0.97, 1.03))))

    sites = [w.projects[n] for n in ("Radhe Skyline", "Radhe Greens", "Radhe Aranya", "Radhe Vanam Villas")]
    for i in range(9):
        w.add(SafetyIncident(project_id=rng.choice(sites).id, occurred_on=w.ago(rng.randint(5, 400)),
                             severity="major" if i == 0 else "minor", description=rng.choice(SAFETY_NOTES)))
