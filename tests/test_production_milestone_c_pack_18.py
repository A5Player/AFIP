from __future__ import annotations

from afip.execution_readiness import (
    CostReadinessCheck,
    ExecutionReadinessInput,
    ExecutionReadinessPolicy,
    ExecutionReadinessRuntime,
    LiquidityReadinessCheck,
    RiskReadinessCheck,
)
from afip.runtime.production_milestone_c_execution_readiness_runtime import run_dict, sample_execution_readiness_input


def _input(**updates: object) -> ExecutionReadinessInput:
    data: dict[str, object] = {
        "action": "buy",
        "decision_confidence": 82.0,
        "decision_score": 68.5,
        "regime_first_key": "expansion|high|buy",
        "spread_points": 24.0,
        "maximum_spread_points": 35.0,
        "liquidity_score": 76.0,
        "risk_score": 81.0,
        "available_margin_ratio": 2.4,
        "open_position_count": 1,
        "maximum_position_count": 4,
    }
    data.update(updates)
    return ExecutionReadinessInput.from_mapping(data)


def test_execution_readiness_input_normalizes_decision_to_execution_contract() -> None:
    value = _input(action="long", regime_first_key="expansion|high|buy")
    assert value.action == "WAIT"
    assert value.regime_first_key == "EXPANSION|HIGH|BUY"
    assert value.decision_confidence == 82.0


def test_execution_readiness_input_reads_decision_mapping() -> None:
    value = ExecutionReadinessInput.from_mapping({
        "decision": {"action": "SELL", "confidence": 74.0, "score": 63.0, "regime_first_key": "normal|medium|sell"},
        "spread_points": 20.0,
        "maximum_spread_points": 32.0,
        "liquidity_score": 70.0,
        "risk_score": 75.0,
        "available_margin_ratio": 2.0,
        "open_position_count": 0,
        "maximum_position_count": 2,
    })
    assert value.action == "SELL"
    assert value.regime_first_key == "NORMAL|MEDIUM|SELL"


def test_cost_readiness_uses_learned_spread_limit() -> None:
    result = CostReadinessCheck().evaluate(_input(spread_points=20.0, maximum_spread_points=40.0))
    assert result.status == "PASS"
    assert result.score == 50.0
    assert "spread_within_learned_limit" in result.reasons


def test_cost_readiness_blocks_above_learned_limit() -> None:
    result = CostReadinessCheck().evaluate(_input(spread_points=44.0, maximum_spread_points=35.0))
    assert result.status == "BLOCK"
    assert "spread_above_learned_limit" in result.reasons


def test_liquidity_readiness_blocks_low_liquidity() -> None:
    result = LiquidityReadinessCheck().evaluate(_input(liquidity_score=42.0))
    assert result.status == "BLOCK"
    assert "liquidity_below_readiness_floor" in result.reasons


def test_risk_readiness_requires_margin_capacity() -> None:
    result = RiskReadinessCheck().evaluate(_input(available_margin_ratio=1.1))
    assert result.status == "BLOCK"
    assert "available_margin_ratio_below_floor" in result.reasons


def test_execution_policy_waits_without_decision_action() -> None:
    runtime = ExecutionReadinessRuntime()
    state = runtime.run(_input(action="WAIT"))
    assert state.status == "EXECUTION_WAIT"
    assert state.decision["action"] == "WAIT"


def test_execution_policy_blocks_failed_checks() -> None:
    state = ExecutionReadinessRuntime().run(_input(spread_points=48.0))
    assert state.status == "EXECUTION_BLOCKED"
    assert state.decision["action"] == "WAIT"
    assert "spread_above_learned_limit" in state.decision["reasons"]


def test_execution_policy_confirms_ready_action() -> None:
    state = ExecutionReadinessRuntime().run(sample_execution_readiness_input())
    assert state.status == "EXECUTION_READY"
    assert state.decision["action"] == "BUY"
    assert state.decision["readiness_score"] > 50.0


def test_execution_readiness_runtime_returns_check_summary() -> None:
    state = ExecutionReadinessRuntime().run(_input())
    assert len(state.checks) == 4
    assert state.input["regime_first_key"] == "EXPANSION|HIGH|BUY"
    assert state.reason == "execution_readiness_confirmed_from_data"


def test_production_milestone_c_execution_readiness_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "EXECUTION_READY"
