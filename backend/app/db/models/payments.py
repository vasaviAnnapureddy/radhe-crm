"""Payments: plans, demands (requests to pay), receipts (money in) and home loans."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Money, Percent, fk


class PaymentPlan(Base):
    __tablename__ = "payment_plans"

    name: Mapped[str] = mapped_column(String(80), unique=True)


class PlanMilestone(Base):
    __tablename__ = "plan_milestones"

    payment_plan_id: Mapped[uuid.UUID] = fk("payment_plans.id")
    seq: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(80))
    percent: Mapped[Decimal] = mapped_column(Percent)
    # Which construction stage triggers this payment (empty for booking and agreement payments).
    construction_milestone_type: Mapped[str | None] = mapped_column(String(40))


class Demand(Base):
    __tablename__ = "demands"

    booking_id: Mapped[uuid.UUID] = fk("bookings.id")
    plan_milestone_id: Mapped[uuid.UUID] = fk("plan_milestones.id")
    # The construction milestone that must finish before this demand can be raised.
    construction_milestone_id: Mapped[uuid.UUID | None] = fk("construction_milestones.id", nullable=True)
    amount: Mapped[Decimal] = mapped_column(Money)
    raised_on: Mapped[date | None] = mapped_column(Date, index=True)
    due_on: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)  # not_raised, raised, paid, overdue
    reminders_sent: Mapped[int] = mapped_column(Integer, default=0)  # extra to the spec: quick view shows it


class Receipt(Base):
    __tablename__ = "receipts"

    demand_id: Mapped[uuid.UUID] = fk("demands.id")
    amount: Mapped[Decimal] = mapped_column(Money)
    received_on: Mapped[date] = mapped_column(Date, index=True)
    mode: Mapped[str] = mapped_column(String(20))  # neft, cheque, upi, loan_disbursement
    from_bank_loan: Mapped[bool] = mapped_column(Boolean, default=False)


class HomeLoan(Base):
    __tablename__ = "home_loans"

    booking_id: Mapped[uuid.UUID] = fk("bookings.id")
    bank: Mapped[str] = mapped_column(String(60), index=True)
    sanctioned_amount: Mapped[Decimal] = mapped_column(Money)
    disbursed_amount: Mapped[Decimal] = mapped_column(Money, default=0)
    status: Mapped[str] = mapped_column(String(30), index=True)  # applied, sanctioned, disbursing, awaiting_disbursement, closed
