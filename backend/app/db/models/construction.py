"""Construction: contractors, milestones, budgets, quality issues and safety incidents."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Money, Percent, fk


class Contractor(Base):
    __tablename__ = "contractors"

    name: Mapped[str] = mapped_column(String(120), index=True)
    trade: Mapped[str] = mapped_column(String(60))  # shuttering, steel, electrical, ...


class ConstructionMilestone(Base):
    __tablename__ = "construction_milestones"

    tower_id: Mapped[uuid.UUID] = fk("towers.id")
    type: Mapped[str] = mapped_column(String(40), index=True)  # foundation, slab_14, brickwork, finishing, ...
    seq: Mapped[int] = mapped_column(Integer)
    planned_date: Mapped[date] = mapped_column(Date, index=True)
    actual_date: Mapped[date | None] = mapped_column(Date)  # empty = not finished yet
    percent_complete: Mapped[Decimal] = mapped_column(Percent, default=0)
    contractor_id: Mapped[uuid.UUID | None] = fk("contractors.id", nullable=True)
    owner_employee_id: Mapped[uuid.UUID | None] = fk("employees.id", nullable=True)  # extra to the spec: "milestones owned"
    delay_cause: Mapped[str | None] = mapped_column(Text)


class ProjectBudget(Base):
    __tablename__ = "project_budgets"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    category: Mapped[str] = mapped_column(String(60))  # structure, finishing, MEP, landscaping, ...
    budget_amount: Mapped[Decimal] = mapped_column(Money)
    actual_amount: Mapped[Decimal] = mapped_column(Money)
    as_of: Mapped[date] = mapped_column(Date)


class QualityIssue(Base):
    __tablename__ = "quality_issues"

    tower_id: Mapped[uuid.UUID] = fk("towers.id")
    raised_on: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), index=True)  # open, closed
    contractor_id: Mapped[uuid.UUID | None] = fk("contractors.id", nullable=True)  # extra: contractor open issues
    owner_employee_id: Mapped[uuid.UUID | None] = fk("employees.id", nullable=True)  # extra: site engineer


class SafetyIncident(Base):
    __tablename__ = "safety_incidents"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    severity: Mapped[str] = mapped_column(String(20))  # minor, major
    description: Mapped[str] = mapped_column(Text)
