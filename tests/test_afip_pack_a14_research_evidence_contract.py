from __future__ import annotations

import json
from pathlib import Path

import pytest

from afip.research_standardization.capital_profit import (
    InitialCapitalObservation,
    SingleUnitProfitObservation,
)
from afip.research_standardization.runtime import (
    ATRBufferCandidate,
    ATRBufferPatternObservation,
    PatternResearchIdentity,
    PatternShapeSignature,
)


def _identity() -> PatternResearchIdentity:
    return PatternResearchIdentity(
        symbol="GOLD#", timeframe="M15", pattern_family="STRUCTURE",
        pattern_name="CLOSED_BAR_TEST", pattern_variant="V1", direction="BUY",
        market_regime="TREND", trend_state="UP", momentum_state="POSITIVE",
        volatility_state="NORMAL", trading_session="LONDON", liquidity_state="NORMAL",
        multi_timeframe_context="H1_UP", entry_plan="SINGLE_ENTRY",
        management_plan="STRUCTURE_CARE", exit_plan="RESEARCH_TP",
    )


def _shape() -> PatternShapeSignature:
    return PatternShapeSignature(4, 3600, .5, .2, .2, .5, 1.0, .5)


def test_blind_forward_outcome_is_explicit_but_decision_future_data_is_forbidden() -> None:
    observation = ATRBufferPatternObservation(
        "PATTERN-1", 1, "SEGMENT-1", ATRBufferCandidate(1, 0, "PLUS", 1, 0, "PLUS"),
        10.0, "WIN", research_identity=_identity(), shape_signature=_shape(),
        cross_market_context_id="GOLD_ONLY", future_data_used=False,
        outcome_evaluation_uses_subsequent_closed_bars=True,
    )
    assert observation.outcome_evaluation_uses_subsequent_closed_bars is True
    with pytest.raises(ValueError, match="free of future data"):
        ATRBufferPatternObservation(
            "PATTERN-2", 2, "SEGMENT-1", ATRBufferCandidate(1, 0, "PLUS", 1, 0, "PLUS"),
            10.0, "WIN", research_identity=_identity(), shape_signature=_shape(),
            cross_market_context_id="GOLD_ONLY", future_data_used=True,
        )


def test_profit_and_capital_require_explicit_blind_forward_labels() -> None:
    common = dict(pattern_id="PATTERN-3", pattern_sequence=3, research_identity=_identity(),
                  shape_signature=_shape(), cross_market_context_id="GOLD_ONLY")
    with pytest.raises(ValueError, match="subsequent closed bars"):
        SingleUnitProfitObservation(
            **common, exit_policy_id="FIXED_RESEARCH_TP", policy_parameters={"tp": 1}, outcome="WIN",
            net_points=1, maximum_favorable_points=2, maximum_adverse_points=1,
            captured_profit_points=1, peak_giveback_points=1, holding_seconds=60,
            break_even_exit=False, transaction_cost_points=0, outcome_evaluation_uses_subsequent_closed_bars=False,
        )
    with pytest.raises(ValueError, match="subsequent closed bars"):
        InitialCapitalObservation(
            **common, starting_capital_usd=100, required_margin_usd=1, approved_risk_usd=1,
            maximum_adverse_equity_usd=1, realized_pnl_usd=1, transaction_cost_usd=0,
            survived=True, margin_failure=False, risk_budget_failure=False,
            outcome_evaluation_uses_subsequent_closed_bars=False,
        )


def test_policies_and_generated_dashboards_declare_safe_live_refresh() -> None:
    root = Path(__file__).resolve().parents[1]
    for name in (
        "atr_buffer_research_policy.json", "single_unit_profit_research_policy.json",
        "initial_capital_research_policy.json",
    ):
        policy = json.loads((root / "config" / "research_metrics" / name).read_text(encoding="utf-8"))
        assert policy["decision_future_data_allowed"] is False
        assert policy["outcome_evaluation_requires_subsequent_closed_bars"] is True
    source = (root / "afip" / "dashboard_ui" / "split_runtime.py").read_text(encoding="utf-8")
    assert 'AFIP_LIVE_STATUS_POLL_V1' in source
    assert 'afip_live_status.html?ts=' in source
    assert 'render_live_status_html' in source
