"""Projects and inventory: projects, towers, units and price history."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Area, Base, Money, fk


class Project(Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[str] = mapped_column(String(20), index=True)  # apartments, villas, plots
    locality: Mapped[str] = mapped_column(String(80))
    rera_no: Mapped[str] = mapped_column(String(40))  # fictional format
    launch_date: Mapped[date] = mapped_column(Date)
    expected_possession: Mapped[date] = mapped_column(Date)
    total_acres: Mapped[Decimal] = mapped_column(Area)
    status: Mapped[str] = mapped_column(String(30), index=True)  # launched, under_construction, partly_delivered
    hero_image: Mapped[str | None] = mapped_column(String(255))


class Tower(Base):
    __tablename__ = "towers"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    name: Mapped[str] = mapped_column(String(40))
    floors: Mapped[int] = mapped_column(Integer)
    units_per_floor: Mapped[int] = mapped_column(Integer)


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("project_id", "unit_no"),)

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    tower_id: Mapped[uuid.UUID | None] = fk("towers.id", nullable=True)  # villas and plots have no tower
    unit_no: Mapped[str] = mapped_column(String(20), index=True)
    floor: Mapped[int | None] = mapped_column(Integer)
    config: Mapped[str] = mapped_column(String(20), index=True)  # 3 BHK, 4 BHK, Villa, Plot
    carpet_sft: Mapped[Decimal | None] = mapped_column(Area)
    sba_sft: Mapped[Decimal | None] = mapped_column(Area)
    plot_sqyd: Mapped[Decimal | None] = mapped_column(Area)
    facing: Mapped[str] = mapped_column(String(10))
    base_price_psf: Mapped[Decimal] = mapped_column(Money)  # per sq ft; per sq yd for plots
    plc_amount: Mapped[Decimal] = mapped_column(Money, default=0)
    floor_rise_amount: Mapped[Decimal] = mapped_column(Money, default=0)
    # available, blocked, booked, registered, handed_over
    status: Mapped[str] = mapped_column(String(20), index=True)
    listed_on: Mapped[date] = mapped_column(Date)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PriceHistory(Base):
    __tablename__ = "price_history"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    config: Mapped[str] = mapped_column(String(20))
    price_psf: Mapped[Decimal] = mapped_column(Money)
    effective_from: Mapped[date] = mapped_column(Date, index=True)
