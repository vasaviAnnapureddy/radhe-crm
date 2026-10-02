"""Departments, 110 employees and their targets."""
from datetime import date, timedelta
from decimal import Decimal

from app.db.models import Department, Employee, EmployeeTarget
from seed.names import email_for, person
from seed.stories import ARJUN, SNEHA

# The first role in each department is the head; everyone else reports to the head.
DEPARTMENTS = [
    ("Pre-sales", [("Pre-sales Lead", 1), ("Tele-caller", 7), ("Lead Qualifier", 4)]),
    ("Sales", [("Sales Head", 1), ("Sales Manager", 14), ("NRI Desk Manager", 3)]),
    ("CRM", [("CRM Head", 1), ("Relationship Manager", 21)]),
    ("Projects & Construction", [("Head of Projects", 1), ("Project Manager", 4), ("Site Engineer", 12),
                                 ("QA/QC Engineer", 3), ("Safety Officer", 2)]),
    ("Procurement", [("Procurement Head", 1), ("Purchase Officer", 5)]),
    ("Design", [("Chief Architect", 1), ("Architect", 2), ("Interior Designer", 5)]),
    ("Finance & Collections", [("Finance Head", 1), ("Accountant", 4), ("Collection Officer", 5)]),
    ("Legal", [("Legal Head", 1), ("Legal Officer", 4)]),
    ("Marketing", [("Marketing Head", 1), ("Campaign Manager", 6)]),
]
PLANTED = {("Relationship Manager", 0): SNEHA, ("Sales Manager", 3): ARJUN}


def quarter_start(d: date) -> date:
    return date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def add_org(w) -> None:
    w.staff, w.by_name = {}, {}
    number = 0
    for dept_name, roles in DEPARTMENTS:
        dept = w.add(Department(name=dept_name))
        head = None
        for role, count in roles:
            for i in range(count):
                number += 1
                planted = PLANTED.get((role, i))
                name = planted or person(w, unique=True)
                # About one in seven people joined in the last six months, so "new joiners" has real rows.
                # Team heads and the story characters are long-serving.
                recent = head is not None and not planted and w.rng.random() < 0.14
                emp = w.add(Employee(
                    code=f"RC-{number:04d}", name=name, phone=w.phone(),
                    email=email_for(name, number, "radheconstructions.demo"),
                    department_id=dept.id, role_title=role, manager_id=head.id if head else None,
                    joined_on=w.ago(w.rng.randint(3, 180) if recent else w.rng.randint(181, 2500)), status="active",
                ))
                head = head or emp
                w.staff.setdefault(role, []).append(emp)
                w.by_name[name] = emp
    for emp in w.rng.sample(w.staff["Tele-caller"] + w.staff["Accountant"] + w.staff["Site Engineer"], 4):
        emp.status = "on_leave"

    w.sales_team = w.staff["Sales Manager"] + w.staff["NRI Desk Manager"]
    w.presales_team = w.staff["Tele-caller"] + w.staff["Lead Qualifier"]
    _add_targets(w)


def _add_targets(w) -> None:
    def target(emp, start, end, metric, value):
        w.add(EmployeeTarget(employee_id=emp.id, period_start=start, period_end=end,
                             metric=metric, target_value=Decimal(value)))

    # Sales: six quarters, so the scorecard can show a trend.
    start = quarter_start(w.today)
    for _ in range(6):
        end = quarter_start(start + timedelta(days=95)) - timedelta(days=1)
        for emp in w.sales_team:
            target(emp, start, end, "bookings", 9)
            target(emp, start, end, "site_visits", 75)
        start = quarter_start(start - timedelta(days=1))

    start = quarter_start(w.today)
    end = quarter_start(start + timedelta(days=95)) - timedelta(days=1)
    for emp in w.staff["Relationship Manager"]:
        target(emp, start, end, "collection_efficiency_pct", 90)
        target(emp, start, end, "response_hours", 24)
    for emp in w.staff["Site Engineer"] + w.staff["Project Manager"]:
        target(emp, start, end, "milestones_on_time_pct", 85)
