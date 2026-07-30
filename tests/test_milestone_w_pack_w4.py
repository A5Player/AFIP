from pathlib import Path
import json
import pytest

from afip.trading_plan_selection import (
    TradingPlanSelectionError,
    TradingPlanSelector,
    TradingPlanTemplate,
)


def plan(**changes):
    data = dict(
        plan_id="BREAKOUT_RETEST_SELECTIVE",
        plan_family="SELECTIVE_CONTINUATION",
        supported_strategy_ids=("BREAKOUT_RETEST_CONTINUATION",),
        minimum_strategy_score=80,
        minimum_evidence_count=3,
        minimum_total_sample_size=100,
        minimum_evidence_quality_score=70,
    )
    data.update(changes)
    return TradingPlanTemplate(**data)


def candidate(**changes):
    data = dict(
        strategy_id="BREAKOUT_RETEST_CONTINUATION",
        strategy_family="CONTINUATION",
        advisory_score=91,
        status="ELIGIBLE_FOR_PLAN_REVIEW",
        evidence_count=5,
        total_sample_size=500,
        weighted_similarity=94,
        weighted_win_rate=83,
        weighted_expectancy=2.4,
        evidence_quality_score=90,
        authority="ADVISORY_ONLY",
        execution_authority=False,
        order_send_allowed=False,
        lot_authority=False,
        sl_tp_authority=False,
    )
    data.update(changes)
    return data


def test_strong_strategy_selects_plan_for_oqs_review_only():
    result = TradingPlanSelector().evaluate(plan(), candidate())
    assert result.status == "ELIGIBLE_FOR_OQS_REVIEW"
    assert result.authority == "ADVISORY_ONLY"
    assert result.final_decision_authority is False
    assert result.execution_authority is False and result.order_send_allowed is False


def test_unsupported_or_ineligible_strategy_fails_closed():
    unsupported = TradingPlanSelector().evaluate(plan(), candidate(strategy_id="REVERSAL"))
    ineligible = TradingPlanSelector().evaluate(plan(), candidate(status="WAIT"))
    assert unsupported.status == "WAIT" and "strategy_not_supported_by_plan" in unsupported.reasons
    assert ineligible.status == "WAIT" and "strategy_not_eligible_for_plan_review" in ineligible.reasons


def test_insufficient_evidence_fails_closed():
    result = TradingPlanSelector().evaluate(plan(), candidate(evidence_count=2, total_sample_size=60))
    assert result.status == "WAIT"
    assert "evidence_count_below_plan_minimum" in result.reasons


def test_forbidden_upstream_authority_is_rejected():
    with pytest.raises(TradingPlanSelectionError, match="upstream_candidate_claims_forbidden_authority"):
        TradingPlanSelector().evaluate(plan(), candidate(order_send_allowed=True))


def test_contract_forbids_trading_authority():
    path = Path(__file__).resolve().parents[1] / "config/trading_plan_selection_contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    assert contract["maximum_output_status"] == "ELIGIBLE_FOR_OQS_REVIEW"
    assert contract["final_decision_authority"] is False
    assert contract["execution_authority"] is False
    assert contract["order_send_allowed"] is False
    assert contract["lot_authority"] is False
    assert contract["final_sl_tp_authority"] is False
    assert contract["bypass_gate_allowed"] is False
