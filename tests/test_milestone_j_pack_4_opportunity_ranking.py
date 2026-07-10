from datetime import datetime, timezone
from afip.opportunity_ranking import OpportunityRankingRuntime
from afip.dashboard_ui.runtime import DashboardUIRuntime


def _candidate(identifier, score, *, direction="BUY", risk=1.0, cost=1.0, conflict="LOW"):
    return {"opportunity_id": identifier, "symbol": "GOLD#", "direction": direction, "regime_score": score, "consensus_score": score, "structure_score": score, "timing_score": score, "risk_score": risk, "cost_score": cost, "conflict_level": conflict}


def test_ranks_highest_eligible_first():
    report = OpportunityRankingRuntime().evaluate_one({"opportunities": [_candidate("B", .70), _candidate("A", .90)]})
    assert report.top_opportunity_id == "A"
    assert report.ranked_opportunities[0].rank == 1


def test_high_conflict_is_ineligible():
    report = OpportunityRankingRuntime().evaluate_one({"opportunities": [_candidate("A", .95, conflict="HIGH")]})
    assert report.status == "WAITING"
    assert report.eligible_count == 0


def test_risk_and_cost_are_gates():
    report = OpportunityRankingRuntime().evaluate_one({"opportunities": [_candidate("R", .95, risk=0.0), _candidate("C", .95, cost=0.0)]})
    assert not any(item.eligible for item in report.ranked_opportunities)


def test_deterministic_tie_breaker():
    report = OpportunityRankingRuntime().evaluate_one({"opportunities": [_candidate("B", .80), _candidate("A", .80)]})
    assert [item.opportunity_id for item in report.ranked_opportunities] == ["A", "B"]


def test_direct_execution_is_disabled_and_review_time_is_deterministic():
    now = datetime(2026, 7, 10, 6, 0, tzinfo=timezone.utc)
    report = OpportunityRankingRuntime().evaluate_one({"current_time_utc": now, "opportunities": [_candidate("A", .90)]})
    assert report.direct_execution is False
    assert report.next_review_time_utc == "2026-07-10T06:10:00+00:00"


def test_dashboard_contains_bilingual_opportunity_panel():
    report = DashboardUIRuntime().evaluate_one({"broker":"XM", "symbol":"GOLD#", "mode":"PAPER", "opportunities": [_candidate("A", .90)]})
    panel = next(item for item in report.panels if item.panel_id == "opportunity_ranking")
    assert panel.title_en == "Opportunity Ranking Engine"
    assert panel.title_th == "กลไกจัดอันดับโอกาส"
