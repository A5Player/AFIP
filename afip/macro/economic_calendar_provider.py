"""Economic calendar provider contracts and deterministic free-source adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Protocol


@dataclass(frozen=True)
class EconomicCalendarProviderResult:
    """Provider response normalized for the macro calendar integration layer."""

    status: str
    source: str
    fetched_at: datetime
    events: tuple[Mapping[str, object], ...]
    reason: str = "provider_ready"


class EconomicCalendarProvider(Protocol):
    """Contract for free or paid economic calendar providers."""

    def fetch_events(self, now: datetime | None = None) -> EconomicCalendarProviderResult:
        """Return raw calendar events using the common AFIP event schema."""


class StaticEconomicCalendarProvider:
    """Small deterministic provider used before live external data is connected."""

    def __init__(self, events: Iterable[Mapping[str, object]] | None = None, source: str = "STATIC_FREE_CALENDAR") -> None:
        self.events = tuple(dict(event) for event in (events or ()))
        self.source = source

    def fetch_events(self, now: datetime | None = None) -> EconomicCalendarProviderResult:
        fetched_at = _ensure_timezone(now or datetime.now(timezone.utc))
        return EconomicCalendarProviderResult(
            status="CALENDAR_PROVIDER_READY",
            source=self.source,
            fetched_at=fetched_at,
            events=self.events,
            reason="static_calendar_events_available",
        )


class EmptyEconomicCalendarProvider:
    """Fallback provider when no external calendar source is configured."""

    def __init__(self, source: str = "EMPTY_FREE_CALENDAR") -> None:
        self.source = source

    def fetch_events(self, now: datetime | None = None) -> EconomicCalendarProviderResult:
        fetched_at = _ensure_timezone(now or datetime.now(timezone.utc))
        return EconomicCalendarProviderResult(
            status="CALENDAR_PROVIDER_EMPTY",
            source=self.source,
            fetched_at=fetched_at,
            events=(),
            reason="no_calendar_provider_configured",
        )


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
