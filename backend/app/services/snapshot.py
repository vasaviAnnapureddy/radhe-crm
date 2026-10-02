"""All rows held in memory, with shortcuts for the questions every service asks.

The data is small and read-only, so we load it once and answer every request from memory.
That keeps hover cards instant. For a much larger database, replace these with SQL queries.
"""
import threading
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from functools import cached_property

from sqlalchemy import select

from app.db.models import (
    Base, Booking, ConstructionMilestone, Customer, CustomerInteraction, Demand, HomeLoan, Lead,
    LeadActivity, Receipt, Tower, Unit,
)
from app.db.session import get_session_factory

IST = timezone(timedelta(hours=5, minutes=30))
RELOAD_SECONDS = 6 * 60 * 60  # six hours; a restart reloads at once


def today_ist() -> date:
    return datetime.now(IST).date()


def to_date(value):
    """Datetime to an India-time date. Plain dates pass through."""
    if isinstance(value, datetime):
        return (value.astimezone(IST) if value.tzinfo else value).date()
    return value


def num(value) -> float:
    return float(value) if value is not None else 0.0


class Snapshot:
    def __init__(self, rows, today: date):
        self.today = today
        self._rows, self._ids, self._index, self._memo = defaultdict(list), defaultdict(dict), {}, {}
        self.add(rows)

    # ---- basic lookups ----
    def add(self, rows) -> None:
        for row in rows:
            self._rows[type(row)].append(row)
            self._ids[type(row)][row.id] = row
        self._index.clear()

    def all(self, model) -> list:
        return self._rows.get(model, [])

    def one(self, model, id):
        return self._ids.get(model, {}).get(id)

    def kids(self, model, attr: str, id) -> list:
        """Rows of `model` whose `attr` equals `id`, for example every Demand of one booking."""
        key = (model, attr)
        if key not in self._index:
            index = defaultdict(list)
            for row in self.all(model):
                index[getattr(row, attr)].append(row)
            self._index[key] = index
        return self._index[key].get(id, [])

    def memo(self, key, build):
        """Work something out once per snapshot."""
        if key not in self._memo:
            self._memo[key] = build()
        return self._memo[key]

    # ---- money ----
    @cached_property
    def paid(self) -> dict:
        """demand id -> rupees received so far."""
        totals = defaultdict(float)
        for receipt in self.all(Receipt):
            totals[receipt.demand_id] += num(receipt.amount)
        return totals

    def left(self, demand) -> float:
        """Rupees still unpaid on a raised demand. Part payments are subtracted."""
        return max(num(demand.amount) - self.paid[demand.id], 0.0) if demand.due_on else 0.0

    def late(self, demand) -> int:
        """Days overdue, or 0 if paid or not yet due."""
        if demand.due_on and demand.due_on < self.today and self.left(demand) > 0:
            return (self.today - demand.due_on).days
        return 0

    def efficiency(self, demands) -> float | None:
        """Collected / demanded, in percent, for demands that are already due."""
        due = [d for d in demands if d.due_on and d.due_on <= self.today]
        asked = sum(num(d.amount) for d in due)
        return round(100 * sum(min(self.paid[d.id], num(d.amount)) for d in due) / asked, 1) if asked else None

    # ---- bookings and buyers ----
    @cached_property
    def active_bookings(self) -> list:
        return [b for b in self.all(Booking) if b.status != "cancelled"]

    @cached_property
    def unit_booking(self) -> dict:
        return {b.unit_id: b for b in self.active_bookings}

    @cached_property
    def active_customers(self) -> list:
        ids = {b.customer_id for b in self.active_bookings}
        return [c for c in self.all(Customer) if c.id in ids]

    def bookings_of(self, customer_id) -> list:
        return [b for b in self.kids(Booking, "customer_id", customer_id) if b.status != "cancelled"]

    def unit(self, booking):
        return self.one(Unit, booking.unit_id)

    def demands(self, booking) -> list:
        return self.kids(Demand, "booking_id", booking.id)

    def booking_paid(self, booking) -> float:
        return sum(self.paid[d.id] for d in self.demands(booking))

    def booking_overdue(self, booking) -> tuple[float, int]:
        """(rupees overdue, worst days overdue) for one booking."""
        late = [d for d in self.demands(booking) if self.late(d)]
        return sum(self.left(d) for d in late), max((self.late(d) for d in late), default=0)

    def customer_overdue(self, customer_id) -> tuple[float, int]:
        parts = [self.booking_overdue(b) for b in self.bookings_of(customer_id)]
        return sum(p[0] for p in parts), max((p[1] for p in parts), default=0)

    def loan(self, booking):
        loans = self.kids(HomeLoan, "booking_id", booking.id)
        return loans[0] if loans else None

    def price(self, unit) -> float:
        area = unit.sba_sft if unit.sba_sft else unit.plot_sqyd
        return num(unit.base_price_psf) * num(area) + num(unit.plc_amount) + num(unit.floor_rise_amount)

    def days_unsold(self, unit) -> int | None:
        return (self.today - unit.listed_on).days if unit.status in ("available", "blocked") else None

    # ---- contact ----
    def last_contact(self, customer_id) -> date | None:
        """The last day WE contacted the buyer."""
        out = [to_date(i.occurred_at) for i in self.kids(CustomerInteraction, "customer_id", customer_id)
               if i.direction == "outbound"]
        return max(out, default=None)

    def open_queries(self, customer_id) -> list:
        """Messages from the buyer that nobody has answered."""
        return [i for i in self.kids(CustomerInteraction, "customer_id", customer_id)
                if i.direction == "inbound" and i.needs_reply and i.replied_at is None]

    def idle_days(self, lead: Lead) -> int:
        dates = [to_date(a.occurred_at) for a in self.kids(LeadActivity, "lead_id", lead.id)]
        return (self.today - max(dates, default=to_date(lead.created_at))).days

    # ---- construction ----
    @cached_property
    def delayed(self) -> dict:
        """Milestones past their planned date and still not finished."""
        return {m.id: m for m in self.all(ConstructionMilestone)
                if m.actual_date is None and m.planned_date < self.today}

    def slip(self, milestone) -> int:
        """Days behind plan: finished late, or still open after the planned date."""
        end = milestone.actual_date or self.today
        return max((end - milestone.planned_date).days, 0)

    def blocked(self, milestone) -> list:
        """Demands that cannot be raised because this milestone is not finished."""
        return [d for d in self.kids(Demand, "construction_milestone_id", milestone.id)
                if d.status == "not_raised" and self.one(Booking, d.booking_id).status != "cancelled"]

    def project_id_of_tower(self, tower_id):
        tower = self.one(Tower, tower_id)
        return tower.project_id if tower else None


# ---- loading and caching ----
_cache = {"snapshot": None, "loaded_at": 0.0}
_lock = threading.Lock()


def load_snapshot() -> Snapshot:
    rows = []
    with get_session_factory()() as session:
        for mapper in Base.registry.mappers:
            rows.extend(session.scalars(select(mapper.class_)).all())
        session.expunge_all()
    return Snapshot(rows, today_ist())


def _is_fresh() -> bool:
    snap = _cache["snapshot"]
    return bool(snap) and time.time() - _cache["loaded_at"] < RELOAD_SECONDS and snap.today == today_ist()


def get_snapshot() -> Snapshot:
    """FastAPI dependency. Reloads when the date changes (India time) or the data is six hours old.

    The data only changes when it is reseeded, and the server is restarted after that, so there is
    no need to reload often. The second check inside the lock matters: when several requests arrive
    together and find the data stale, only the first one reloads; the others wait and reuse it.
    """
    if not _is_fresh():
        with _lock:
            if not _is_fresh():
                _cache["snapshot"], _cache["loaded_at"] = load_snapshot(), time.time()
    return _cache["snapshot"]
