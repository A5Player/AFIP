"""Aggregate macro news impact into confidence and trade-awareness state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .news_impact_engine import MacroNewsImpact


@dataclass(frozen=True)
class MacroNewsConfidence:
    """Aggregated confidence across macro news assessments."""

    status: str
    article_count: int
    supportive_count: int
    pressure_count: int
    neutral_count: int
    gold_bias: str
    confidence_score: float
    impact_score: float
    trade_instruction: str
    reason: str


class MacroNewsConfidenceEngine:
    """Convert individual news impacts into a single macro news state."""

    def aggregate(self, impacts: Iterable[MacroNewsImpact]) -> MacroNewsConfidence:
        items = tuple(impacts)
        if not items:
            return MacroNewsConfidence(
                status="NEWS_CONFIDENCE_EMPTY",
                article_count=0,
                supportive_count=0,
                pressure_count=0,
                neutral_count=0,
                gold_bias="NEUTRAL",
                confidence_score=0.0,
                impact_score=0.0,
                trade_instruction="NORMAL_REVIEW",
                reason="no_macro_news_available",
            )
        supportive = tuple(item for item in items if item.direction == "GOLD_SUPPORTIVE")
        pressure = tuple(item for item in items if item.direction == "GOLD_PRESSURE")
        neutral = tuple(item for item in items if item.direction == "GOLD_NEUTRAL")
        weighted_supportive = sum(item.confidence_score for item in supportive)
        weighted_pressure = sum(item.confidence_score for item in pressure)
        total_confidence = sum(item.confidence_score for item in items)
        impact_score = round(max(item.impact_score for item in items), 2)
        if weighted_supportive > weighted_pressure * 1.15:
            gold_bias = "SUPPORTIVE"
        elif weighted_pressure > weighted_supportive * 1.15:
            gold_bias = "PRESSURE"
        else:
            gold_bias = "MIXED"
        confidence = round(total_confidence / len(items), 2)
        trade_instruction = "MACRO_REVIEW" if impact_score >= 90 or gold_bias == "MIXED" else "NORMAL_REVIEW"
        return MacroNewsConfidence(
            status="NEWS_CONFIDENCE_READY",
            article_count=len(items),
            supportive_count=len(supportive),
            pressure_count=len(pressure),
            neutral_count=len(neutral),
            gold_bias=gold_bias,
            confidence_score=confidence,
            impact_score=impact_score,
            trade_instruction=trade_instruction,
            reason=f"supportive={len(supportive)};pressure={len(pressure)};neutral={len(neutral)}",
        )
