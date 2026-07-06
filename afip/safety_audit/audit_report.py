"""Production Milestone D Pack 4 safety and audit report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .audit_contract import SafetyAuditContract
from .audit_policy import SafetyAuditDecision


@dataclass(frozen=True)
class SafetyAuditReport:
    """Immutable audit report for deterministic runtime verification."""

    status: str
    action: str
    reason: str
    check_count: int
    evidence_count: int
    active_market_regime: str
    average_decision_confidence: float
    average_execution_readiness: float
    average_risk_capacity: float
    average_cost_quality: float
    audit_score: float
    missing_checks: Tuple[str, ...]
    trace_ids: Tuple[str, ...]

    @classmethod
    def from_contract(cls, contract: SafetyAuditContract, decision: SafetyAuditDecision) -> "SafetyAuditReport":
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            check_count=len(contract.check_keys),
            evidence_count=len(contract.evidence),
            active_market_regime=contract.active_market_regime,
            average_decision_confidence=contract.average_decision_confidence,
            average_execution_readiness=contract.average_execution_readiness,
            average_risk_capacity=contract.average_risk_capacity,
            average_cost_quality=contract.average_cost_quality,
            audit_score=contract.audit_score,
            missing_checks=contract.missing_checks,
            trace_ids=contract.trace_ids,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "check_count": self.check_count,
            "evidence_count": self.evidence_count,
            "active_market_regime": self.active_market_regime,
            "average_decision_confidence": self.average_decision_confidence,
            "average_execution_readiness": self.average_execution_readiness,
            "average_risk_capacity": self.average_risk_capacity,
            "average_cost_quality": self.average_cost_quality,
            "audit_score": self.audit_score,
            "missing_checks": self.missing_checks,
            "trace_ids": self.trace_ids,
        }
