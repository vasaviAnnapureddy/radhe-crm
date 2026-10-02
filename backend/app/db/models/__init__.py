"""Import every model here so Alembic and the tests can see all tables."""
from app.db.base import Base
from app.db.models.access import AuditLog, User
from app.db.models.construction import (
    ConstructionMilestone,
    Contractor,
    ProjectBudget,
    QualityIssue,
    SafetyIncident,
)
from app.db.models.interactions import CustomerInteraction, Risk, Task
from app.db.models.organisation import Department, Employee, EmployeeTarget
from app.db.models.payments import Demand, HomeLoan, PaymentPlan, PlanMilestone, Receipt
from app.db.models.projects import PriceHistory, Project, Tower, Unit
from app.db.models.sales import (
    Booking,
    ChannelPartner,
    CpCommission,
    Customer,
    Lead,
    LeadActivity,
    SiteVisit,
)
from app.db.models.service import InteriorProject, ServiceTicket

__all__ = [
    "Base", "User", "AuditLog", "Department", "Employee", "EmployeeTarget",
    "Project", "Tower", "Unit", "PriceHistory",
    "ChannelPartner", "Lead", "LeadActivity", "SiteVisit", "Customer", "Booking", "CpCommission",
    "PaymentPlan", "PlanMilestone", "Demand", "Receipt", "HomeLoan",
    "Contractor", "ConstructionMilestone", "ProjectBudget", "QualityIssue", "SafetyIncident",
    "InteriorProject", "ServiceTicket", "CustomerInteraction", "Task", "Risk",
]
