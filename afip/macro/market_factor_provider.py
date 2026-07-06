"""Provider contracts for macro market factors."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Protocol


@dataclass(frozen=True)
class MarketFactorProviderResult:
    """Normalized provider output for macro market factor values."""

    status: str
    source: str
    observed_at: datetime
    factors: Mapping[str, float] = field(default_factory=dict)
    reason: str = "market_factor_provider_ready"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "source": self.source,
            "observed_at": self.observed_at.isoformat(),
            "factors": dict(self.factors),
            "reason": self.reason,
        }


class MarketFactorProvider(Protocol):
    """Read macro market factors from a free or paid data source."""

    def fetch_factors(self, observed_at: datetime | None = None) -> MarketFactorProviderResult:
        """Return normalized market factor values."""


class EmptyMarketFactorProvider:
    """Safe fallback when no market factor data provider is configured."""

    def fetch_factors(self, observed_at: datetime | None = None) -> MarketFactorProviderResult:
        observed_at = observed_at or datetime.now(timezone.utc)
        return MarketFactorProviderResult(
            status="MARKET_FACTOR_PROVIDER_EMPTY",
            source="EMPTY_MARKET_FACTOR_PROVIDER",
            observed_at=observed_at,
            factors={},
            reason="no_market_factor_provider_configured",
        )


class StaticMarketFactorProvider:
    """Deterministic provider used by tests, replay, and offline simulation."""

    def __init__(self, factors: Mapping[str, object] | None = None, source: str = "STATIC_FREE_MARKET_FACTORS") -> None:
        self._factors = {str(key): self._to_float(value) for key, value in (factors or {}).items()}
        self._source = source

    def fetch_factors(self, observed_at: datetime | None = None) -> MarketFactorProviderResult:
        observed_at = observed_at or datetime.now(timezone.utc)
        return MarketFactorProviderResult(
            status="MARKET_FACTOR_PROVIDER_READY",
            source=self._source,
            observed_at=observed_at,
            factors=dict(self._factors),
            reason="static_market_factor_provider_ready",
        )

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
