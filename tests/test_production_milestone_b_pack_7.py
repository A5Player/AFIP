from __future__ import annotations

from afip.execution.execution_plan_allocator import ExecutionPlanAllocator
from afip.execution.execution_readiness_assessment import ExecutionReadinessAssessment
from afip.execution.execution_strategy_selection import ExecutionStrategySelection
from afip.execution.execution_timing_model import ExecutionTimingModel
from afip.execution.order_size_allocator import OrderSizeAllocator
from afip.runtime.production_milestone_b_execution_runtime import ProductionMilestoneBExecutionRuntime


def test_execution_plan_allocator_creates_buy_plan() -> None:
    result = ExecutionPlanAllocator().create(
        decision_profile={"action": "BUY", "confidence": 0.90},
        context_profile={"market_state": "TRENDING", "volatility_state": "NORMAL", "liquidity_state": "EXPANDING", "spread_points": 20.0},
        risk_profile={"risk_status": "ACCEPTED", "risk_budget": 0.01},
        account_profile={"equity": 100.0, "maximum_lot": 0.05},
    )
    assert result.status == "EXECUTION_PLAN_READY"
    assert result.action == "BUY"
    assert result.lot_size >= 0.01


def test_execution_plan_allocator_creates_selective_sell_plan() -> None:
    result = ExecutionPlanAllocator().create(
        decision_profile={"action": "SELL", "confidence": 0.78},
        context_profile={"market_state": "SIDEWAYS", "volatility_state": "NORMAL", "liquidity_state": "NORMAL", "spread_points": 28.0},
        risk_profile={"risk_status": "ACCEPTED", "risk_budget": 0.01},
    )
    assert result.action == "SELL"
    assert result.strategy == "LIQUIDITY_CONFIRMATION"
    assert result.status in {"EXECUTION_PLAN_READY", "EXECUTION_PLAN_SELECTIVE"}


def test_execution_plan_allocator_returns_review_for_wait() -> None:
    result = ExecutionPlanAllocator().create(decision_profile={"action": "WAIT", "confidence": 0.92})
    assert result.status == "EXECUTION_PLAN_REVIEW"
    assert result.lot_size == 0.0


def test_execution_timing_model_delays_high_spread() -> None:
    result = ExecutionTimingModel().evaluate(spread_points=42.0, spread_limit=35.0, decision_confidence=0.90)
    assert result.status == "EXECUTION_TIMING_REVIEW"
    assert result.timing == "DELAY"


def test_order_size_allocator_respects_maximum_lot() -> None:
    result = OrderSizeAllocator().allocate(equity=5000.0, risk_budget=0.02, confidence=0.95, maximum_lot=0.05)
    assert result.status == "ORDER_SIZE_READY"
    assert result.lot_size == 0.05
    assert result.exposure_ratio <= 1.0


def test_execution_readiness_rejects_unaccepted_risk() -> None:
    result = ExecutionReadinessAssessment().assess("BUY", 0.90, "NOT_ACCEPTED", "IMMEDIATE", "BREAKOUT_CONTINUATION")
    assert result.readiness == "NOT_READY"
    assert result.status == "EXECUTION_READINESS_REVIEW"


def test_execution_strategy_selection_uses_limited_risk_for_high_volatility() -> None:
    result = ExecutionStrategySelection().select("BUY", "TRENDING", "HIGH", "EXPANDING")
    assert result.strategy == "LIMITED_RISK_ENTRY"
    assert result.participation == "REDUCED"


def test_execution_runtime_uses_default_profiles() -> None:
    result = ProductionMilestoneBExecutionRuntime().run()
    assert result.status == "MILESTONE_B_EXECUTION_RUNTIME_READY"
    assert result.action == "BUY"
    assert result.lot_size >= 0.01
