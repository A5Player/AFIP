"""Production Milestone E Pack 5 dynamic weight observation model."""

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
class DynamicWeightObservation:
    """Single observed contribution for one financial intelligence source."""

    market_regime: str
    intelligence_name: str
    direction: str
    sample_count: int
    contribution_score: float
    accuracy_rate: float
    stability_score: float
    recency_score: float
    execution_cost_score: float
    conflict_score: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DynamicWeightObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            intelligence_name=_norm(value.get("intelligence_name") or value.get("engine") or value.get("source")),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            contribution_score=_float(value.get("contribution_score") or value.get("contribution")),
            accuracy_rate=_float(value.get("accuracy_rate") or value.get("realized_accuracy_rate")),
            stability_score=_float(value.get("stability_score") or value.get("weight_stability_score")),
            recency_score=_float(value.get("recency_score") or value.get("freshness_score")),
            execution_cost_score=_float(value.get("execution_cost_score") or value.get("cost_score")),
            conflict_score=_float(value.get("conflict_score") or value.get("opposition_score")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def regime_weight_key(self) -> str:
        return f"{self.market_regime}:{self.intelligence_name}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.intelligence_name not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.contribution_score > 0
            and self.accuracy_rate > 0
            and self.stability_score > 0
            and self.recency_score > 0
            and self.execution_cost_score > 0
            and self.conflict_score >= 0
            and bool(self.trace_id)
        )
