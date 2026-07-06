"""Production Milestone C Pack 3 macro news runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from afip.macro.news_cache import MacroNewsCache
from afip.macro.news_confidence_engine import MacroNewsConfidenceEngine
from afip.macro.news_impact_engine import MacroNewsImpactEngine
from afip.macro.news_provider import EmptyMacroNewsProvider, MacroNewsProvider, StaticMacroNewsProvider


class ProductionMilestoneCNewsRuntime:
    """Run provider, cache, impact, and confidence stages for macro news."""

    def __init__(self, provider: MacroNewsProvider | None = None, cache_ttl_seconds: int = 300) -> None:
        self.provider = provider or EmptyMacroNewsProvider()
        self.cache = MacroNewsCache(ttl_seconds=cache_ttl_seconds)
        self.impact_engine = MacroNewsImpactEngine()
        self.confidence_engine = MacroNewsConfidenceEngine()

    def run(self, articles: Iterable[Mapping[str, object]] | None = None, now: datetime | None = None):
        current = _ensure_timezone(now or datetime.now(timezone.utc))
        provider = StaticMacroNewsProvider(articles) if articles is not None else self.provider
        cached = self.cache.get(current)
        provider_result = cached or provider.fetch_news(current)
        if cached is None:
            self.cache.set(provider_result, current)
        impacts = tuple(self.impact_engine.assess(article, current) for article in provider_result.articles)
        confidence = self.confidence_engine.aggregate(impacts)
        return provider_result, impacts, confidence, self.cache.state(current)

    def run_dict(self, articles: Iterable[Mapping[str, object]] | None = None, now: datetime | None = None) -> dict[str, object]:
        provider_result, impacts, confidence, cache_state = self.run(articles, now)
        top_impact = max((item.impact_score for item in impacts), default=0.0)
        top_confidence = max((item.confidence_score for item in impacts), default=0.0)
        return {
            "runtime": "PRODUCTION_MILESTONE_C_NEWS_RUNTIME",
            "status": confidence.status,
            "provider_status": provider_result.status,
            "provider_source": provider_result.source,
            "cache_status": cache_state.status,
            "article_count": confidence.article_count,
            "supportive_count": confidence.supportive_count,
            "pressure_count": confidence.pressure_count,
            "neutral_count": confidence.neutral_count,
            "gold_bias": confidence.gold_bias,
            "confidence_score": confidence.confidence_score,
            "impact_score": confidence.impact_score,
            "top_article_impact": round(top_impact, 2),
            "top_article_confidence": round(top_confidence, 2),
            "trade_instruction": confidence.trade_instruction,
            "reason": confidence.reason,
        }


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
