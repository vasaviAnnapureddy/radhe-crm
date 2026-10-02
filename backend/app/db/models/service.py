"""Interiors and service. The pages are [SHOULD], but the tables exist now so the seed is complete."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Money, fk


class InteriorProject(Base):
    __tablename__ = "interior_projects"

    customer_id: Mapped[uuid.UUID] = fk("customers.id")
    unit_id: Mapped[uuid.UUID] = fk("units.id")
    designer_employee_id: Mapped[uuid.UUID] = fk("employees.id")
    package: Mapped[str] = mapped_column(String(60))
    value: Mapped[Decimal] = mapped_column(Money)
    stage: Mapped[str] = mapped_column(String(30), index=True)  # design, approval, execution, handover, done
    start_date: Mapped[date] = mapped_column(Date)
    target_date: Mapped[date] = mapped_column(Date)


class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    unit_id: Mapped[uuid.UUID] = fk("units.id")
    customer_id: Mapped[uuid.UUID] = fk("customers.id")
    category: Mapped[str] = mapped_column(String(40), index=True)  # snag, complaint, document, possession_query
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), index=True)  # open, in_progress, resolved
    raised_on: Mapped[date] = mapped_column(Date, index=True)
    resolved_on: Mapped[date | None] = mapped_column(Date)
    sla_hours: Mapped[int] = mapped_column(Integer)
    assigned_employee_id: Mapped[uuid.UUID | None] = fk("employees.id", nullable=True)
