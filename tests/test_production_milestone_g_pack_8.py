from afip.runtime.production_milestone_g_production_release_candidate_runtime import (
    evaluate_production_release_candidate_record,
    evaluate_production_release_candidate_records,
    explain_production_release_candidate_record,
)
from afip.production_release_candidate import ProductionReleaseCandidateObservation


def _record(**overrides):
    data = {
        "market_regime": "trend",
        "signal_context": "sell_edge",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "configuration_version": "v7",
        "long_run_score": 86,
        "production_hardening_score": 84,
        "paper_trading_score": 80,
        "observability_score": 82,
        "feature_flag_score": 78,
        "event_log_score": 80,
        "deployment_checklist_score": 88,
        "release_notes_score": 79,
        "rollback_plan_score": 81,
        "operator_handoff_score": 83,
        "unresolved_reviews": 0,
    }
    data.update(overrides)
    return data


def test_production_release_candidate_blocks_records_without_market_regime():
    profile = evaluate_production_release_candidate_record(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"


def test_production_release_candidate_blocks_live_execution_mode():
    profile = evaluate_production_release_candidate_record(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_release_candidate"
    assert profile.readiness_gate == "BLOCKED"


def test_production_release_candidate_preserves_regime_before_signal_context():
    first, second = evaluate_production_release_candidate_records([
        _record(market_regime="trend", signal_context="buy_edge"),
        _record(market_regime="range", signal_context="sell_edge"),
    ])

    assert first.market_regime == "TREND"
    assert first.signal_context == "BUY_EDGE"
    assert second.market_regime == "RANGE"
    assert second.signal_context == "SELL_EDGE"


def test_production_release_candidate_calculates_scores_deterministically():
    first = evaluate_production_release_candidate_record(_record())
    second = evaluate_production_release_candidate_record(_record())

    assert first.status == "READY"
    assert first.reason == "production_release_candidate_ready"
    assert first.release_evidence_quality == second.release_evidence_quality
    assert first.production_release_score == second.production_release_score
    assert first.readiness_gate == "PRODUCTION_RELEASE_CANDIDATE_READY"


def test_production_release_candidate_requires_review_for_unresolved_items():
    profile = evaluate_production_release_candidate_record(_record(unresolved_reviews=1))

    assert profile.status == "REVIEW"
    assert profile.reason == "unresolved_review_required"
    assert profile.readiness_gate == "REVIEW_REQUIRED"


def test_production_release_candidate_report_and_observation_normalizes_percent_values():
    observation = ProductionReleaseCandidateObservation.from_mapping(_record(long_run_score=75, deployment_checklist_score=91))
    report = explain_production_release_candidate_record(_record())
    text = report.as_text()

    assert observation.long_run_score == 0.75
    assert observation.deployment_checklist_score == 0.91
    assert observation.production_release_score <= 1.0
    assert "Production Release Candidate Report" in text
    assert "Execution mode: LOCKED_SIMULATION_ONLY" in text
    assert "Readiness gate: PRODUCTION_RELEASE_CANDIDATE_READY" in text
    assert "Decision reason: production_release_candidate_ready" in text
