"""TTL cache and freshness checks for macro market factor data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .market_factor_provider import MarketFactorProviderResult


@dataclass(frozen=True)
class MarketFactorCacheState:
    """Current market factor cache state."""

    status: str
    age_seconds: float | None
    reason: str


class MarketFactorCache:
    """Small in-memory cache to avoid repeated provider reads."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = max(1, int(ttl_seconds))
        self._result: MarketFactorProviderResult | None = None
        self._stored_at: datetime | None = None

    def set(self, result: MarketFactorProviderResult, stored_at: datetime | None = None) -> None:
        self._result = result
        self._stored_at = stored_at or datetime.now(timezone.utc)

    def get(self, current_time: datetime | None = None) -> MarketFactorProviderResult | None:
        if self._result is None or self._stored_at is None:
            return None
        current_time = current_time or datetime.now(timezone.utc)
        if self._age_seconds(current_time) <= self.ttl_seconds:
            return self._result
        return None

    def state(self, current_time: datetime | None = None) -> MarketFactorCacheState:
        current_time = current_time or datetime.now(timezone.utc)
        if self._result is None or self._stored_at is None:
            return MarketFactorCacheState("MARKET_FACTOR_CACHE_EMPTY", None, "no_market_factor_cache_value")
        age = self._age_seconds(current_time)
        if age <= self.ttl_seconds:
            return MarketFactorCacheState("MARKET_FACTOR_CACHE_READY", round(age, 3), "market_factor_cache_hit")
        return MarketFactorCacheState("MARKET_FACTOR_CACHE_EXPIRED", round(age, 3), "market_factor_cache_expired")

    def _age_seconds(self, current_time: datetime) -> float:
        assert self._stored_at is not None
        return max(0.0, (current_time - self._stored_at).total_seconds())
