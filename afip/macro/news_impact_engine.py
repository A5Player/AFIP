"""Macro news impact scoring for gold-sensitive market conditions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class MacroNewsArticle:
    """Normalized macro news article."""

    title: str
    source: str
    published_at: datetime
    summary: str = ""
    topic: str = "GENERAL"
    currency: str = "USD"


@dataclass(frozen=True)
class MacroNewsImpact:
    """Impact assessment for a normalized macro news article."""

    title: str
    source: str
    topic: str
    direction: str
    impact_score: float
    urgency_score: float
    confidence_score: float
    reason: str


class MacroNewsImpactEngine:
    """Score macro news by topic, freshness, source quality, and gold relevance."""

    HIGH_IMPACT_TOPICS = {
        "FOMC": 96.0,
        "FED": 92.0,
        "CPI": 94.0,
        "PCE": 92.0,
        "NFP": 90.0,
        "JOBS": 86.0,
        "TREASURY_YIELD": 88.0,
        "DXY": 84.0,
        "REAL_YIELD": 92.0,
        "INFLATION": 88.0,
    }
    TRUSTED_SOURCES = {"FED", "BLS", "BEA", "TREASURY", "CFTC", "STATIC_FREE_NEWS", "COMBINED_FREE_NEWS"}

    def assess(self, article: MacroNewsArticle | Mapping[str, object], now: datetime | None = None) -> MacroNewsImpact:
        normalized = normalize_news_article(article)
        current = _ensure_timezone(now or datetime.now(timezone.utc))
        topic_key = normalized.topic.upper().replace(" ", "_")
        text = f"{normalized.title} {normalized.summary}".upper()
        base_impact = self.HIGH_IMPACT_TOPICS.get(topic_key, _keyword_impact(text))
        age_minutes = max(0.0, (current - normalized.published_at).total_seconds() / 60.0)
        urgency = _urgency_from_age(age_minutes)
        source_quality = 92.0 if normalized.source.upper() in self.TRUSTED_SOURCES else 72.0
        direction = _direction_from_text(text)
        confidence = min(99.0, round((base_impact * 0.45) + (urgency * 0.30) + (source_quality * 0.25), 2))
        reason = f"topic={topic_key};age_minutes={round(age_minutes, 2)};source_quality={source_quality}"
        return MacroNewsImpact(
            title=normalized.title,
            source=normalized.source,
            topic=topic_key,
            direction=direction,
            impact_score=round(base_impact, 2),
            urgency_score=round(urgency, 2),
            confidence_score=confidence,
            reason=reason,
        )


def normalize_news_article(article: MacroNewsArticle | Mapping[str, object]) -> MacroNewsArticle:
    if isinstance(article, MacroNewsArticle):
        return article
    title = str(article.get("title", "")).strip() or "Untitled Macro News"
    source = str(article.get("source", "UNKNOWN_NEWS_SOURCE")).strip() or "UNKNOWN_NEWS_SOURCE"
    raw_published = article.get("published_at") or article.get("time") or datetime.now(timezone.utc)
    if isinstance(raw_published, datetime):
        published_at = _ensure_timezone(raw_published)
    else:
        published_at = _ensure_timezone(datetime.fromisoformat(str(raw_published).replace("Z", "+00:00")))
    return MacroNewsArticle(
        title=title,
        source=source,
        published_at=published_at,
        summary=str(article.get("summary", "")),
        topic=str(article.get("topic", "GENERAL")),
        currency=str(article.get("currency", "USD")),
    )


def _keyword_impact(text: str) -> float:
    if any(keyword in text for keyword in ("FED", "FOMC", "RATE", "INFLATION", "CPI", "PCE")):
        return 88.0
    if any(keyword in text for keyword in ("JOBS", "PAYROLL", "YIELD", "DOLLAR")):
        return 82.0
    if "GOLD" in text:
        return 70.0
    return 35.0


def _urgency_from_age(age_minutes: float) -> float:
    if age_minutes <= 15:
        return 96.0
    if age_minutes <= 60:
        return 86.0
    if age_minutes <= 240:
        return 68.0
    return 38.0


def _direction_from_text(text: str) -> str:
    supportive = ("LOWER YIELD", "DOLLAR FALL", "DXY DOWN", "DOVISH", "RATE CUT", "INFLATION COOL")
    pressure = ("HIGHER YIELD", "DOLLAR RISE", "DXY UP", "HAWKISH", "RATE HIKE", "INFLATION HOT")
    if any(token in text for token in supportive):
        return "GOLD_SUPPORTIVE"
    if any(token in text for token in pressure):
        return "GOLD_PRESSURE"
    return "GOLD_NEUTRAL"


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
