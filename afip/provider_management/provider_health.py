"""Provider health models for financial data routing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ProviderHealthRecord:
    """Compact health profile for one financial data provider."""

    provider_name: str
    status: str = "READY"
    source_type: str = "FREE"
    latency_ms: float = 0.0
    freshness_seconds: float = 0.0
    coverage_score: float = 100.0
    reliability_score: float = 100.0
    error_count: int = 0
    observed_at: datetime | None = None
    reason: str = "provider_health_ready"

    def normalized_observed_at(self) -> datetime:
        """Return timezone-aware observation time."""
        value = self.observed_at or datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def as_dict(self) -> dict[str, object]:
        return {
            "provider_name": self.provider_name,
            "status": self.status,
            "source_type": self.source_type,
            "latency_ms": round(float(self.latency_ms), 4),
            "freshness_seconds": round(float(self.freshness_seconds), 4),
            "coverage_score": round(float(self.coverage_score), 4),
            "reliability_score": round(float(self.reliability_score), 4),
            "error_count": int(self.error_count),
            "observed_at": self.normalized_observed_at().isoformat(),
            "reason": self.reason,
        }
