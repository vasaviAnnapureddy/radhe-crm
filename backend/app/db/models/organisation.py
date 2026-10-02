"""Organisation: departments, employees and their targets."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, fk


class Department(Base):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(80), unique=True)


class Employee(Base):
    __tablename__ = "employees"

    code: Mapped[str] = mapped_column(String(20), unique=True)  # like RC-0042
    name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    department_id: Mapped[uuid.UUID] = fk("departments.id")
    role_title: Mapped[str] = mapped_column(String(80), index=True)
    manager_id: Mapped[uuid.UUID | None] = fk("employees.id", nullable=True)
    joined_on: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)  # active, on_leave, exited


class EmployeeTarget(Base):
    __tablename__ = "employee_targets"

    employee_id: Mapped[uuid.UUID] = fk("employees.id")
    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end: Mapped[date] = mapped_column(Date)
    metric: Mapped[str] = mapped_column(String(40))  # bookings_value, site_visits, ...
    target_value: Mapped[Decimal] = mapped_column(Numeric(16, 2))
