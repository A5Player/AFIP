"""Data quality assessment for normalized financial inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class DataQualityResult:
    """Quality decision for a normalized provider payload."""

    status: str
    score: float
    decision: str
    missing_fields: tuple[str, ...]
    duplicate_count: int
    stale: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "score": round(self.score, 4),
            "decision": self.decision,
            "missing_fields": list(self.missing_fields),
            "duplicate_count": self.duplicate_count,
            "stale": self.stale,
            "reason": self.reason,
        }


class DataQualityAssessment:
    """Check field completeness, duplicate input, and freshness before runtime usage."""

    def __init__(self, required_fields: tuple[str, ...] = (), max_age_seconds: float = 900.0) -> None:
        self.required_fields = tuple(required_fields)
        self.max_age_seconds = float(max_age_seconds)

    def assess(
        self,
        values: Mapping[str, object],
        observed_at: datetime | None = None,
        now: datetime | None = None,
    ) -> DataQualityResult:
        normalized_values = {str(key): value for key, value in values.items()}
        missing = tuple(field for field in self.required_fields if field not in normalized_values)
        duplicate_count = self._duplicate_count(normalized_values)
        observed = self._normalize_time(observed_at)
        current = self._normalize_time(now)
        age = max(0.0, (current - observed).total_seconds())
        stale = age > self.max_age_seconds

        completeness_score = 100.0 if not self.required_fields else 100.0 * (1.0 - (len(missing) / len(self.required_fields)))
        duplicate_penalty = min(40.0, duplicate_count * 10.0)
        stale_penalty = 35.0 if stale else 0.0
        score = max(0.0, min(100.0, completeness_score - duplicate_penalty - stale_penalty))

        if stale and missing:
            decision = "BLOCKED"
            status = "DATA_QUALITY_BLOCKED"
            reason = "data_quality_blocked"
        elif stale and duplicate_count > 0:
            decision = "BLOCKED"
            status = "DATA_QUALITY_BLOCKED"
            reason = "data_quality_blocked"
        elif score >= 80.0:
            decision = "READY"
            status = "DATA_QUALITY_READY"
            reason = "data_quality_ready"
        elif score >= 50.0:
            decision = "REVIEW"
            status = "DATA_QUALITY_REVIEW"
            reason = "data_quality_review"
        else:
            decision = "BLOCKED"
            status = "DATA_QUALITY_BLOCKED"
            reason = "data_quality_blocked"

        return DataQualityResult(
            status=status,
            score=score,
            decision=decision,
            missing_fields=missing,
            duplicate_count=duplicate_count,
            stale=stale,
            reason=reason,
        )

    @staticmethod
    def _normalize_time(value: datetime | None) -> datetime:
        result = value or datetime.now(timezone.utc)
        if result.tzinfo is None:
            return result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)

    @staticmethod
    def _duplicate_count(values: Mapping[str, object]) -> int:
        seen: set[object] = set()
        duplicates = 0
        for value in values.values():
            comparable = value if isinstance(value, (str, int, float, bool, type(None))) else repr(value)
            if comparable in seen:
                duplicates += 1
            seen.add(comparable)
        return duplicates
