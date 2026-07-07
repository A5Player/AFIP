"""Experience knowledge profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperienceKnowledgeProfile:
    """Knowledge profile grouped by market regime before signal context."""

    market_regime: str
    signal_context: str
    sample_count: int
    total_weight: float
    weighted_result: float
    positive_rate: float
    average_adaptive_confidence: float
    average_self_evaluation_score: float
    average_data_quality: float
    average_knowledge_quality: float
    average_recency_score: float
    average_reliability_score: float

    @property
    def expectancy(self) -> float:
        if self.total_weight == 0.0:
            return 0.0
        return round(self.weighted_result / self.total_weight, 6)

    @property
    def experience_score(self) -> float:
        outcome_score = min(max((self.expectancy + 1.0) / 2.0, 0.0), 1.0)
        value = (
            self.positive_rate * 0.25
            + outcome_score * 0.20
            + self.average_reliability_score * 0.25
            + self.average_data_quality * 0.15
            + self.average_knowledge_quality * 0.15
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def knowledge_state(self) -> str:
        if self.average_data_quality < 0.60:
            return "DATA_REVIEW_REQUIRED"
        if self.average_knowledge_quality < 0.60:
            return "KNOWLEDGE_REVIEW_REQUIRED"
        if self.average_recency_score < 0.50:
            return "RECENCY_REVIEW_REQUIRED"
        if self.expectancy < 0.0:
            return "OUTCOME_REVIEW_REQUIRED"
        if self.experience_score >= 0.75:
            return "EXPERIENCE_SUPPORTED"
        return "EXPERIENCE_OBSERVED"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "sample_count": self.sample_count,
            "total_weight": round(self.total_weight, 6),
            "weighted_result": round(self.weighted_result, 6),
            "positive_rate": self.positive_rate,
            "average_adaptive_confidence": self.average_adaptive_confidence,
            "average_self_evaluation_score": self.average_self_evaluation_score,
            "average_data_quality": self.average_data_quality,
            "average_knowledge_quality": self.average_knowledge_quality,
            "average_recency_score": self.average_recency_score,
            "average_reliability_score": self.average_reliability_score,
            "expectancy": self.expectancy,
            "experience_score": self.experience_score,
            "knowledge_state": self.knowledge_state,
        }
