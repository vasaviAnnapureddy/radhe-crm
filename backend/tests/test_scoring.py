"""Unit tests for the score formulas. They use plain numbers, no database."""
from app.scoring.scores import CFG, buyer_health, lead_score, linear, project_health, scorecard


def test_linear_is_clamped():
    assert linear(7, 7, 45) == 1.0
    assert linear(45, 7, 45) == 0.0
    assert linear(100, 7, 45) == 0.0
    assert linear(26, 7, 45) == 0.5


def test_every_set_of_weights_adds_up_to_100():
    for name in ("buyer_health", "lead_score", "project_health"):
        assert sum(CFG[name]["weights"].values()) == 100, name
    for role, weights in CFG["employee_scorecard"]["roles"].items():
        assert sum(weights.values()) == 100, role


def test_buyer_health_perfect_buyer_scores_100():
    result = buyer_health(on_time=5, payments=5, worst_overdue_days=0, days_since_contact=3, open_tickets=0,
                          unanswered=0, loan_status=None)
    assert result["score"] == 100 and result["band"] == "good"
    assert [p["points"] for p in result["parts"]] == [40, 25, 20, 15]


def test_buyer_health_unhappy_buyer_like_karthik():
    # 3 of 5 payments on time, no contact for 41 days, 1 open complaint, 3 unanswered emails, no loan.
    result = buyer_health(3, 5, 0, 41, 1, 3, None)
    points = {p["key"]: p["points"] for p in result["parts"]}
    assert points == {"payment_timeliness": 24.0, "engagement_recency": 2.6, "open_complaints": 0.0, "loan_status": 15.0}
    assert result["score"] == 42 and result["band"] == "risk"


def test_buyer_health_overdue_and_waiting_on_bank():
    result = buyer_health(4, 4, 90, 7, 0, 0, "awaiting_disbursement")
    points = {p["key"]: p["points"] for p in result["parts"]}
    assert points["payment_timeliness"] == 0.0  # 90 days overdue wipes out the payment points
    assert points["loan_status"] == 5.0  # 15 x 0.33, rounded to one decimal


def test_lead_score_best_and_worst():
    assert lead_score(1.0, 1.0, 1.0, 0)["score"] == 100
    assert lead_score(0.0, 0.0, 0.0, 60)["score"] == 0


def test_project_health_perfect_and_late():
    assert project_health(0, 0, 1.0, 100, 0)["score"] == 100
    late = {p["key"]: p["points"] for p in project_health(45, 20, 0.5, 80, 2)["parts"]}
    assert late == {"schedule_variance": 0.0, "cost_variance": 0.0, "sales_velocity": 12.5,
                    "collection_efficiency": 0.0, "open_high_risks": 0.0}


def test_scorecard_weights_achievement_and_caps_at_100():
    card = scorecard("sales", [
        ("bookings_vs_target", "Bookings", 9, 18, 2.0, "number"),   # 200% is capped at 100%
        ("site_visits", "Site visits", 75, 0, 0.0, "number"),
        ("conversion", "Conversion", 11, 5.5, 0.5, "percent"),
        ("stalled_deals", "Stalled", 0, 9, -0.8, "number"),          # below zero is floored at 0%
    ])
    assert [p["achievement_pct"] for p in card["parts"]] == [100, 0, 50, 0]
    assert card["score"] == 52  # 40 + 0 + 12.5 + 0, rounded
    assert card["needs_attention"] is True
