"""Runtime adaptation profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeAdaptationProfile:
    """Regime-first runtime adaptation plan without automatic runtime writes."""

    market_regime: str
    signal_context: str
    proposed_strategy_weight: float
    current_runtime_weight: float
    evolution_pressure: float
    adaptation_quality: float
    data_quality: float
    knowledge_quality: float
    stability_score: float
    execution_cost: float

    @property
    def raw_adjustment(self) -> float:
        return round(self.proposed_strategy_weight - self.current_runtime_weight, 6)

    @property
    def adaptation_strength(self) -> float:
        cost_adjusted_quality = self.adaptation_quality * (1.0 - (self.execution_cost * 0.50))
        value = self.evolution_pressure * 0.45 + cost_adjusted_quality * 0.55
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def planned_runtime_weight(self) -> float:
        capped_adjustment = max(min(self.raw_adjustment, 0.10), -0.10)
        quality_scaled_adjustment = capped_adjustment * self.adaptation_strength
        value = self.current_runtime_weight + quality_scaled_adjustment
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def runtime_weight_delta(self) -> float:
        return round(self.planned_runtime_weight - self.current_runtime_weight, 6)

    @property
    def adaptation_state(self) -> str:
        if self.data_quality < 0.60 or self.knowledge_quality < 0.60 or self.stability_score < 0.60:
            return "RUNTIME_REVIEW_REQUIRED"
        if self.execution_cost > 0.70:
            return "EXECUTION_COST_REVIEW_REQUIRED"
        if self.runtime_weight_delta > 0.01:
            return "PLAN_WEIGHT_INCREASE"
        if self.runtime_weight_delta < -0.01:
            return "PLAN_WEIGHT_REDUCTION"
        return "MAINTAIN_RUNTIME_WEIGHT"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "proposed_strategy_weight": self.proposed_strategy_weight,
            "current_runtime_weight": self.current_runtime_weight,
            "evolution_pressure": self.evolution_pressure,
            "adaptation_quality": self.adaptation_quality,
            "data_quality": self.data_quality,
            "knowledge_quality": self.knowledge_quality,
            "stability_score": self.stability_score,
            "execution_cost": self.execution_cost,
            "raw_adjustment": self.raw_adjustment,
            "adaptation_strength": self.adaptation_strength,
            "planned_runtime_weight": self.planned_runtime_weight,
            "runtime_weight_delta": self.runtime_weight_delta,
            "adaptation_state": self.adaptation_state,
        }
