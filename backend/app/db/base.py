"""Parent class for every table, plus small helpers that keep the model files short."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Money is stored in rupees with 2 decimals, up to 999,99,99,99,999.99
Money = Numeric(14, 2)
# Areas (sq ft, sq yd) and percentages
Area = Numeric(10, 2)
Percent = Numeric(5, 2)


class Base(DeclarativeBase):
    """Every table gets a UUID id, created_at and updated_at."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def fk(target: str, nullable: bool = False):
    """A foreign key column. Always indexed, because we filter and join on these."""
    return mapped_column(Uuid, ForeignKey(target), index=True, nullable=nullable)
