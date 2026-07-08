from afip.runtime.production_freeze_p1_architecture_audit_runtime import (
    evaluate_production_architecture_audit_record,
    evaluate_production_architecture_audit_records,
    explain_production_architecture_audit_record,
)
from afip.production_architecture_audit import ProductionArchitectureAuditObservation


def _record(**overrides):
    data = {
        "market_regime": "trend",
        "signal_context": "sell_edge",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "module_boundary_score": 86,
        "dependency_alignment_score": 84,
        "runtime_flow_score": 85,
        "configuration_score": 82,
        "naming_score": 100,
        "documentation_trace_score": 80,
        "duplicate_logic_findings": 0,
        "circular_dependency_findings": 0,
        "unresolved_findings": 0,
    }
    data.update(overrides)
    return data


def test_architecture_audit_blocks_records_without_market_regime():
    profile = evaluate_production_architecture_audit_record(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"


def test_architecture_audit_blocks_live_execution_mode():
    profile = evaluate_production_architecture_audit_record(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_architecture_audit"
    assert profile.audit_gate == "BLOCKED"


def test_architecture_audit_preserves_regime_before_signal_context():
    first, second = evaluate_production_architecture_audit_records([
        _record(market_regime="trend", signal_context="buy_edge"),
        _record(market_regime="range", signal_context="sell_edge"),
    ])

    assert first.market_regime == "TREND"
    assert first.signal_context == "BUY_EDGE"
    assert second.market_regime == "RANGE"
    assert second.signal_context == "SELL_EDGE"


def test_architecture_audit_calculates_scores_deterministically():
    first = evaluate_production_architecture_audit_record(_record())
    second = evaluate_production_architecture_audit_record(_record())

    assert first.status == "READY"
    assert first.reason == "production_architecture_audit_ready"
    assert first.architecture_quality == second.architecture_quality
    assert first.audit_score == second.audit_score
    assert first.audit_gate == "PRODUCTION_ARCHITECTURE_AUDIT_READY"


def test_architecture_audit_requires_review_for_circular_dependency_findings():
    profile = evaluate_production_architecture_audit_record(_record(circular_dependency_findings=1))

    assert profile.status == "REVIEW"
    assert profile.reason == "circular_dependency_review_required"
    assert profile.audit_gate == "REVIEW_REQUIRED"


def test_architecture_audit_report_and_observation_normalizes_percent_values():
    observation = ProductionArchitectureAuditObservation.from_mapping(_record(module_boundary_score=75, naming_score=100))
    report = explain_production_architecture_audit_record(_record())
    text = report.as_text()

    assert observation.module_boundary_score == 0.75
    assert observation.naming_score == 1.0
    assert observation.audit_score <= 1.0
    assert "Production Architecture Audit Report" in text
    assert "Execution mode: LOCKED_SIMULATION_ONLY" in text
    assert "Audit gate: PRODUCTION_ARCHITECTURE_AUDIT_READY" in text
    assert "Decision reason: production_architecture_audit_ready" in text
