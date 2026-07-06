"""Production Milestone D Pack 4 safety and audit policy."""

from __future__ import annotations

from dataclasses import dataclass

from .audit_contract import SafetyAuditContract


@dataclass(frozen=True)
class SafetyAuditDecision:
    """Policy decision for the final safety and audit layer."""

    status: str
    action: str
    reason: str
    audit_score: float


class SafetyAuditPolicy:
    """Deterministic safety policy after data, decision, and execution flow are ready."""

    def decide(self, contract: SafetyAuditContract) -> SafetyAuditDecision:
        if contract.missing_checks:
            return SafetyAuditDecision("SAFETY_AUDIT_WAIT", "WAIT", "missing_required_audit_check", contract.audit_score)
        if not contract.sequence_is_valid:
            return SafetyAuditDecision("SAFETY_AUDIT_BLOCKED", "WAIT", "market_regime_sequence_invalid", contract.audit_score)
        if not contract.all_evidence_usable:
            return SafetyAuditDecision("SAFETY_AUDIT_BLOCKED", "WAIT", "audit_evidence_not_usable", contract.audit_score)
        if len(contract.trace_ids) != len(contract.check_keys):
            return SafetyAuditDecision("SAFETY_AUDIT_BLOCKED", "WAIT", "traceability_incomplete", contract.audit_score)
        if contract.audit_score < 70.0:
            return SafetyAuditDecision("SAFETY_AUDIT_BLOCKED", "WAIT", "audit_score_below_required_level", contract.audit_score)
        return SafetyAuditDecision("SAFETY_AUDIT_READY", "ALLOW_PRODUCTION_PATH", "safety_audit_ready", contract.audit_score)
