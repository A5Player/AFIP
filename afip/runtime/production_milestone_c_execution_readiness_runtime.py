"""Production entrypoint for Milestone C Pack 18 execution readiness."""

from __future__ import annotations

from afip.execution_readiness import ExecutionReadinessInput, ExecutionReadinessRuntime


def sample_execution_readiness_input() -> ExecutionReadinessInput:
    return ExecutionReadinessInput(
        action="BUY",
        decision_confidence=82.0,
        decision_score=68.5,
        regime_first_key="EXPANSION|HIGH|BUY",
        spread_points=24.0,
        maximum_spread_points=35.0,
        liquidity_score=76.0,
        risk_score=81.0,
        available_margin_ratio=2.4,
        open_position_count=1,
        maximum_position_count=4,
    )


def run_dict() -> dict[str, object]:
    return ExecutionReadinessRuntime().run(sample_execution_readiness_input()).as_dict()
