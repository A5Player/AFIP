from afip.decision_execution_flow import (
    DecisionExecutionFlowContract,
    DecisionExecutionFlowPolicy,
    DecisionExecutionFlowRuntime,
    ExecutionRequest,
)
from afip.runtime.production_milestone_d_decision_execution_runtime import build_production_milestone_d_decision_execution_state


def _ready_requests():
    base = {
        "market_regime": "trending",
        "decision_action": "buy",
        "execution_status": "execution_ready",
        "cost_status": "pass",
        "risk_status": "pass",
        "data_pipeline_status": "DATA_PIPELINE_READY",
        "runtime_wiring_status": "RUNTIME_WIRING_READY",
        "requested_position_size": 0.01,
        "maximum_position_size": 0.03,
    }
    return [
        {**base, "stage_key": "runtime_wiring", "decision_confidence": 82, "execution_readiness_score": 80},
        {**base, "stage_key": "data_pipeline", "decision_confidence": 84, "execution_readiness_score": 83},
        {**base, "stage_key": "decision_state", "decision_confidence": 86, "execution_readiness_score": 85},
        {**base, "stage_key": "execution_readiness", "decision_confidence": 88, "execution_readiness_score": 87},
    ]


def test_execution_request_normalizes_market_regime_first_key():
    request = ExecutionRequest.from_mapping({
        "stage": " decision_state ",
        "regime": " trending ",
        "action": " buy ",
        "confidence": 86,
        "readiness_status": " execution_ready ",
        "readiness_score": 85,
        "cost_status": " pass ",
        "risk_status": " pass ",
        "data_pipeline_status": "DATA_PIPELINE_READY",
        "runtime_wiring_status": "RUNTIME_WIRING_READY",
        "position_size": 0.01,
        "max_position_size": 0.03,
    })
    assert request.stage_key == "DECISION_STATE"
    assert request.market_regime == "TRENDING"
    assert request.decision_action == "BUY"
    assert request.is_usable is True


def test_execution_request_blocks_invalid_position_capacity():
    request = ExecutionRequest.from_mapping({**_ready_requests()[0], "requested_position_size": 0.05})
    assert request.position_size_is_valid is False
    assert request.is_usable is False


def test_decision_execution_contract_orders_required_stages_deterministically():
    contract = DecisionExecutionFlowContract.from_requests(reversed(_ready_requests()))
    assert contract.stage_keys == ("RUNTIME_WIRING", "DATA_PIPELINE", "DECISION_STATE", "EXECUTION_READINESS")


def test_decision_execution_contract_reports_missing_required_stage():
    contract = DecisionExecutionFlowContract.from_requests(_ready_requests()[:3])
    assert contract.missing_stages == ("EXECUTION_READINESS",)
    assert contract.is_ready is False


def test_decision_execution_contract_requires_market_regime_before_execution_flow():
    requests = _ready_requests()
    requests[1] = {**requests[1], "market_regime": "ranging"}
    contract = DecisionExecutionFlowContract.from_requests(requests)
    assert contract.active_market_regime == "UNKNOWN"
    assert contract.sequence_is_valid is False


def test_decision_execution_contract_uses_data_derived_flow_score():
    contract = DecisionExecutionFlowContract.from_requests(_ready_requests())
    assert contract.average_decision_confidence == 85.0
    assert contract.average_execution_readiness == 83.75
    assert contract.flow_score == 85.9375


def test_decision_execution_policy_waits_for_missing_stage():
    decision = DecisionExecutionFlowPolicy().decide(DecisionExecutionFlowContract.from_requests(_ready_requests()[:2]))
    assert decision.status == "DECISION_EXECUTION_WAIT"
    assert decision.action == "WAIT"


def test_decision_execution_policy_blocks_failed_request():
    requests = _ready_requests()
    requests[0] = {**requests[0], "cost_status": "blocked"}
    decision = DecisionExecutionFlowPolicy().decide(DecisionExecutionFlowContract.from_requests(requests))
    assert decision.status == "DECISION_EXECUTION_BLOCKED"
    assert decision.reason == "execution_request_not_usable"


def test_decision_execution_policy_confirms_ready_flow():
    decision = DecisionExecutionFlowPolicy().decide(DecisionExecutionFlowContract.from_requests(_ready_requests()))
    assert decision.status == "DECISION_EXECUTION_READY"
    assert decision.action == "PREPARE_EXECUTION"


def test_decision_execution_runtime_builds_audit_report():
    report = DecisionExecutionFlowRuntime().run(_ready_requests())
    assert report.status == "DECISION_EXECUTION_READY"
    assert report.stage_count == 4
    assert report.request_count == 4
    assert report.selected_action == "BUY"


def test_production_milestone_d_decision_execution_runtime_is_deterministic():
    first = build_production_milestone_d_decision_execution_state()
    second = build_production_milestone_d_decision_execution_state()
    assert first == second
    assert first["status"] == "DECISION_EXECUTION_READY"
