"""Quality assessment for trading pattern research records."""

from __future__ import annotations

from dataclasses import dataclass

from afip.trading_patterns.trade_pattern_repository import TradePatternSummary


@dataclass(frozen=True)
class TradePatternQualityResult:
    """Quality decision for a compact trading pattern."""

    status: str
    quality_score: float
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "quality_score": self.quality_score, "reasons": list(self.reasons)}


class TradePatternQuality:
    """Assess whether a pattern has enough stable evidence for research use."""

    def __init__(
        self,
        minimum_observations: int = 5,
        minimum_profit_factor: float = 1.05,
        maximum_average_cost_points: float = 45.0,
    ) -> None:
        self.minimum_observations = int(minimum_observations)
        self.minimum_profit_factor = float(minimum_profit_factor)
        self.maximum_average_cost_points = float(maximum_average_cost_points)

    def assess(self, summary: TradePatternSummary) -> TradePatternQualityResult:
        stats = summary.statistics
        reasons: list[str] = []
        if stats.observations < self.minimum_observations:
            reasons.append("insufficient_pattern_observations")
        if stats.profit_factor < self.minimum_profit_factor:
            reasons.append("profit_factor_below_research_threshold")
        if stats.average_execution_cost_points > self.maximum_average_cost_points:
            reasons.append("execution_cost_above_research_threshold")
        score = 100.0
        score -= max(0, self.minimum_observations - stats.observations) * 10.0
        score -= max(0.0, self.minimum_profit_factor - stats.profit_factor) * 30.0
        score -= max(0.0, stats.average_execution_cost_points - self.maximum_average_cost_points)
        score = round(max(0.0, min(100.0, score)), 2)
        if reasons:
            return TradePatternQualityResult("PATTERN_OBSERVE_ONLY", score, tuple(reasons))
        return TradePatternQualityResult("PATTERN_RESEARCH_READY", score, ("pattern_quality_ready",))
