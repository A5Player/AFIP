"""Small in-memory cache for macro news provider results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .news_provider import MacroNewsProviderResult


@dataclass(frozen=True)
class MacroNewsCacheState:
    """Current state of the macro news cache."""

    status: str
    age_seconds: float | None
    ttl_seconds: int
    reason: str


class MacroNewsCache:
    """Cache provider results to reduce duplicate external news reads."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = int(ttl_seconds)
        self._result: MacroNewsProviderResult | None = None
        self._stored_at: datetime | None = None

    def set(self, result: MacroNewsProviderResult, now: datetime | None = None) -> None:
        self._result = result
        self._stored_at = _ensure_timezone(now or datetime.now(timezone.utc))

    def get(self, now: datetime | None = None) -> MacroNewsProviderResult | None:
        state = self.state(now)
        if state.status == "NEWS_CACHE_READY":
            return self._result
        return None

    def state(self, now: datetime | None = None) -> MacroNewsCacheState:
        if self._result is None or self._stored_at is None:
            return MacroNewsCacheState("NEWS_CACHE_EMPTY", None, self.ttl_seconds, "no_cached_news")
        current = _ensure_timezone(now or datetime.now(timezone.utc))
        age_seconds = max(0.0, (current - self._stored_at).total_seconds())
        if age_seconds <= self.ttl_seconds:
            return MacroNewsCacheState("NEWS_CACHE_READY", age_seconds, self.ttl_seconds, "cached_news_valid")
        return MacroNewsCacheState("NEWS_CACHE_EXPIRED", age_seconds, self.ttl_seconds, "cached_news_expired")


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
