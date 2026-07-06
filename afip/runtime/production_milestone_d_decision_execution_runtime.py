"""Production Milestone D Pack 3 deterministic decision execution runtime builder."""

from __future__ import annotations

from afip.decision_execution_flow import DecisionExecutionFlowRuntime


def _sample_requests() -> list[dict[str, object]]:
    return [
        {
            "stage_key": "runtime_wiring",
            "market_regime": "trending",
            "decision_action": "buy",
            "decision_confidence": 82.0,
            "execution_status": "execution_ready",
            "execution_readiness_score": 80.0,
            "cost_status": "pass",
            "risk_status": "pass",
            "data_pipeline_status": "DATA_PIPELINE_READY",
            "runtime_wiring_status": "RUNTIME_WIRING_READY",
            "requested_position_size": 0.01,
            "maximum_position_size": 0.03,
        },
        {
            "stage_key": "data_pipeline",
            "market_regime": "trending",
            "decision_action": "buy",
            "decision_confidence": 84.0,
            "execution_status": "execution_ready",
            "execution_readiness_score": 83.0,
            "cost_status": "pass",
            "risk_status": "pass",
            "data_pipeline_status": "DATA_PIPELINE_READY",
            "runtime_wiring_status": "RUNTIME_WIRING_READY",
            "requested_position_size": 0.01,
            "maximum_position_size": 0.03,
        },
        {
            "stage_key": "decision_state",
            "market_regime": "trending",
            "decision_action": "buy",
            "decision_confidence": 86.0,
            "execution_status": "execution_ready",
            "execution_readiness_score": 85.0,
            "cost_status": "pass",
            "risk_status": "pass",
            "data_pipeline_status": "DATA_PIPELINE_READY",
            "runtime_wiring_status": "RUNTIME_WIRING_READY",
            "requested_position_size": 0.01,
            "maximum_position_size": 0.03,
        },
        {
            "stage_key": "execution_readiness",
            "market_regime": "trending",
            "decision_action": "buy",
            "decision_confidence": 88.0,
            "execution_status": "execution_ready",
            "execution_readiness_score": 87.0,
            "cost_status": "pass",
            "risk_status": "pass",
            "data_pipeline_status": "DATA_PIPELINE_READY",
            "runtime_wiring_status": "RUNTIME_WIRING_READY",
            "requested_position_size": 0.01,
            "maximum_position_size": 0.03,
        },
    ]


def build_production_milestone_d_decision_execution_state() -> dict[str, object]:
    """Return deterministic Pack D3 decision-to-execution flow state."""

    return DecisionExecutionFlowRuntime().run(_sample_requests()).to_dict()
