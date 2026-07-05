from afip.context.context_transition_model import ContextTransitionModel
from afip.context.liquidity_context import LiquidityContext
from afip.context.market_context_engine import MarketContextEngine
from afip.context.market_state_classifier import MarketStateClassifier
from afip.context.volatility_context import VolatilityContext
from afip.runtime.production_milestone_b_context_runtime import (
    run_production_milestone_b_context_runtime,
)


def test_market_state_classifier_detects_trending_context() -> None:
    result = MarketStateClassifier().classify({"trend_strength": 0.88, "range_balance": 0.30})
    assert result.status == "MARKET_STATE_READY"
    assert result.market_state == "TRENDING"
    assert result.confidence == 88.0


def test_market_state_classifier_detects_sideways_context() -> None:
    result = MarketStateClassifier().classify({"trend_strength": 0.25, "range_balance": 0.82})
    assert result.market_state == "SIDEWAYS"
    assert result.context_score == 82.0


def test_market_state_classifier_detects_breakout_context() -> None:
    result = MarketStateClassifier().classify({"breakout_pressure": 0.91, "trend_strength": 0.62})
    assert result.market_state == "BREAKOUT"
    assert result.reason == "market_state_breakout"


def test_market_state_classifier_detects_pullback_context() -> None:
    result = MarketStateClassifier().classify({"pullback_depth": 0.76, "trend_strength": 0.55})
    assert result.market_state == "PULLBACK"
    assert result.status == "MARKET_STATE_READY"


def test_volatility_context_reduces_execution_quality_in_extreme_volatility() -> None:
    result = VolatilityContext().assess({"volatility": 0.90})
    assert result.status == "VOLATILITY_REVIEW"
    assert result.volatility_state == "EXTREME_VOLATILITY"
    assert result.adjustment_factor == 0.70


def test_liquidity_context_identifies_expansion() -> None:
    result = LiquidityContext().assess(
        {"liquidity_depth": 0.82, "spread_quality": 0.75, "volume_participation": 0.78}
    )
    assert result.status == "LIQUIDITY_READY"
    assert result.liquidity_state == "LIQUIDITY_EXPANSION"
    assert result.execution_quality_factor == 1.05


def test_context_transition_model_marks_active_transition_for_state_change() -> None:
    result = ContextTransitionModel().evaluate("SIDEWAYS", "BREAKOUT")
    assert result.status == "CONTEXT_TRANSITION_REVIEW"
    assert result.transition_state == "ACTIVE_CONTEXT_TRANSITION"
    assert result.stability_score == 54.0


def test_market_context_runtime_returns_serializable_payload() -> None:
    payload = run_production_milestone_b_context_runtime(
        {
            "trend_strength": 0.87,
            "volatility": 0.58,
            "liquidity_depth": 0.80,
            "spread_quality": 0.76,
            "volume_participation": 0.73,
        },
        previous_state="TRENDING",
    )
    assert payload["runtime_status"] == "PRODUCTION_MILESTONE_B_CONTEXT_READY"
    assert payload["milestone"] == "PRODUCTION_MILESTONE_B_PACK_6"
    assert payload["market_state"] == "TRENDING"
    assert payload["status"] == "MARKET_CONTEXT_READY"
    assert payload["context_score"] >= 70.0
