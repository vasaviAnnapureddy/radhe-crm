"""Access: the admin user and a log of the few writes the console allows."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, fk


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))  # argon2 hash, never the password
    role: Mapped[str] = mapped_column(String(20), default="admin")  # admin, employee, customer
    # Portal logins point at the one person they belong to. The server uses this, never an id from the browser.
    employee_id: Mapped[uuid.UUID | None] = fk("employees.id", nullable=True)
    customer_id: Mapped[uuid.UUID | None] = fk("customers.id", nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True)
    action: Mapped[str] = mapped_column(String(60), index=True)  # login, logout, risk_status_change
    entity_type: Mapped[str | None] = mapped_column(String(40))
    entity_id: Mapped[uuid.UUID | None] = mapped_column()
    details_json: Mapped[dict | None] = mapped_column(JSON)
