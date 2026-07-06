"""Provider registry for macro, institutional, news, and market data sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from afip.provider_management.provider_health import ProviderHealthRecord
from afip.provider_management.provider_quality import ProviderQualityEngine, ProviderQualityScore


@dataclass
class ProviderRegistry:
    """In-memory registry of financial data providers and quality profiles."""

    records: list[ProviderHealthRecord] = field(default_factory=list)
    quality_engine: ProviderQualityEngine = field(default_factory=ProviderQualityEngine)

    def register(self, record: ProviderHealthRecord) -> None:
        """Add or replace one provider health record."""
        self.records = [item for item in self.records if item.provider_name != record.provider_name]
        self.records.append(record)

    def extend(self, records: Iterable[ProviderHealthRecord]) -> None:
        for record in records:
            self.register(record)

    def quality_scores(self) -> list[ProviderQualityScore]:
        """Return provider scores sorted by quality descending."""
        scores = [self.quality_engine.score(record) for record in self.records]
        return sorted(scores, key=lambda item: (-item.score, item.provider_name))

    def best_available(self) -> ProviderQualityScore | None:
        """Return the highest-quality provider that can be used by runtime."""
        for score in self.quality_scores():
            if score.decision in {"READY", "REVIEW"}:
                return score
        return None

    def as_dict(self) -> dict[str, object]:
        scores = self.quality_scores()
        best = self.best_available()
        return {
            "status": "PROVIDER_REGISTRY_READY" if scores else "PROVIDER_REGISTRY_EMPTY",
            "provider_count": len(scores),
            "best_provider": best.as_dict() if best else None,
            "providers": [score.as_dict() for score in scores],
            "reason": "provider_registry_ranked" if scores else "no_provider_records",
        }
