"""Quality assessment for market knowledge records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class KnowledgeQualityAssessment:
    """Quality profile for a compact knowledge record."""

    status: str
    quality_score: float
    sample_confidence: float
    freshness_score: float
    stability_score: float
    usability: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "quality_score": self.quality_score,
            "sample_confidence": self.sample_confidence,
            "freshness_score": self.freshness_score,
            "stability_score": self.stability_score,
            "usability": self.usability,
            "reason": self.reason,
        }


class KnowledgeQualityEngine:
    """Score whether aggregated market knowledge is ready for decision support."""

    def assess(self, record: Mapping[str, object], *, now: datetime | None = None) -> KnowledgeQualityAssessment:
        timestamp = now or datetime.now(timezone.utc)
        occurrence_count = int(record.get("occurrence_count", 0))
        statistics = record.get("statistics", {})
        stats = statistics if isinstance(statistics, Mapping) else {}
        result_std = self._to_float(stats.get("result_std"), 0.0)
        expectancy = abs(self._to_float(stats.get("expectancy"), 0.0))
        last_seen = self._parse_datetime(record.get("last_seen"), timestamp)

        sample_confidence = min(100.0, occurrence_count * 4.0)
        days_old = max(0.0, (timestamp - last_seen).total_seconds() / 86400.0)
        freshness_score = max(0.0, 100.0 - days_old * 2.0)
        stability_score = self._stability(expectancy, result_std, occurrence_count)
        quality_score = round((sample_confidence * 0.42) + (freshness_score * 0.28) + (stability_score * 0.30), 2)
        usability = self._usability(quality_score, occurrence_count)
        return KnowledgeQualityAssessment(
            status="KNOWLEDGE_QUALITY_READY",
            quality_score=quality_score,
            sample_confidence=round(sample_confidence, 2),
            freshness_score=round(freshness_score, 2),
            stability_score=round(stability_score, 2),
            usability=usability,
            reason=self._reason(usability),
        )

    def assess_dict(self, record: Mapping[str, object], *, now: datetime | None = None) -> dict[str, object]:
        return self.assess(record, now=now).as_dict()

    def _stability(self, expectancy: float, result_std: float, occurrence_count: int) -> float:
        if occurrence_count == 0:
            return 0.0
        if result_std == 0:
            return 70.0 if expectancy > 0 else 50.0
        ratio = expectancy / result_std
        return min(100.0, max(0.0, 45.0 + ratio * 45.0))

    def _usability(self, quality_score: float, occurrence_count: int) -> str:
        if occurrence_count < 5:
            return "OBSERVE_ONLY"
        if quality_score >= 75.0:
            return "DECISION_SUPPORT_READY"
        if quality_score >= 55.0:
            return "RESEARCH_REVIEW"
        return "OBSERVE_ONLY"

    def _reason(self, usability: str) -> str:
        if usability == "DECISION_SUPPORT_READY":
            return "knowledge_sample_quality_ready"
        if usability == "RESEARCH_REVIEW":
            return "knowledge_requires_research_review"
        return "knowledge_sample_not_ready"

    @staticmethod
    def _parse_datetime(value: object, fallback: datetime) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            return fallback
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _to_float(value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
