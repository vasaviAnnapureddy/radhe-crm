"""Interactions, tasks and risks."""
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, fk


class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"

    customer_id: Mapped[uuid.UUID] = fk("customers.id")
    employee_id: Mapped[uuid.UUID | None] = fk("employees.id", nullable=True)
    channel: Mapped[str] = mapped_column(String(20))  # call, email, whatsapp, meeting
    direction: Mapped[str] = mapped_column(String(10))  # inbound (from buyer), outbound (from us)
    summary: Mapped[str] = mapped_column(Text)  # kept as text so the V2 copilot can search it
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    needs_reply: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Task(Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(200))
    owner_employee_id: Mapped[uuid.UUID] = fk("employees.id")
    entity_type: Mapped[str | None] = mapped_column(String(40))
    entity_id: Mapped[uuid.UUID | None] = mapped_column()
    priority: Mapped[str] = mapped_column(String(10))  # low, medium, high
    due_on: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)  # open, done


class Risk(Base):
    __tablename__ = "risks"

    rule_id: Mapped[str] = mapped_column(String(60), index=True)  # id from config/risk_rules.yaml
    category: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(10), index=True)  # low, medium, high
    title: Mapped[str] = mapped_column(String(255))
    facts_json: Mapped[dict] = mapped_column(JSON)  # the "Observed" numbers
    entity_refs_json: Mapped[list] = mapped_column(JSON)  # clickable linked entities
    suggested_action: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)  # open, acknowledged, resolved
    owner_employee_id: Mapped[uuid.UUID | None] = fk("employees.id", nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
