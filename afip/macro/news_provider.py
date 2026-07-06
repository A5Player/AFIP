"""News provider contracts and deterministic macro news adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Protocol


@dataclass(frozen=True)
class MacroNewsProviderResult:
    """Provider response normalized for AFIP macro news processing."""

    status: str
    source: str
    fetched_at: datetime
    articles: tuple[Mapping[str, object], ...]
    reason: str = "news_provider_ready"


class MacroNewsProvider(Protocol):
    """Contract for free or paid macro news providers."""

    def fetch_news(self, now: datetime | None = None) -> MacroNewsProviderResult:
        """Return raw macro news using the common AFIP news schema."""


class StaticMacroNewsProvider:
    """Deterministic provider used before live RSS or agency feeds are connected."""

    def __init__(self, articles: Iterable[Mapping[str, object]] | None = None, source: str = "STATIC_FREE_NEWS") -> None:
        self.articles = tuple(dict(article) for article in (articles or ()))
        self.source = source

    def fetch_news(self, now: datetime | None = None) -> MacroNewsProviderResult:
        fetched_at = _ensure_timezone(now or datetime.now(timezone.utc))
        return MacroNewsProviderResult(
            status="NEWS_PROVIDER_READY",
            source=self.source,
            fetched_at=fetched_at,
            articles=self.articles,
            reason="static_macro_news_available",
        )


class EmptyMacroNewsProvider:
    """Safe fallback when no live news provider is configured."""

    def __init__(self, source: str = "EMPTY_FREE_NEWS") -> None:
        self.source = source

    def fetch_news(self, now: datetime | None = None) -> MacroNewsProviderResult:
        fetched_at = _ensure_timezone(now or datetime.now(timezone.utc))
        return MacroNewsProviderResult(
            status="NEWS_PROVIDER_EMPTY",
            source=self.source,
            fetched_at=fetched_at,
            articles=(),
            reason="no_news_provider_configured",
        )


class CombinedMacroNewsProvider:
    """Combine multiple macro news providers into one deterministic result."""

    def __init__(self, providers: Iterable[MacroNewsProvider], source: str = "COMBINED_FREE_NEWS") -> None:
        self.providers = tuple(providers)
        self.source = source

    def fetch_news(self, now: datetime | None = None) -> MacroNewsProviderResult:
        fetched_at = _ensure_timezone(now or datetime.now(timezone.utc))
        articles: list[Mapping[str, object]] = []
        active_sources: list[str] = []
        for provider in self.providers:
            result = provider.fetch_news(fetched_at)
            articles.extend(result.articles)
            active_sources.append(result.source)
        status = "NEWS_PROVIDER_READY" if articles else "NEWS_PROVIDER_EMPTY"
        return MacroNewsProviderResult(
            status=status,
            source=self.source,
            fetched_at=fetched_at,
            articles=tuple(articles),
            reason="combined_sources=" + ",".join(active_sources),
        )


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
