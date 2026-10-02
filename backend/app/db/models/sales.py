"""Sales: channel partners, leads, site visits, customers, bookings and commissions."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Money, Percent, fk


class ChannelPartner(Base):
    __tablename__ = "channel_partners"

    firm_name: Mapped[str] = mapped_column(String(120), index=True)
    contact_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    city: Mapped[str] = mapped_column(String(60))
    commission_pct: Mapped[Decimal] = mapped_column(Percent)
    status: Mapped[str] = mapped_column(String(20), default="active")


class Lead(Base):
    __tablename__ = "leads"  # created_at (from Base) is the day the lead came in

    name: Mapped[str] = mapped_column(String(120), index=True)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(40), index=True)
    channel_partner_id: Mapped[uuid.UUID | None] = fk("channel_partners.id", nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(Money)
    budget_max: Mapped[Decimal | None] = mapped_column(Money)
    preferred_config: Mapped[str | None] = mapped_column(String(20))
    preferred_project_id: Mapped[uuid.UUID | None] = fk("projects.id", nullable=True)
    country: Mapped[str] = mapped_column(String(60), default="India")
    owner_employee_id: Mapped[uuid.UUID] = fk("employees.id")
    # new, contacted, visit_scheduled, visit_done, negotiation, blocked, booked,
    # agreement_signed, registered, possession, lost, cancelled
    stage: Mapped[str] = mapped_column(String(30), index=True)
    lost_reason: Mapped[str | None] = mapped_column(String(120))


class LeadActivity(Base):
    __tablename__ = "lead_activities"

    lead_id: Mapped[uuid.UUID] = fk("leads.id")
    employee_id: Mapped[uuid.UUID] = fk("employees.id")
    type: Mapped[str] = mapped_column(String(20))  # call, whatsapp, email, meeting, note
    summary: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SiteVisit(Base):
    __tablename__ = "site_visits"

    lead_id: Mapped[uuid.UUID] = fk("leads.id")
    project_id: Mapped[uuid.UUID] = fk("projects.id")
    employee_id: Mapped[uuid.UUID] = fk("employees.id")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)  # scheduled, done, no_show, cancelled
    feedback: Mapped[str | None] = mapped_column(Text)


class Customer(Base):
    __tablename__ = "customers"

    lead_id: Mapped[uuid.UUID | None] = fk("leads.id", nullable=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(20), index=True)  # end_user, nri, hni, investor, corporate
    is_nri: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    country: Mapped[str] = mapped_column(String(60), default="India")
    city: Mapped[str | None] = mapped_column(String(60))  # extra to the spec: needed for "Dallas", "Dubai"
    rm_employee_id: Mapped[uuid.UUID] = fk("employees.id")


class Booking(Base):
    __tablename__ = "bookings"

    unit_id: Mapped[uuid.UUID] = fk("units.id")
    customer_id: Mapped[uuid.UUID] = fk("customers.id")
    employee_id: Mapped[uuid.UUID] = fk("employees.id")  # the sales manager who closed it
    channel_partner_id: Mapped[uuid.UUID | None] = fk("channel_partners.id", nullable=True)
    booked_on: Mapped[date] = mapped_column(Date, index=True)
    agreement_value: Mapped[Decimal] = mapped_column(Money)
    payment_plan_id: Mapped[uuid.UUID] = fk("payment_plans.id")
    # booked, agreement_signed, registered, possession, cancelled
    status: Mapped[str] = mapped_column(String(20), index=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(120))
    agreement_on: Mapped[date | None] = mapped_column(Date)
    registered_on: Mapped[date | None] = mapped_column(Date)
    possession_on: Mapped[date | None] = mapped_column(Date)


class CpCommission(Base):
    __tablename__ = "cp_commissions"

    booking_id: Mapped[uuid.UUID] = fk("bookings.id")
    channel_partner_id: Mapped[uuid.UUID] = fk("channel_partners.id")
    amount: Mapped[Decimal] = mapped_column(Money)
    due_on: Mapped[date] = mapped_column(Date, index=True)
    paid_on: Mapped[date | None] = mapped_column(Date)
