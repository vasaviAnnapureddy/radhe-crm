"""Proves the scale and each of the 7 planted stories exist after seeding (on a throwaway SQLite database)."""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Base, Booking, ChannelPartner, ConstructionMilestone, Contractor, CpCommission, Customer,
    CustomerInteraction, Demand, Employee, HomeLoan, InteriorProject, Lead, LeadActivity, Project,
    Receipt, ServiceTicket, SiteVisit, Tower, Unit,
)
from seed import stories as S
from seed.build import build_world, insert_rows

TODAY = date.today()
CR = S.CR


@pytest.fixture(scope="module")
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        insert_rows(conn, build_world(TODAY).rows)
    with Session(engine) as session:
        yield session


def count(db, model, *where) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*where))


def active_buyers_by_rm(db) -> dict:
    rows = db.execute(select(Customer.rm_employee_id, func.count(Customer.id.distinct()))
                      .join(Booking, Booking.customer_id == Customer.id).where(Booking.status != "cancelled")
                      .group_by(Customer.rm_employee_id)).all()
    return dict(rows)


def outstanding_60_plus(db) -> list:
    """(customer id, booking id, amount still unpaid) for demands 60+ days past their due date."""
    paid = select(Receipt.demand_id, func.sum(Receipt.amount).label("paid")).group_by(Receipt.demand_id).subquery()
    rows = db.execute(select(Booking.customer_id, Booking.id, Demand.amount - func.coalesce(paid.c.paid, 0))
                      .join(Booking, Booking.id == Demand.booking_id)
                      .outerjoin(paid, paid.c.demand_id == Demand.id)
                      .where(Demand.due_on <= TODAY - timedelta(days=60), Booking.status != "cancelled")).all()
    return [(c, b, float(left)) for c, b, left in rows if left > 0]


def test_scale(db):
    assert count(db, Project) == 5
    assert count(db, Unit) == 1600
    assert count(db, Lead) == S.TOTAL_LEADS
    assert count(db, Booking) == S.TOTAL_BOOKINGS
    assert count(db, Employee) == 110
    assert count(db, ChannelPartner) == 30
    assert count(db, Contractor) == 12
    assert db.scalar(select(func.count(HomeLoan.bank.distinct()))) == 8


def test_story_1_tower_b_delay(db):
    stage, contractor = db.execute(
        select(ConstructionMilestone, Contractor.name)
        .join(Tower, Tower.id == ConstructionMilestone.tower_id).join(Project, Project.id == Tower.project_id)
        .join(Contractor, Contractor.id == ConstructionMilestone.contractor_id)
        .where(Project.name == S.DELAY_PROJECT, Tower.name == S.DELAY_TOWER,
               ConstructionMilestone.type == S.DELAY_MILESTONE)).one()
    assert stage.actual_date is None
    assert (TODAY - stage.planned_date).days == S.DELAY_SLIP_DAYS
    assert contractor == S.DELAY_CONTRACTOR and "steel" in stage.delay_cause

    bookings, amount = db.execute(
        select(func.count(Demand.booking_id.distinct()), func.sum(Demand.amount))
        .where(Demand.construction_milestone_id == stage.id, Demand.status == "not_raised")).one()
    assert bookings == S.DELAY_BLOCKED_BOOKINGS
    assert 6.7 * CR <= float(amount) <= 6.9 * CR

    # It is the only stage that is past its planned date and still open.
    assert count(db, ConstructionMilestone, ConstructionMilestone.actual_date.is_(None),
                 ConstructionMilestone.planned_date < TODAY) == 1


def test_story_2_unhappy_nri_buyer_and_overloaded_rm(db):
    karthik = db.scalars(select(Customer).where(Customer.name == S.KARTHIK)).one()
    assert karthik.is_nri and karthik.city == "Dallas"
    booking, unit, tower = db.execute(
        select(Booking, Unit, Tower.name).join(Unit, Unit.id == Booking.unit_id).join(Tower, Tower.id == Unit.tower_id)
        .where(Booking.customer_id == karthik.id)).one()
    assert (unit.config, tower) == ("4 BHK", S.DELAY_TOWER)

    paid = db.scalar(select(func.sum(Receipt.amount)).join(Demand, Demand.id == Receipt.demand_id)
                     .where(Demand.booking_id == booking.id))
    assert abs(float(paid) / float(booking.agreement_value) - 0.45) < 0.005

    emails = db.scalars(select(CustomerInteraction.occurred_at).where(
        CustomerInteraction.customer_id == karthik.id, CustomerInteraction.direction == "inbound",
        CustomerInteraction.needs_reply, CustomerInteraction.replied_at.is_(None))).all()
    assert len(emails) == 3
    assert (TODAY - min(emails).date()).days == 12
    assert count(db, ServiceTicket, ServiceTicket.customer_id == karthik.id, ServiceTicket.status == "open") == 1

    sneha = db.scalars(select(Employee).where(Employee.name == S.SNEHA)).one()
    assert karthik.rm_employee_id == sneha.id
    load = active_buyers_by_rm(db)
    average = sum(load.values()) / len(load)
    assert load[sneha.id] == S.SNEHA_BUYERS
    assert 37 <= average <= 39
    assert [rm for rm, n in load.items() if n > 1.5 * average] == [sneha.id]


