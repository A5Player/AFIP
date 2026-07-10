from datetime import datetime, timezone
from afip.trade_scoring import TradeScoringRuntime
from afip.dashboard_ui.runtime import DashboardUIRuntime


def _candidate(identifier, total=.9, quality=.9, risk=.9, execution=.9, *, eligible=True, direction="BUY"):
    return {"opportunity_id": identifier, "symbol": "GOLD#", "direction": direction, "total_score": total, "quality_score": quality, "risk_adjusted_score": risk, "execution_readiness_score": execution, "eligible": eligible}


def test_highest_eligible_score_is_top():
    report = TradeScoringRuntime().evaluate_one({"ranked_opportunities": [_candidate("B", .8), _candidate("A", .95)]})
    assert report.top_opportunity_id == "A"
    assert report.status == "READY"


def test_upstream_ineligible_candidate_remains_blocked():
    report = TradeScoringRuntime().evaluate_one({"ranked_opportunities": [_candidate("A", .95, eligible=False)]})
    assert report.eligible_count == 0
    assert report.status == "WAITING"


def test_reject_grade_blocks_candidate():
    report = TradeScoringRuntime().evaluate_one({"ranked_opportunities": [_candidate("A", .2, .2, .2, .2)]})
    assert report.scores[0].grade == "REJECT"
    assert not report.scores[0].eligible


def test_tie_breaking_is_deterministic():
    report = TradeScoringRuntime().evaluate_one({"ranked_opportunities": [_candidate("B"), _candidate("A")]})
    assert [x.opportunity_id for x in report.scores] == ["A", "B"]


def test_direct_execution_disabled_and_review_time_deterministic():
    now = datetime(2026, 7, 10, 7, 0, tzinfo=timezone.utc)
    report = TradeScoringRuntime().evaluate_one({"current_time_utc": now, "ranked_opportunities": [_candidate("A")]})
    assert report.direct_execution is False
    assert report.next_review_time_utc == "2026-07-10T07:10:00+00:00"


def test_dashboard_contains_bilingual_trade_scoring_panel():
    report = DashboardUIRuntime().evaluate_one({"broker":"XM", "symbol":"GOLD#", "mode":"PAPER", "opportunities": [_candidate("A")]})
    panel = next(item for item in report.panels if item.panel_id == "trade_scoring")
    assert panel.title_en == "Trade Scoring Engine"
    assert panel.title_th == "กลไกให้คะแนนการซื้อขาย"
