"""The risk engine must surface all 7 planted stories, with clickable entities."""
from app.db.models import Customer, Risk
from app.scoring.scores import customer_health
from app.services.entities import ENTITIES
from seed import stories as S


def risks_of(snapshot, rule_id: str) -> list:
    return [r for r in snapshot.all(Risk) if r.rule_id == rule_id]


def labels(risk) -> list[str]:
    return [e["label"] for e in risk.entity_refs_json]


def test_story_1_tower_b_delay_is_a_high_risk(snapshot):
    (risk,) = risks_of(snapshot, "milestone_slip_blocks_demands")
    assert risk.severity == "high" and risk.category == "Construction"
    assert risk.title == "Tower B delay blocks ₹6.8 Cr in demands"
    assert S.DELAY_CONTRACTOR in labels(risk)


def test_story_2_karthik_and_sneha(snapshot):
    karthik = next(c for c in snapshot.all(Customer) if c.name == S.KARTHIK)
    assert 36 <= customer_health(snapshot, karthik)["score"] <= 46
    unanswered = risks_of(snapshot, "buyer_query_unanswered")
    mine = next(r for r in unanswered if S.KARTHIK in labels(r))
    assert mine.severity == "high" and S.SNEHA in labels(mine)
    assert len(unanswered) == 6
    (workload,) = risks_of(snapshot, "rm_workload_high")
    assert workload.title == f"{S.SNEHA} handles 62 buyers vs team average 38"


def test_story_3_arjun(snapshot):
    idle = [r for r in risks_of(snapshot, "negotiation_idle_high_value") if S.ARJUN in r.title]
    assert len(idle) == 1 and idle[0].title.startswith("9 negotiations idle 14+ days, ₹14 Cr at risk")
    (low,) = risks_of(snapshot, "sales_low_conversion")
    assert S.ARJUN in low.title


def test_story_4_skyway(snapshot):
    (risk,) = risks_of(snapshot, "cp_commission_pending")
    assert S.SKYWAY in risk.title
    share = next(f["value"] for f in risk.facts_json["items"] if "villa" in f["label"])
    assert 29 <= share <= 33


def test_story_5_ageing_inventory(snapshot):
    (risk,) = risks_of(snapshot, "unit_unsold_ageing")
    assert risk.title == "22 units at Radhe Greens unsold for 270+ days"


def test_story_6_bank_bottleneck(snapshot):
    (risk,) = risks_of(snapshot, "bank_disbursement_bottleneck")
    assert risk.title == f"6 buyers overdue 60+ days are waiting on {S.BOTTLENECK_BANK} disbursement"
    assert len(risks_of(snapshot, "buyer_overdue")) == S.OVERDUE_BUYERS


def test_story_7_interiors_upsell(snapshot):
    (risk,) = risks_of(snapshot, "interiors_upsell")
    assert risk.title.startswith("63 buyers near possession have no interior package")


def test_every_linked_entity_can_be_opened(snapshot):
    for risk in snapshot.all(Risk):
        assert risk.entity_refs_json, risk.title
        for entity in risk.entity_refs_json:
            assert entity["type"] in ENTITIES and entity["label"], risk.title