def test_story_3_stuck_sales_manager(db):
    arjun = db.scalars(select(Employee).where(Employee.name == S.ARJUN)).one()
    visits = dict(db.execute(select(SiteVisit.employee_id, func.count()).where(SiteVisit.status == "done")
                             .group_by(SiteVisit.employee_id)).all())
    bookings = dict(db.execute(select(Booking.employee_id, func.count()).group_by(Booking.employee_id)).all())
    assert visits[arjun.id] >= 30
    assert 0.035 <= bookings[arjun.id] / visits[arjun.id] <= 0.045
    assert 0.10 <= sum(bookings.values()) / sum(visits.values()) <= 0.125

    last_activity = (select(LeadActivity.lead_id, func.max(LeadActivity.occurred_at).label("last"))
                     .group_by(LeadActivity.lead_id).subquery())
    rows = db.execute(select(Lead.budget_max, last_activity.c.last)
                      .join(last_activity, last_activity.c.lead_id == Lead.id)
                      .where(Lead.owner_employee_id == arjun.id, Lead.stage == "negotiation")).all()
    idle = [float(budget) for budget, last in rows
            if (TODAY - datetime.fromisoformat(str(last)).date()).days >= 14]
    assert len(idle) == 9
    assert 13.5 * CR <= sum(idle) <= 14.5 * CR


def test_story_4_star_channel_partner(db):
    skyway = db.scalars(select(ChannelPartner).where(ChannelPartner.firm_name == S.SKYWAY)).one()
    villas = db.execute(select(Booking.channel_partner_id).join(Unit, Unit.id == Booking.unit_id)
                        .join(Project, Project.id == Unit.project_id)
                        .where(Project.type == "villas", Booking.status != "cancelled",
                               Booking.booked_on >= date(TODAY.year, 1, 1))).scalars().all()
    assert 0.29 <= villas.count(skyway.id) / len(villas) <= 0.33

    late = (CpCommission.paid_on.is_(None), CpCommission.due_on <= TODAY - timedelta(days=45))
    assert count(db, CpCommission, CpCommission.channel_partner_id == skyway.id, *late) >= 3
    assert count(db, CpCommission, CpCommission.channel_partner_id != skyway.id, *late) == 0


def test_story_5_ageing_inventory(db):
    old = db.execute(select(Unit, Project.name).join(Project, Project.id == Unit.project_id)
                     .where(Unit.status == "available", Unit.listed_on <= TODAY - timedelta(days=270))).all()
    assert len(old) == S.AGEING_UNITS
    for unit, project in old:
        assert project == S.AGEING_PROJECT and unit.facing == "West" and 2 <= unit.floor <= 4
        assert (TODAY - unit.listed_on).days >= 300


def test_story_6_bank_bottleneck(db):
    overdue = outstanding_60_plus(db)
    assert len({customer for customer, _, _ in overdue}) == S.OVERDUE_BUYERS
    assert 4.1 * CR <= sum(left for _, _, left in overdue) <= 4.3 * CR

    waiting = db.execute(select(HomeLoan.bank, func.count()).where(
        HomeLoan.booking_id.in_([booking for _, booking, _ in overdue]),
        HomeLoan.status == "awaiting_disbursement").group_by(HomeLoan.bank)).all()
    assert waiting == [(S.BOTTLENECK_BANK, S.BOTTLENECK_BUYERS)]


def test_story_7_interiors_upsell(db):
    handover_soon = (select(ConstructionMilestone.tower_id).where(
        ConstructionMilestone.type == "handover", ConstructionMilestone.actual_date.is_(None),
        ConstructionMilestone.planned_date <= TODAY + timedelta(days=180)))
    buyers = set(db.scalars(select(Booking.customer_id).join(Unit, Unit.id == Booking.unit_id)
                            .where(Unit.tower_id.in_(handover_soon), Booking.status != "cancelled")).all())
    with_package = set(db.scalars(select(InteriorProject.customer_id)).all())
    without = buyers - with_package
    assert len(without) == S.UPSELL_BUYERS

    average_package = float(db.scalar(select(func.avg(InteriorProject.value))))
    assert 8.5 * CR <= len(without) * average_package <= 9.5 * CR
