"""Production Milestone D Pack 5 end-to-end dry run evidence model."""

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
class EndToEndDryRunEvidence:
    """Single data-first capability result for a production dry run."""

    capability_key: str
    market_regime: str
    runtime_status: str
    data_status: str
    decision_status: str
    execution_status: str
    audit_status: str
    trace_id: str
    readiness_score: float
    data_quality_score: float
    decision_confidence: float
    execution_score: float
    audit_score: float

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EndToEndDryRunEvidence":
        return cls(
            capability_key=_norm(value.get("capability_key") or value.get("capability") or value.get("stage_key")),
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            runtime_status=_norm(value.get("runtime_status") or value.get("runtime")),
            data_status=_norm(value.get("data_status") or value.get("data")),
            decision_status=_norm(value.get("decision_status") or value.get("decision")),
            execution_status=_norm(value.get("execution_status") or value.get("execution")),
            audit_status=_norm(value.get("audit_status") or value.get("audit")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
            readiness_score=_float(value.get("readiness_score") or value.get("runtime_score")),
            data_quality_score=_float(value.get("data_quality_score") or value.get("data_score")),
            decision_confidence=_float(value.get("decision_confidence") or value.get("confidence")),
            execution_score=_float(value.get("execution_score") or value.get("execution_readiness_score")),
            audit_score=_float(value.get("audit_score") or value.get("safety_score")),
        )

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def has_traceability(self) -> bool:
        return bool(self.trace_id)

    @property
    def is_usable(self) -> bool:
        ready_statuses = {"READY", "PASS", "COMPLETE", "DRY_RUN_READY"}
        return (
            self.has_market_regime
            and self.runtime_status in ready_statuses
            and self.data_status in ready_statuses
            and self.decision_status in {"READY", "PASS", "DECISION_READY", "DRY_RUN_READY"}
            and self.execution_status in {"READY", "PASS", "EXECUTION_READY", "DECISION_EXECUTION_READY"}
            and self.audit_status in {"READY", "PASS", "SAFETY_AUDIT_READY", "AUDIT_PASS"}
            and self.has_traceability
            and self.readiness_score > 0
            and self.data_quality_score > 0
            and self.decision_confidence > 0
            and self.execution_score > 0
            and self.audit_score > 0
        )
