from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_intelligence_complete import MarketIntentIntelligenceCompletionRuntime


def _report(index: int, **overrides):
    payload = {
        "review_certification_id": f"QREV-{index:016X}", "status": "READY", "milestone": "Q", "pack": "9",
        "certification_timestamp": 50000 + index * 1000,
        "governance_report_count": 3, "total_calibration_report_count": 9,
        "total_validation_window_count": 81, "research_review_score": 94.0,
        "market_intent_review_certified": True, "milestone_q_completion_candidate": True,
        "review_required": False, "data_quality_certified": True, "future_safe": True,
        "market_regime_before_intent": True, "market_behaviour_before_intent": True,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False, "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False, "production_certification_granted": False,
        "release_candidate_granted": False,
    }
    payload.update(overrides)
    return payload


def _reports():
    return [_report(1), _report(2), _report(3)]


def test_milestone_q_completes_deterministically():
    result = MarketIntentIntelligenceCompletionRuntime().complete_many(_reports(), completion_timestamp=60000)
    assert result.status == "COMPLETE"
    assert result.completion_id.startswith("QCOMP-")
    assert result.milestone_q_complete is True
    assert result.next_milestone == "R_PRODUCTION_CERTIFICATION"
    assert result.review_required is False


def test_completion_report_is_immutable_and_repeatable():
    runtime = MarketIntentIntelligenceCompletionRuntime()
    first = runtime.complete_many(_reports(), completion_timestamp=60000)
    assert first == runtime.complete_many(_reports(), completion_timestamp=60000)
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_lineage_and_duplicate_ids():
    rows = _reports()
    rows[0]["pack"] = "8"
    rows[1]["review_certification_id"] = rows[0]["review_certification_id"]
    result = MarketIntentIntelligenceCompletionRuntime().complete_many(rows, completion_timestamp=60000)
    assert "pack_9_lineage_invalid" in result.block_reasons
    assert "duplicate_or_invalid_pack_9_review_certification_id" in result.block_reasons


def test_blocks_uncertified_candidate_and_pending_review():
    rows = _reports()
    rows[1].update(status="BLOCKED", market_intent_review_certified=False, milestone_q_completion_candidate=False, review_required=True)
    result = MarketIntentIntelligenceCompletionRuntime().complete_many(rows, completion_timestamp=60000)
    assert "pack_9_review_not_certified" in result.block_reasons
    assert "pack_9_completion_candidate_missing" in result.block_reasons
    assert "market_intent_review_pending" in result.block_reasons


def test_blocks_insufficient_count_low_score_and_bad_chronology():
    rows = [_report(2, research_review_score=60.0), _report(1)]
    result = MarketIntentIntelligenceCompletionRuntime().complete_many(
        rows, completion_timestamp=20000, minimum_certificate_count=3, minimum_review_score=75.0,
    )
    assert "minimum_review_certificate_count_not_met" in result.block_reasons
    assert "minimum_research_review_score_not_met" in result.block_reasons
    assert "market_intent_completion_chronology_invalid" in result.block_reasons


def test_blocks_invalid_metrics():
    rows = _reports()
    rows[0]["research_review_score"] = float("nan")
    result = MarketIntentIntelligenceCompletionRuntime().complete_many(rows, completion_timestamp=60000)
    assert "market_intent_completion_metrics_invalid" in result.block_reasons


def test_blocks_quality_future_prerequisite_and_policy_failures():
    rows = _reports()
    rows[0]["data_quality_certified"] = False
    rows[1]["future_safe"] = False
    rows[1]["market_regime_before_intent"] = False
    rows[2]["market_behaviour_before_intent"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketIntentIntelligenceCompletionRuntime().complete_many(rows, completion_timestamp=60000)
    assert "data_quality_not_certified" in result.block_reasons
    assert "future_leakage_detected" in result.block_reasons
    assert "market_regime_not_evaluated_before_intent" in result.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_production_release_and_execution_authority_stay_disabled():
    result = MarketIntentIntelligenceCompletionRuntime().complete_many(_reports(), completion_timestamp=60000)
    assert result.research_only is True
    assert result.production_certification_granted is False
    assert result.release_candidate_granted is False
    assert result.automatic_parameter_update_allowed is False
    assert result.trading_logic_change_allowed is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
