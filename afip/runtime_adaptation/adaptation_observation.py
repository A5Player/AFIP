"""Runtime adaptation observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimeAdaptationObservation:
    """Normalized strategy evidence for deterministic runtime adaptation planning."""

    market_regime: str
    signal_context: str
    proposed_strategy_weight: float
    current_runtime_weight: float
    evolution_pressure: float
    evidence_quality: float
    data_quality: float
    knowledge_quality: float
    stability_score: float
    execution_cost: float
    strategy_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RuntimeAdaptationObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        proposed_strategy_weight = _ratio(value.get("proposed_strategy_weight", value.get("strategy_weight", 0.50)))
        current_runtime_weight = _ratio(value.get("current_runtime_weight", value.get("runtime_weight", value.get("current_strategy_weight", 0.50))))
        evolution_pressure = _ratio(value.get("evolution_pressure", value.get("adaptation_pressure", proposed_strategy_weight)))
        evidence_quality = _ratio(value.get("average_evidence_quality", value.get("evidence_quality", 0.0)))
        data_quality = _ratio(value.get("average_data_quality", value.get("data_quality", evidence_quality)))
        knowledge_quality = _ratio(value.get("average_knowledge_quality", value.get("knowledge_quality", evidence_quality)))
        stability_score = _ratio(value.get("stability_score", value.get("runtime_stability", 1.0)))
        execution_cost = _ratio(value.get("execution_cost", value.get("cost_pressure", 0.0)))
        strategy_source = str(value.get("strategy_source", value.get("source", "STRATEGY_EVOLUTION"))).strip().upper() or "STRATEGY_EVOLUTION"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            proposed_strategy_weight=proposed_strategy_weight,
            current_runtime_weight=current_runtime_weight,
            evolution_pressure=evolution_pressure,
            evidence_quality=evidence_quality,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            stability_score=stability_score,
            execution_cost=execution_cost,
            strategy_source=strategy_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def adaptation_quality(self) -> float:
        quality = (
            self.evidence_quality * 0.30
            + self.data_quality * 0.25
            + self.knowledge_quality * 0.25
            + self.stability_score * 0.20
        )
        return round(min(max(quality, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
