"""Production Milestone D Pack 4 safety and audit evidence model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _norm(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value or "").strip().upper().replace(" ", "_").replace("-", "_")
    return text or default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class SafetyAuditEvidence:
    """Single deterministic evidence item for financial execution safety."""

    check_key: str
    market_regime: str
    execution_status: str
    audit_status: str
    risk_status: str
    cost_status: str
    trace_id: str
    decision_confidence: float
    execution_readiness_score: float
    risk_capacity_score: float
    cost_quality_score: float

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SafetyAuditEvidence":
        return cls(
            check_key=_norm(value.get("check_key") or value.get("check") or value.get("stage_key")),
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            execution_status=_norm(value.get("execution_status") or value.get("status")),
            audit_status=_norm(value.get("audit_status") or value.get("audit")),
            risk_status=_norm(value.get("risk_status") or value.get("risk")),
            cost_status=_norm(value.get("cost_status") or value.get("cost")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
            decision_confidence=_float(value.get("decision_confidence") or value.get("confidence")),
            execution_readiness_score=_float(value.get("execution_readiness_score") or value.get("readiness_score")),
            risk_capacity_score=_float(value.get("risk_capacity_score") or value.get("risk_score")),
            cost_quality_score=_float(value.get("cost_quality_score") or value.get("cost_score")),
        )

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def has_traceability(self) -> bool:
        return bool(self.trace_id)

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.execution_status in {"DECISION_EXECUTION_READY", "EXECUTION_READY", "READY"}
            and self.audit_status in {"PASS", "AUDIT_PASS", "READY"}
            and self.risk_status in {"PASS", "RISK_PASS", "READY"}
            and self.cost_status in {"PASS", "TRADING_COST_PASS", "READY"}
            and self.has_traceability
            and self.decision_confidence > 0
            and self.execution_readiness_score > 0
        )
