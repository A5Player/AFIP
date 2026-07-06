from afip.end_to_end_dry_run import (
    EndToEndDryRunContract,
    EndToEndDryRunEvidence,
    EndToEndDryRunPolicy,
    EndToEndDryRunRuntime,
)
from afip.runtime.production_milestone_d_end_to_end_dry_run_runtime import (
    build_production_milestone_d_end_to_end_dry_run_state,
)


def _ready_evidence():
    base = {
        "market_regime": "trending",
        "runtime_status": "READY",
        "data_status": "READY",
        "decision_status": "DECISION_READY",
        "execution_status": "DECISION_EXECUTION_READY",
        "audit_status": "SAFETY_AUDIT_READY",
        "readiness_score": 86,
        "data_quality_score": 84,
        "decision_confidence": 88,
        "execution_score": 85,
        "audit_score": 87,
    }
    return [
        {**base, "capability_key": "runtime_wiring", "trace_id": "D5-001"},
        {**base, "capability_key": "data_pipeline", "trace_id": "D5-002"},
        {**base, "capability_key": "decision_execution", "trace_id": "D5-003"},
        {**base, "capability_key": "safety_audit", "trace_id": "D5-004"},
    ]


def test_dry_run_evidence_normalizes_financial_capability_key():
    evidence = EndToEndDryRunEvidence.from_mapping({
        "capability": " runtime wiring ",
        "regime": " trending ",
        "runtime": " ready ",
        "data": " ready ",
        "decision": " decision ready ",
        "execution": " decision execution ready ",
        "audit": " safety audit ready ",
        "trace": "TRACE-1",
        "runtime_score": 86,
        "data_score": 84,
        "confidence": 88,
        "execution_readiness_score": 85,
        "safety_score": 87,
    })
    assert evidence.capability_key == "RUNTIME_WIRING"
    assert evidence.market_regime == "TRENDING"
    assert evidence.execution_status == "DECISION_EXECUTION_READY"
    assert evidence.is_usable is True


def test_dry_run_evidence_blocks_missing_traceability():
    evidence = EndToEndDryRunEvidence.from_mapping({**_ready_evidence()[0], "trace_id": ""})
    assert evidence.has_traceability is False
    assert evidence.is_usable is False


def test_dry_run_contract_orders_capabilities_deterministically():
    contract = EndToEndDryRunContract.from_evidence(reversed(_ready_evidence()))
    assert contract.capability_keys == (
        "RUNTIME_WIRING",
        "DATA_PIPELINE",
        "DECISION_EXECUTION",
        "SAFETY_AUDIT",
    )


def test_dry_run_contract_reports_missing_required_capability():
    contract = EndToEndDryRunContract.from_evidence(_ready_evidence()[:3])
    assert contract.missing_capabilities == ("SAFETY_AUDIT",)
    assert contract.is_ready is False


def test_dry_run_contract_requires_market_regime_before_runtime_path():
    evidence = _ready_evidence()
    evidence[1] = {**evidence[1], "market_regime": "ranging"}
    contract = EndToEndDryRunContract.from_evidence(evidence)
    assert contract.active_market_regime == "UNKNOWN"
    assert contract.sequence_is_valid is False


def test_dry_run_contract_uses_data_derived_score():
    contract = EndToEndDryRunContract.from_evidence(_ready_evidence())
    assert contract.average_runtime_readiness == 86.0
    assert contract.average_data_quality == 84.0
    assert contract.average_decision_confidence == 88.0
    assert contract.average_execution_score == 85.0
    assert contract.average_audit_score == 87.0
    assert contract.dry_run_score == 86.69


def test_dry_run_policy_waits_for_missing_capability():
    decision = EndToEndDryRunPolicy().decide(EndToEndDryRunContract.from_evidence(_ready_evidence()[:2]))
    assert decision.status == "END_TO_END_DRY_RUN_WAIT"
    assert decision.action == "WAIT"


def test_dry_run_policy_blocks_failed_evidence():
    evidence = _ready_evidence()
    evidence[2] = {**evidence[2], "decision_status": "blocked"}
    decision = EndToEndDryRunPolicy().decide(EndToEndDryRunContract.from_evidence(evidence))
    assert decision.status == "END_TO_END_DRY_RUN_BLOCKED"
    assert decision.reason == "dry_run_evidence_not_usable"


def test_dry_run_policy_confirms_ready_integrated_path():
    decision = EndToEndDryRunPolicy().decide(EndToEndDryRunContract.from_evidence(_ready_evidence()))
    assert decision.status == "END_TO_END_DRY_RUN_READY"
    assert decision.action == "CONFIRM_DRY_RUN"


def test_dry_run_runtime_builds_final_report():
    report = EndToEndDryRunRuntime().run(_ready_evidence())
    assert report.status == "END_TO_END_DRY_RUN_READY"
    assert report.capability_count == 4
    assert report.evidence_count == 4
    assert report.active_market_regime == "TRENDING"
    assert report.is_ready is True


def test_production_milestone_d_end_to_end_dry_run_runtime_is_deterministic():
    first = build_production_milestone_d_end_to_end_dry_run_state()
    second = build_production_milestone_d_end_to_end_dry_run_state()
    assert first == second
    assert first["status"] == "END_TO_END_DRY_RUN_READY"
    assert first["is_ready"] is True
