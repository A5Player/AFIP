from afip.runtime.production_milestone_d_runtime_wiring_runtime import build_runtime
from afip.runtime_wiring import RuntimeComponentState, RuntimeFlowContract, RuntimeWiringPolicy


def ready_states():
    return {
        "MARKET_REGIME": {
            "status": "MARKET_REGIME_INTELLIGENCE_READY",
            "readiness_score": 82.0,
            "evidence_count": 12,
            "reason": "regime_threshold_ready",
        },
        "DECISION_INTELLIGENCE": {
            "status": "DECISION_INTELLIGENCE_READY",
            "confidence": 78.0,
            "evidence_count": 9,
            "reason": "decision_candidate_ready",
        },
        "EXECUTION_READINESS": {
            "status": "EXECUTION_READY",
            "readiness_score": 88.0,
            "evidence_count": 7,
            "reason": "execution_checks_passed",
        },
        "PRODUCTION_INTEGRATION": {
            "status": "PRODUCTION_INTEGRATION_READY",
            "readiness_score": 91.0,
            "evidence_count": 5,
            "reason": "production_contract_ready",
        },
        "MILESTONE_COMPLETION": {
            "status": "MILESTONE_C_COMPLETE",
            "completion_score": 100.0,
            "capability_count": 8,
            "reason": "milestone_c_complete",
        },
    }


def test_runtime_component_state_normalizes_financial_key():
    state = RuntimeComponentState(" market_regime ", " market_regime_intelligence_ready ", 101.5, 1, 3, "ok")
    assert state.component_key == "MARKET_REGIME"
    assert state.status == "MARKET_REGIME_INTELLIGENCE_READY"
    assert state.readiness_score == 100.0
    assert state.is_ready is True


def test_runtime_component_state_blocks_without_evidence():
    state = RuntimeComponentState("DECISION_INTELLIGENCE", "DECISION_INTELLIGENCE_READY", 80.0, 2, 0, "missing")
    assert state.is_ready is False


def test_runtime_flow_contract_orders_required_components_deterministically():
    states = ready_states()
    unordered = {
        "EXECUTION_READINESS": states["EXECUTION_READINESS"],
        "MARKET_REGIME": states["MARKET_REGIME"],
        "MILESTONE_COMPLETION": states["MILESTONE_COMPLETION"],
        "DECISION_INTELLIGENCE": states["DECISION_INTELLIGENCE"],
        "PRODUCTION_INTEGRATION": states["PRODUCTION_INTEGRATION"],
    }
    contract = RuntimeFlowContract.from_runtime_states(unordered)
    assert contract.component_keys == (
        "MARKET_REGIME",
        "DECISION_INTELLIGENCE",
        "EXECUTION_READINESS",
        "PRODUCTION_INTEGRATION",
        "MILESTONE_COMPLETION",
    )


def test_runtime_flow_contract_reports_missing_component():
    states = ready_states()
    states.pop("EXECUTION_READINESS")
    contract = RuntimeFlowContract.from_runtime_states(states)
    assert contract.missing_components == ("EXECUTION_READINESS",)
    assert contract.is_wirable is False


def test_runtime_flow_contract_reports_failed_component():
    states = ready_states()
    states["PRODUCTION_INTEGRATION"] = {**states["PRODUCTION_INTEGRATION"], "readiness_score": 40.0}
    contract = RuntimeFlowContract.from_runtime_states(states)
    assert contract.failed_components == ("PRODUCTION_INTEGRATION",)


def test_runtime_flow_contract_uses_data_derived_aggregate_readiness():
    contract = RuntimeFlowContract.from_runtime_states(ready_states())
    assert contract.aggregate_readiness == 87.8


def test_runtime_wiring_policy_waits_for_missing_component():
    states = ready_states()
    states.pop("DECISION_INTELLIGENCE")
    decision = RuntimeWiringPolicy().decide(RuntimeFlowContract.from_runtime_states(states))
    assert decision.status == "RUNTIME_WIRING_WAIT"
    assert decision.action == "WAIT"


def test_runtime_wiring_policy_blocks_failed_readiness():
    states = ready_states()
    states["EXECUTION_READINESS"] = {**states["EXECUTION_READINESS"], "status": "EXECUTION_WAIT"}
    decision = RuntimeWiringPolicy().decide(RuntimeFlowContract.from_runtime_states(states))
    assert decision.status == "RUNTIME_WIRING_BLOCKED"
    assert decision.reason == "runtime_component_not_ready"


def test_runtime_wiring_policy_confirms_ready_runtime_path():
    decision = RuntimeWiringPolicy().decide(RuntimeFlowContract.from_runtime_states(ready_states()))
    assert decision.status == "RUNTIME_WIRING_READY"
    assert decision.action == "WIRE_RUNTIME"


def test_runtime_wiring_runtime_builds_audit_report():
    report = build_runtime().run(ready_states()).as_dict()
    assert report["status"] == "RUNTIME_WIRING_READY"
    assert report["component_count"] == 5
    assert report["sequence_is_valid"] is True
    assert report["missing_components"] == []


def test_production_milestone_d_runtime_wiring_runtime_is_deterministic():
    runtime = build_runtime()
    first = runtime.run(ready_states()).as_dict()
    second = runtime.run(ready_states()).as_dict()
    assert first == second
