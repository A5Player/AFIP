"""Milestone F completion observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class MilestoneFCompletionObservation:
    """Normalized production readiness evidence for deterministic Milestone F closure."""

    market_regime: str
    signal_context: str
    production_readiness_score: float
    production_runtime_weight: float
    readiness_evidence_quality: float
    data_quality: float
    knowledge_quality: float
    strategy_quality: float
    runtime_stability: float
    validation_quality: float
    monitoring_quality: float
    rollback_readiness: float
    documentation_quality: float
    handoff_quality: float
    completion_risk: float
    completion_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "MilestoneFCompletionObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        production_readiness_score = _ratio(value.get("production_readiness_score", value.get("readiness_score", 0.0)))
        production_runtime_weight = _ratio(value.get("production_runtime_weight", value.get("runtime_weight", 0.0)))
        readiness_evidence_quality = _ratio(value.get("readiness_evidence_quality", value.get("evidence_quality", production_readiness_score)))
        data_quality = _ratio(value.get("data_quality", readiness_evidence_quality))
        knowledge_quality = _ratio(value.get("knowledge_quality", readiness_evidence_quality))
        strategy_quality = _ratio(value.get("strategy_quality", value.get("strategy_consistency", readiness_evidence_quality)))
        runtime_stability = _ratio(value.get("runtime_stability", value.get("stability_score", readiness_evidence_quality)))
        validation_quality = _ratio(value.get("validation_quality", value.get("validation_consistency", readiness_evidence_quality)))
        monitoring_quality = _ratio(value.get("monitoring_quality", readiness_evidence_quality))
        rollback_readiness = _ratio(value.get("rollback_readiness", value.get("rollback_quality", monitoring_quality)))
        documentation_quality = _ratio(value.get("documentation_quality", value.get("docs_quality", readiness_evidence_quality)))
        handoff_quality = _ratio(value.get("handoff_quality", documentation_quality))
        completion_risk = _ratio(value.get("completion_risk", value.get("risk_pressure", 0.0)))
        completion_source = str(value.get("completion_source", value.get("source", "PRODUCTION_READINESS"))).strip().upper() or "PRODUCTION_READINESS"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            production_readiness_score=production_readiness_score,
            production_runtime_weight=production_runtime_weight,
            readiness_evidence_quality=readiness_evidence_quality,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            strategy_quality=strategy_quality,
            runtime_stability=runtime_stability,
            validation_quality=validation_quality,
            monitoring_quality=monitoring_quality,
            rollback_readiness=rollback_readiness,
            documentation_quality=documentation_quality,
            handoff_quality=handoff_quality,
            completion_risk=completion_risk,
            completion_source=completion_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def operational_closure_quality(self) -> float:
        value = self.monitoring_quality * 0.35 + self.rollback_readiness * 0.30 + self.documentation_quality * 0.20 + self.handoff_quality * 0.15
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
