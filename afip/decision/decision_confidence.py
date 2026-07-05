from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionConfidenceResult:
    status: str
    confidence: float
    confidence_level: str
    reason: str


class DecisionConfidence:
    """Calculate production decision confidence from fusion, weight, conflict, and risk inputs."""

    def calculate(
        self,
        fusion_score: float = 0.0,
        adaptive_weight_score: float = 0.0,
        consensus_score: float = 0.0,
        conflict_ratio: float = 0.0,
        risk_accepted: bool = True,
    ) -> DecisionConfidenceResult:
        fusion = self._normalize_score(fusion_score)
        adaptive = self._normalize_score(adaptive_weight_score)
        consensus = self._normalize_score(consensus_score)
        conflict = self._normalize_score(conflict_ratio)

        confidence = (fusion * 0.35) + (adaptive * 0.30) + (consensus * 0.25) + ((1.0 - conflict) * 0.10)
        if not risk_accepted:
            confidence *= 0.45

        rounded = round(max(0.0, min(confidence, 1.0)), 4)
        level = self._level(rounded, risk_accepted)
        return DecisionConfidenceResult(
            status="DECISION_CONFIDENCE_READY",
            confidence=rounded,
            confidence_level=level,
            reason=self._reason(level, risk_accepted),
        )

    @staticmethod
    def _normalize_score(value: float) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        if score > 1.0:
            score = score / 100.0
        return max(0.0, min(score, 1.0))

    @staticmethod
    def _level(confidence: float, risk_accepted: bool) -> str:
        if not risk_accepted:
            return "REDUCED"
        if confidence >= 0.78:
            return "HIGH"
        if confidence >= 0.58:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _reason(level: str, risk_accepted: bool) -> str:
        if not risk_accepted:
            return "risk_not_accepted"
        if level == "HIGH":
            return "decision_confidence_supported_by_fusion"
        if level == "MODERATE":
            return "decision_confidence_requires_selective_execution"
        return "decision_confidence_insufficient"
