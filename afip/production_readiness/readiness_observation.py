"""Production readiness observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionReadinessObservation:
    """Normalized validation evidence for deterministic production readiness review."""

    market_regime: str
    signal_context: str
    validation_score: float
    approved_runtime_weight: float
    evidence_quality: float
    data_quality: float
    knowledge_quality: float
    explainability_score: float
    runtime_stability: float
    validation_sample_quality: float
    validation_consistency: float
    validation_risk: float
    deployment_control_quality: float
    monitoring_quality: float
    rollback_readiness: float
    readiness_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionReadinessObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        validation_score = _ratio(value.get("validation_score", value.get("score", 0.0)))
        approved_runtime_weight = _ratio(value.get("approved_runtime_weight", value.get("runtime_weight", 0.0)))
        evidence_quality = _ratio(value.get("evidence_quality", value.get("quality", validation_score)))
        data_quality = _ratio(value.get("data_quality", evidence_quality))
        knowledge_quality = _ratio(value.get("knowledge_quality", evidence_quality))
        explainability_score = _ratio(value.get("explainability_score", value.get("explainability", evidence_quality)))
        runtime_stability = _ratio(value.get("runtime_stability", value.get("stability_score", evidence_quality)))
        validation_sample_quality = _ratio(value.get("validation_sample_quality", evidence_quality))
        validation_consistency = _ratio(value.get("validation_consistency", evidence_quality))
        validation_risk = _ratio(value.get("validation_risk", value.get("risk_pressure", 0.0)))
        deployment_control_quality = _ratio(value.get("deployment_control_quality", value.get("deployment_quality", evidence_quality)))
        monitoring_quality = _ratio(value.get("monitoring_quality", evidence_quality))
        rollback_readiness = _ratio(value.get("rollback_readiness", value.get("rollback_quality", deployment_control_quality)))
        readiness_source = str(value.get("readiness_source", value.get("source", "VALIDATION"))).strip().upper() or "VALIDATION"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            validation_score=validation_score,
            approved_runtime_weight=approved_runtime_weight,
            evidence_quality=evidence_quality,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            explainability_score=explainability_score,
            runtime_stability=runtime_stability,
            validation_sample_quality=validation_sample_quality,
            validation_consistency=validation_consistency,
            validation_risk=validation_risk,
            deployment_control_quality=deployment_control_quality,
            monitoring_quality=monitoring_quality,
            rollback_readiness=rollback_readiness,
            readiness_source=readiness_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def operational_quality(self) -> float:
        quality = (
            self.deployment_control_quality * 0.35
            + self.monitoring_quality * 0.35
            + self.rollback_readiness * 0.30
        )
        return round(min(max(quality, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
