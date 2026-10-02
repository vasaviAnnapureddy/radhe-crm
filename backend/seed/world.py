"""The World holds today's date, the random generator and every row created so far."""
import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from faker import Faker

IST = timezone(timedelta(hours=5, minutes=30))


class World:
    def __init__(self, today: date, seed: int = 42):
        self.today = today
        # A fixed seed gives the same names, ids and numbers on every run.
        self.rng = random.Random(seed)
        self.fake = Faker("en_IN")
        self.fake.seed_instance(seed)
        self.rows: list = []
        self.used_names: set[str] = set()

    def add(self, obj):
        obj.id = uuid.UUID(int=self.rng.getrandbits(128), version=4)
        self.rows.append(obj)
        return obj

    def ago(self, days: int) -> date:
        """A date `days` before today. A negative number gives a future date."""
        return self.today - timedelta(days=days)

    def at(self, days_ago: int) -> datetime:
        """A date and time in office hours, India time."""
        clock = time(self.rng.randint(9, 18), self.rng.randint(0, 59))
        return datetime.combine(self.ago(days_ago), clock, IST)

    def phone(self) -> str:
        """A made-up 10-digit mobile number."""
        return "9" + "".join(str(self.rng.randint(0, 9)) for _ in range(9))


def rupees(amount) -> Decimal:
    """Round to whole rupees."""
    return Decimal(int(round(float(amount))))


def list_price(unit) -> Decimal:
    """Area x rate + extra charges. Plots are priced on plot area, everything else on SBA."""
    area = unit.sba_sft if unit.sba_sft else unit.plot_sqyd
    return unit.base_price_psf * area + unit.plc_amount + unit.floor_rise_amount


@dataclass
class Deal:
    """One booking with the objects around it, so later generators do not need lookups."""
    booking: object
    unit: object
    customer: object
    project: object
    ago: int  # days since booking
    cancelled: bool
    loan: object = None
