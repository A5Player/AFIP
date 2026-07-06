"""Time-aware cache for economic calendar provider results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from afip.macro.economic_calendar_provider import EconomicCalendarProviderResult


@dataclass(frozen=True)
class EconomicCalendarCacheState:
    """Cache state exposed to runtime reports and tests."""

    status: str
    source: str | None
    event_count: int
    age_seconds: float | None
    reason: str


class EconomicCalendarCache:
    """Keep recent calendar results available without repeated provider reads."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = int(ttl_seconds)
        self._cached_result: EconomicCalendarProviderResult | None = None
        self._stored_at: datetime | None = None

    def get(self, now: datetime | None = None) -> EconomicCalendarProviderResult | None:
        current_time = self._ensure_timezone(now or datetime.now(timezone.utc))
        if self._cached_result is None or self._stored_at is None:
            return None
        if current_time - self._stored_at > timedelta(seconds=self.ttl_seconds):
            return None
        return self._cached_result

    def set(self, result: EconomicCalendarProviderResult, now: datetime | None = None) -> EconomicCalendarProviderResult:
        self._cached_result = result
        self._stored_at = self._ensure_timezone(now or result.fetched_at)
        return result

    def resolve(self, provider_result: EconomicCalendarProviderResult | None, now: datetime | None = None) -> EconomicCalendarProviderResult | None:
        cached = self.get(now)
        if cached is not None:
            return cached
        if provider_result is None:
            return None
        return self.set(provider_result, now)

    def state(self, now: datetime | None = None) -> EconomicCalendarCacheState:
        current_time = self._ensure_timezone(now or datetime.now(timezone.utc))
        if self._cached_result is None or self._stored_at is None:
            return EconomicCalendarCacheState(
                status="CALENDAR_CACHE_EMPTY",
                source=None,
                event_count=0,
                age_seconds=None,
                reason="no_cached_calendar_result",
            )
        age_seconds = (current_time - self._stored_at).total_seconds()
        if age_seconds <= self.ttl_seconds:
            status = "CALENDAR_CACHE_READY"
            reason = "cached_calendar_result_available"
        else:
            status = "CALENDAR_CACHE_EXPIRED"
            reason = "cached_calendar_result_expired"
        return EconomicCalendarCacheState(
            status=status,
            source=self._cached_result.source,
            event_count=len(self._cached_result.events),
            age_seconds=round(age_seconds, 2),
            reason=reason,
        )

    def _ensure_timezone(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
