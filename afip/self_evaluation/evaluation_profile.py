"""Self evaluation profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SelfEvaluationProfile:
    """Evaluation profile grouped by market regime and decision status."""

    market_regime: str
    decision_status: str
    sample_count: int
    total_weight: float
    weighted_result: float
    win_rate: float
    average_expected_confidence: float
    average_confidence_error: float
    average_data_quality: float
    average_knowledge_quality: float

    @property
    def expectancy(self) -> float:
        if self.total_weight == 0.0:
            return 0.0
        return round(self.weighted_result / self.total_weight, 6)

    @property
    def evaluation_score(self) -> float:
        if self.sample_count == 0:
            return 0.0
        confidence_alignment = 1.0 - self.average_confidence_error
        value = (self.win_rate + confidence_alignment + self.average_data_quality + self.average_knowledge_quality) / 4.0
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def improvement_priority(self) -> str:
        if self.average_data_quality < self.average_knowledge_quality:
            return "DATA_QUALITY_REVIEW"
        if self.average_confidence_error > 0.35:
            return "CONFIDENCE_ALIGNMENT_REVIEW"
        if self.expectancy < 0.0:
            return "DECISION_OUTCOME_REVIEW"
        return "MAINTAIN_CURRENT_PROCESS"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "decision_status": self.decision_status,
            "sample_count": self.sample_count,
            "total_weight": round(self.total_weight, 6),
            "weighted_result": round(self.weighted_result, 6),
            "win_rate": self.win_rate,
            "average_expected_confidence": self.average_expected_confidence,
            "average_confidence_error": self.average_confidence_error,
            "average_data_quality": self.average_data_quality,
            "average_knowledge_quality": self.average_knowledge_quality,
            "expectancy": self.expectancy,
            "evaluation_score": self.evaluation_score,
            "improvement_priority": self.improvement_priority,
        }
