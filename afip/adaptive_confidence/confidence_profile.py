"""Adaptive confidence profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveConfidenceProfile:
    """Confidence profile grouped by market regime and signal context."""

    market_regime: str
    signal_context: str
    sample_count: int
    total_samples: float
    average_raw_confidence: float
    average_evidence_quality: float
    average_self_evaluation_score: float
    average_data_quality: float
    average_knowledge_quality: float
    average_stability_score: float

    @property
    def adaptive_confidence(self) -> float:
        raw = self.average_raw_confidence
        evidence = self.average_evidence_quality
        blended = (raw * 0.60) + (evidence * 0.40)
        return round(min(max(blended, 0.0), 1.0), 6)

    @property
    def confidence_adjustment(self) -> float:
        return round(self.adaptive_confidence - self.average_raw_confidence, 6)

    @property
    def confidence_state(self) -> str:
        if self.average_data_quality < 0.60:
            return "DATA_REVIEW_REQUIRED"
        if self.average_self_evaluation_score < 0.60:
            return "EVALUATION_REVIEW_REQUIRED"
        if self.average_stability_score < 0.55:
            return "STABILITY_REVIEW_REQUIRED"
        if self.confidence_adjustment < -0.10:
            return "CONFIDENCE_REDUCED"
        if self.confidence_adjustment > 0.10:
            return "CONFIDENCE_INCREASED"
        return "CONFIDENCE_MAINTAINED"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "sample_count": self.sample_count,
            "total_samples": round(self.total_samples, 6),
            "average_raw_confidence": self.average_raw_confidence,
            "average_evidence_quality": self.average_evidence_quality,
            "average_self_evaluation_score": self.average_self_evaluation_score,
            "average_data_quality": self.average_data_quality,
            "average_knowledge_quality": self.average_knowledge_quality,
            "average_stability_score": self.average_stability_score,
            "adaptive_confidence": self.adaptive_confidence,
            "confidence_adjustment": self.confidence_adjustment,
            "confidence_state": self.confidence_state,
        }
