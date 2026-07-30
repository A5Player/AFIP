import json
from pathlib import Path

from afip.holding_intelligence import (
    EXIT_REVIEW,
    HOLD,
    PROTECT_PROFIT,
    REDUCE_EXPOSURE,
    WAIT_DATA,
    HoldingContext,
    HoldingIntelligenceRuntime,
)


def _item(**changes):
    base = dict(
        position_id="position-001",
        adaptive_sl_status="NORMAL_SL_APPROVED",
        data_integrity_pass=True,
        risk_pass=True,
        execution_pass=True,
        trend_continuity_score=88,
        structure_integrity_score=90,
        regime_stability_score=85,
        momentum_score=82,
        exit_evidence_score=20,
        mfe_points=300,
        mae_points=-80,
        unrealized_points=220,
        protected_points=100,
        holding_minutes=60,
        expected_holding_minutes=180,
        news_risk_high=False,
        spread_abnormal=False,
    )
    base.update(changes)
    return HoldingContext(**base)


def test_strong_context_supports_hold():
    result = HoldingIntelligenceRuntime().assess(_item())
    assert result.action == HOLD
    assert result.reason == "holding_evidence_supported"


def test_profit_protection_for_unprotected_profit_or_market_risk():
    runtime = HoldingIntelligenceRuntime()
    unprotected = runtime.assess(_item(unrealized_points=400, protected_points=50))
    assert unprotected.action == PROTECT_PROFIT

    risk = runtime.assess(_item(news_risk_high=True))
    assert risk.action == PROTECT_PROFIT
    assert risk.reason == "market_risk_protection_required"


def test_degraded_context_reduces_exposure():
    result = HoldingIntelligenceRuntime().assess(
        _item(trend_continuity_score=45, exit_evidence_score=65)
    )
    assert result.action == REDUCE_EXPOSURE
    assert result.reason == "holding_evidence_degraded"


def test_dominant_exit_evidence_escalates_to_exit_review():
    runtime = HoldingIntelligenceRuntime()
    result = runtime.assess(_item(exit_evidence_score=85))
    assert result.action == EXIT_REVIEW

    authority = runtime.assess(_item(risk_pass=False))
    assert authority.action == EXIT_REVIEW
    assert authority.reason == "independent_authority_not_approved"


def test_fail_closed_and_no_execution_authority():
    runtime = HoldingIntelligenceRuntime()
    waiting = runtime.assess(_item(adaptive_sl_status="NOT_ELIGIBLE"))
    assert waiting.action == WAIT_DATA

    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "holding_intelligence_runtime_contract.json").read_text(encoding="utf-8")
    )
    assert contract["fail_closed"] is True

    result = runtime.assess(_item())
    assert result.order_modify_called is False
    assert result.order_close_called is False
    assert result.execution_authority is False
