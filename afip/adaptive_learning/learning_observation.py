"""Production Milestone E Pack 9 adaptive learning observation model."""

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
class AdaptiveLearningObservation:
    """Single data-derived adaptive learning observation for financial intelligence."""

    market_regime: str
    learning_context: str
    direction: str
    sample_count: int
    reinforcement_score: float
    adaptation_score: float
    forgetting_score: float
    validation_score: float
    stability_score: float
    drift_risk_score: float
    execution_cost_score: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AdaptiveLearningObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            learning_context=_norm(value.get("learning_context") or value.get("context") or value.get("pattern_family")),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            reinforcement_score=_float(value.get("reinforcement_score") or value.get("reinforcement")),
            adaptation_score=_float(value.get("adaptation_score") or value.get("adaptation")),
            forgetting_score=_float(value.get("forgetting_score") or value.get("forgetting")),
            validation_score=_float(value.get("validation_score") or value.get("validation")),
            stability_score=_float(value.get("stability_score") or value.get("stability")),
            drift_risk_score=_float(value.get("drift_risk_score") or value.get("drift_risk")),
            execution_cost_score=_float(value.get("execution_cost_score") or value.get("cost_score")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def learning_key(self) -> str:
        return f"{self.market_regime}:{self.learning_context}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.learning_context not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.reinforcement_score > 0
            and self.adaptation_score > 0
            and self.forgetting_score >= 0
            and self.validation_score > 0
            and self.stability_score > 0
            and self.drift_risk_score >= 0
            and self.execution_cost_score >= 0
            and bool(self.trace_id)
        )
