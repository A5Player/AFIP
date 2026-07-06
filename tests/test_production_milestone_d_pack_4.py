from afip.runtime.production_milestone_d_safety_audit_runtime import build_production_milestone_d_safety_audit_state
from afip.safety_audit import SafetyAuditContract, SafetyAuditEvidence, SafetyAuditPolicy, SafetyAuditRuntime


def _ready_evidence():
    base = {
        "market_regime": "trending",
        "execution_status": "DECISION_EXECUTION_READY",
        "audit_status": "PASS",
        "risk_status": "PASS",
        "cost_status": "PASS",
        "decision_confidence": 86,
        "execution_readiness_score": 84,
        "risk_capacity_score": 82,
        "cost_quality_score": 80,
    }
    return [
        {**base, "check_key": "market_regime", "trace_id": "D4-001"},
        {**base, "check_key": "data_pipeline", "trace_id": "D4-002"},
        {**base, "check_key": "decision_execution", "trace_id": "D4-003"},
        {**base, "check_key": "risk_capacity", "trace_id": "D4-004"},
        {**base, "check_key": "cost_quality", "trace_id": "D4-005"},
        {**base, "check_key": "traceability", "trace_id": "D4-006"},
    ]


def test_safety_audit_evidence_normalizes_market_regime_first_key():
    evidence = SafetyAuditEvidence.from_mapping({
        "check": " market regime ",
        "regime": " trending ",
        "status": " decision execution ready ",
        "audit": " pass ",
        "risk": " pass ",
        "cost": " pass ",
        "trace": "TRACE-1",
        "confidence": 86,
        "readiness_score": 84,
        "risk_score": 82,
        "cost_score": 80,
    })
    assert evidence.check_key == "MARKET_REGIME"
    assert evidence.market_regime == "TRENDING"
    assert evidence.execution_status == "DECISION_EXECUTION_READY"
    assert evidence.is_usable is True


def test_safety_audit_evidence_blocks_missing_traceability():
    evidence = SafetyAuditEvidence.from_mapping({**_ready_evidence()[0], "trace_id": ""})
    assert evidence.has_traceability is False
    assert evidence.is_usable is False


def test_safety_audit_contract_orders_required_checks_deterministically():
    contract = SafetyAuditContract.from_evidence(reversed(_ready_evidence()))
    assert contract.check_keys == (
        "MARKET_REGIME",
        "DATA_PIPELINE",
        "DECISION_EXECUTION",
        "RISK_CAPACITY",
        "COST_QUALITY",
        "TRACEABILITY",
    )


def test_safety_audit_contract_reports_missing_required_check():
    contract = SafetyAuditContract.from_evidence(_ready_evidence()[:5])
    assert contract.missing_checks == ("TRACEABILITY",)
    assert contract.is_ready is False


def test_safety_audit_contract_requires_market_regime_before_audit_flow():
    evidence = _ready_evidence()
    evidence[2] = {**evidence[2], "market_regime": "ranging"}
    contract = SafetyAuditContract.from_evidence(evidence)
    assert contract.active_market_regime == "UNKNOWN"
    assert contract.sequence_is_valid is False


def test_safety_audit_contract_uses_data_derived_audit_score():
    contract = SafetyAuditContract.from_evidence(_ready_evidence())
    assert contract.average_decision_confidence == 86.0
    assert contract.average_execution_readiness == 84.0
    assert contract.average_risk_capacity == 82.0
    assert contract.average_cost_quality == 80.0
    assert contract.audit_score == 84.9


def test_safety_audit_policy_waits_for_missing_check():
    decision = SafetyAuditPolicy().decide(SafetyAuditContract.from_evidence(_ready_evidence()[:3]))
    assert decision.status == "SAFETY_AUDIT_WAIT"
    assert decision.action == "WAIT"


def test_safety_audit_policy_blocks_failed_evidence():
    evidence = _ready_evidence()
    evidence[4] = {**evidence[4], "cost_status": "blocked"}
    decision = SafetyAuditPolicy().decide(SafetyAuditContract.from_evidence(evidence))
    assert decision.status == "SAFETY_AUDIT_BLOCKED"
    assert decision.reason == "audit_evidence_not_usable"


def test_safety_audit_policy_confirms_ready_production_path():
    decision = SafetyAuditPolicy().decide(SafetyAuditContract.from_evidence(_ready_evidence()))
    assert decision.status == "SAFETY_AUDIT_READY"
    assert decision.action == "ALLOW_PRODUCTION_PATH"


def test_safety_audit_runtime_builds_audit_report():
    report = SafetyAuditRuntime().run(_ready_evidence())
    assert report.status == "SAFETY_AUDIT_READY"
    assert report.check_count == 6
    assert report.evidence_count == 6
    assert report.active_market_regime == "TRENDING"


def test_production_milestone_d_safety_audit_runtime_is_deterministic():
    first = build_production_milestone_d_safety_audit_state()
    second = build_production_milestone_d_safety_audit_state()
    assert first == second
    assert first["status"] == "SAFETY_AUDIT_READY"
