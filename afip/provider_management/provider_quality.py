"""Quality scoring for financial data providers."""

from __future__ import annotations

from dataclasses import dataclass

from afip.provider_management.provider_health import ProviderHealthRecord


@dataclass(frozen=True)
class ProviderQualityScore:
    """Rankable quality score for one provider."""

    provider_name: str
    status: str
    score: float
    decision: str
    reason: str
    components: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "provider_name": self.provider_name,
            "status": self.status,
            "score": round(self.score, 4),
            "decision": self.decision,
            "reason": self.reason,
            "components": {key: round(value, 4) for key, value in self.components.items()},
        }


class ProviderQualityEngine:
    """Score provider readiness using freshness, latency, coverage, and reliability."""

    def __init__(
        self,
        max_latency_ms: float = 2500.0,
        max_freshness_seconds: float = 900.0,
        review_threshold: float = 55.0,
        ready_threshold: float = 70.0,
    ) -> None:
        self.max_latency_ms = float(max_latency_ms)
        self.max_freshness_seconds = float(max_freshness_seconds)
        self.review_threshold = float(review_threshold)
        self.ready_threshold = float(ready_threshold)

    def score(self, record: ProviderHealthRecord) -> ProviderQualityScore:
        status = record.status.upper()
        if status in {"OFFLINE", "ERROR", "UNAVAILABLE"}:
            return ProviderQualityScore(
                provider_name=record.provider_name,
                status=status,
                score=0.0,
                decision="UNAVAILABLE",
                reason="provider_unavailable",
                components={"status": 0.0, "latency": 0.0, "freshness": 0.0, "coverage": 0.0, "reliability": 0.0},
            )

        latency_score = self._inverse_score(record.latency_ms, self.max_latency_ms)
        freshness_score = self._inverse_score(record.freshness_seconds, self.max_freshness_seconds)
        coverage_score = self._bounded(record.coverage_score)
        reliability_score = self._bounded(record.reliability_score - (record.error_count * 4.0))
        status_score = 100.0 if status in {"READY", "OK", "ACTIVE"} else 65.0

        total = (
            status_score * 0.15
            + latency_score * 0.2
            + freshness_score * 0.25
            + coverage_score * 0.2
            + reliability_score * 0.2
        )
        if total >= self.ready_threshold:
            decision = "READY"
            reason = "provider_quality_ready"
        elif total >= self.review_threshold:
            decision = "REVIEW"
            reason = "provider_quality_review"
        else:
            decision = "DEGRADED"
            reason = "provider_quality_degraded"

        return ProviderQualityScore(
            provider_name=record.provider_name,
            status=status,
            score=self._bounded(total),
            decision=decision,
            reason=reason,
            components={
                "status": status_score,
                "latency": latency_score,
                "freshness": freshness_score,
                "coverage": coverage_score,
                "reliability": reliability_score,
            },
        )

    @staticmethod
    def _bounded(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    @classmethod
    def _inverse_score(cls, value: float, limit: float) -> float:
        if limit <= 0:
            return 100.0
        return cls._bounded(100.0 - ((max(0.0, float(value)) / limit) * 100.0))
