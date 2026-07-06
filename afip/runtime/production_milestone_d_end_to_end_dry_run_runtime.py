"""Production Milestone D Pack 5 deterministic end-to-end dry run state."""

from __future__ import annotations

from afip.end_to_end_dry_run import EndToEndDryRunRuntime


def _sample_evidence() -> tuple[dict[str, object], ...]:
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
    return (
        {**base, "capability_key": "runtime_wiring", "trace_id": "D5-001"},
        {**base, "capability_key": "data_pipeline", "trace_id": "D5-002"},
        {**base, "capability_key": "decision_execution", "trace_id": "D5-003"},
        {**base, "capability_key": "safety_audit", "trace_id": "D5-004"},
    )


def build_production_milestone_d_end_to_end_dry_run_state() -> dict[str, object]:
    """Build deterministic Pack 5 state without external side effects."""
    report = EndToEndDryRunRuntime().run(_sample_evidence())
    return {
        "milestone": "Production Milestone D",
        "pack": 5,
        "name": "End-to-End Dry Run",
        "status": report.status,
        "action": report.action,
        "reason": report.reason,
        "active_market_regime": report.active_market_regime,
        "capability_count": report.capability_count,
        "evidence_count": report.evidence_count,
        "dry_run_score": report.dry_run_score,
        "is_ready": report.is_ready,
        "trace_ids": report.trace_ids,
    }
