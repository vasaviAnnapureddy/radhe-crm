"""Builds every row in memory, then inserts them table by table."""
from collections import defaultdict
from datetime import date

from app.db.models import Base, Employee, Risk, User
from app.risks.engine import detect
from app.services.snapshot import Snapshot
from seed.care import add_care
from seed.inventory import add_construction, add_inventory
from seed.money import add_payments, add_plans
from seed.org import add_org
from seed.sales import add_sales
from seed.world import World


def build_world(today: date) -> World:
    w = World(today)
    add_org(w)           # departments, employees, targets
    add_inventory(w)     # projects, towers, units, prices
    add_construction(w)  # contractors, milestones, budgets, quality, safety
    add_plans(w)         # payment plans
    add_sales(w)         # partners, bookings, customers, leads, visits
    add_payments(w)      # demands, receipts, loans
    add_care(w)          # interactions, tickets, interiors, tasks
    # Last: run the risk rules over the finished data and store what they find.
    for risk in detect(Snapshot(w.rows, today)):
        w.add(Risk(**risk, status="open", detected_at=w.at(0), resolved_at=None))
    return w


def add_portal_users(w, password_hash: str) -> int:
    """A login for every employee and every buyer with an active booking.

    They all share one demo password, so the hash is worked out once and reused.
    Each login is tied to exactly one person: that link decides what they can see.
    """
    before = len(w.rows)
    for employee in (row for row in list(w.rows) if isinstance(row, Employee)):
        w.add(User(email=employee.email.lower(), name=employee.name, role="employee", is_active=True,
                   password_hash=password_hash, employee_id=employee.id))
    for customer in w.active_customers:
        w.add(User(email=customer.email.lower(), name=customer.name, role="customer", is_active=True,
                   password_hash=password_hash, customer_id=customer.id))
    return len(w.rows) - before


def insert_rows(conn, rows) -> dict[str, int]:
    """Insert parents before children (sorted_tables gives that order). Returns rows per table."""
    by_table = defaultdict(list)
    for row in rows:
        by_table[row.__table__].append(row)
    counts = {}
    for table in Base.metadata.sorted_tables:
        objs = by_table.get(table)
        if not objs:
            continue
        # Skip columns nobody filled in, so the database default (like created_at) is used.
        columns = [c.key for c in table.columns if any(getattr(o, c.key) is not None for o in objs)]
        conn.execute(table.insert(), [{c: getattr(o, c) for c in columns} for o in objs])
        counts[table.name] = len(objs)
    return counts
