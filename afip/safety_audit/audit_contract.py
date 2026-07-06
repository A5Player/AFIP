"""Production Milestone D Pack 4 safety and audit contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Tuple

from .audit_evidence import SafetyAuditEvidence

REQUIRED_AUDIT_SEQUENCE: Tuple[str, ...] = (
    "MARKET_REGIME",
    "DATA_PIPELINE",
    "DECISION_EXECUTION",
    "RISK_CAPACITY",
    "COST_QUALITY",
    "TRACEABILITY",
)


@dataclass(frozen=True)
class SafetyAuditContract:
    """Data-first contract proving the runtime path is safe and auditable."""

    evidence: Tuple[SafetyAuditEvidence, ...]
    check_keys: Tuple[str, ...]
    missing_checks: Tuple[str, ...]
    active_market_regime: str
    average_decision_confidence: float
    average_execution_readiness: float
    average_risk_capacity: float
    average_cost_quality: float
    audit_score: float
    trace_ids: Tuple[str, ...]
    sequence_is_valid: bool
    all_evidence_usable: bool

    @classmethod
    def from_evidence(cls, values: Iterable[Mapping[str, Any] | SafetyAuditEvidence]) -> "SafetyAuditContract":
        evidence = tuple(
            value if isinstance(value, SafetyAuditEvidence) else SafetyAuditEvidence.from_mapping(value)
            for value in values
        )
        by_check = {item.check_key: item for item in evidence}
        ordered_keys = tuple(key for key in REQUIRED_AUDIT_SEQUENCE if key in by_check)
        missing = tuple(key for key in REQUIRED_AUDIT_SEQUENCE if key not in by_check)
        ordered_evidence = tuple(by_check[key] for key in ordered_keys)

        regimes = tuple(item.market_regime for item in ordered_evidence if item.has_market_regime)
        active_regime = regimes[0] if regimes and all(regime == regimes[0] for regime in regimes) else "UNKNOWN"

        decision_values = tuple(item.decision_confidence for item in ordered_evidence)
        readiness_values = tuple(item.execution_readiness_score for item in ordered_evidence)
        risk_values = tuple(item.risk_capacity_score for item in ordered_evidence)
        cost_values = tuple(item.cost_quality_score for item in ordered_evidence)

        average_decision = round(sum(decision_values) / len(decision_values), 4) if decision_values else 0.0
        average_readiness = round(sum(readiness_values) / len(readiness_values), 4) if readiness_values else 0.0
        average_risk = round(sum(risk_values) / len(risk_values), 4) if risk_values else 0.0
        average_cost = round(sum(cost_values) / len(cost_values), 4) if cost_values else 0.0
        all_usable = bool(ordered_evidence) and all(item.is_usable for item in ordered_evidence)
        trace_ids = tuple(item.trace_id for item in ordered_evidence if item.trace_id)
        sequence_valid = ordered_keys == REQUIRED_AUDIT_SEQUENCE and active_regime != "UNKNOWN"
        trace_score = 10.0 if len(trace_ids) == len(REQUIRED_AUDIT_SEQUENCE) else 0.0
        audit_score = round(
            (average_decision * 0.25)
            + (average_readiness * 0.25)
            + (average_risk * 0.2)
            + (average_cost * 0.2)
            + trace_score,
            4,
        )

        return cls(
            evidence=ordered_evidence,
            check_keys=ordered_keys,
            missing_checks=missing,
            active_market_regime=active_regime,
            average_decision_confidence=average_decision,
            average_execution_readiness=average_readiness,
            average_risk_capacity=average_risk,
            average_cost_quality=average_cost,
            audit_score=audit_score,
            trace_ids=trace_ids,
            sequence_is_valid=sequence_valid,
            all_evidence_usable=all_usable,
        )

    @property
    def is_ready(self) -> bool:
        return (
            not self.missing_checks
            and self.sequence_is_valid
            and self.all_evidence_usable
            and len(self.trace_ids) == len(REQUIRED_AUDIT_SEQUENCE)
            and self.audit_score >= 70.0
        )
