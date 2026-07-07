"""Strategy evolution profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyEvolutionProfile:
    """Knowledge-first strategy evolution profile grouped by regime before signal."""

    market_regime: str
    signal_context: str
    sample_count: int
    total_weight: float
    average_experience_score: float
    average_expectancy: float
    average_positive_rate: float
    average_evidence_quality: float
    average_data_quality: float
    average_knowledge_quality: float
    average_reliability_score: float
    average_current_strategy_weight: float

    @property
    def evolution_pressure(self) -> float:
        outcome = min(max((self.average_expectancy + 1.0) / 2.0, 0.0), 1.0)
        value = (
            self.average_experience_score * 0.30
            + outcome * 0.25
            + self.average_positive_rate * 0.20
            + self.average_evidence_quality * 0.25
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def proposed_strategy_weight(self) -> float:
        delta = (self.evolution_pressure - 0.50) * 0.20
        value = self.average_current_strategy_weight + delta
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def weight_adjustment(self) -> float:
        return round(self.proposed_strategy_weight - self.average_current_strategy_weight, 6)

    @property
    def evolution_state(self) -> str:
        if self.average_data_quality < 0.60 or self.average_knowledge_quality < 0.60 or self.average_reliability_score < 0.60:
            return "EVIDENCE_REVIEW_REQUIRED"
        if self.sample_count <= 0:
            return "KNOWLEDGE_REQUIRED"
        if self.average_expectancy < 0.0:
            return "REDUCE_STRATEGY_WEIGHT"
        if self.evolution_pressure >= 0.75:
            return "INCREASE_STRATEGY_WEIGHT"
        return "MAINTAIN_STRATEGY_WEIGHT"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "sample_count": self.sample_count,
            "total_weight": round(self.total_weight, 6),
            "average_experience_score": self.average_experience_score,
            "average_expectancy": self.average_expectancy,
            "average_positive_rate": self.average_positive_rate,
            "average_evidence_quality": self.average_evidence_quality,
            "average_data_quality": self.average_data_quality,
            "average_knowledge_quality": self.average_knowledge_quality,
            "average_reliability_score": self.average_reliability_score,
            "average_current_strategy_weight": self.average_current_strategy_weight,
            "evolution_pressure": self.evolution_pressure,
            "proposed_strategy_weight": self.proposed_strategy_weight,
            "weight_adjustment": self.weight_adjustment,
            "evolution_state": self.evolution_state,
        }
