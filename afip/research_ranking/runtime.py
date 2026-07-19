"""Multi-dimensional research ranking with non-compensating drawdown limits."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class RankingPolicy:
    maximum_drawdown_percentage: float = 20.0
    minimum_trade_count: int = 30
    minimum_expectancy: float = 0.0
    minimum_profit_factor: float = 1.0
    minimum_out_of_sample_windows: int = 1
    drawdown_weight: float = 0.30
    expectancy_weight: float = 0.20
    profit_factor_weight: float = 0.20
    recovery_weight: float = 0.15
    stability_weight: float = 0.15

def _number(row: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    return float(row.get(key, default))

class ResearchRankingEngine:
    def __init__(self, policy: RankingPolicy | None = None) -> None:
        self.policy = policy or RankingPolicy()

    def classify(self, row: Mapping[str, Any]) -> str:
        if _number(row, "trade_count") < self.policy.minimum_trade_count:
            return "INSUFFICIENT_EVIDENCE"
        if _number(row, "out_of_sample_windows") < self.policy.minimum_out_of_sample_windows:
            return "INSUFFICIENT_EVIDENCE"
        if _number(row, "maximum_drawdown_percentage") > self.policy.maximum_drawdown_percentage:
            return "QUARANTINED"
        if _number(row, "expectancy") <= self.policy.minimum_expectancy:
            return "REJECTED"
        if _number(row, "profit_factor") < self.policy.minimum_profit_factor:
            return "REJECTED"
        return "CERTIFIED_CANDIDATE"

    def score(self, row: Mapping[str, Any]) -> float:
        status = self.classify(row)
        if status != "CERTIFIED_CANDIDATE":
            return -1.0
        drawdown = _number(row, "maximum_drawdown_percentage")
        drawdown_score = max(0.0, 1.0 - drawdown / self.policy.maximum_drawdown_percentage)
        expectancy_score = min(1.0, max(0.0, _number(row, "expectancy") / 10.0))
        profit_factor_score = min(1.0, max(0.0, (_number(row, "profit_factor") - 1.0) / 2.0))
        recovery_score = min(1.0, max(0.0, _number(row, "recovery_factor") / 5.0))
        stability_score = min(1.0, max(0.0, _number(row, "stability_score") / 100.0))
        value = (
            drawdown_score * self.policy.drawdown_weight
            + expectancy_score * self.policy.expectancy_weight
            + profit_factor_score * self.policy.profit_factor_weight
            + recovery_score * self.policy.recovery_weight
            + stability_score * self.policy.stability_weight
        )
        return round(value * 100.0, 8)

    def rank(self, rows: Iterable[Mapping[str, Any]], limit: int = 100) -> dict[str, Any]:
        evaluated = []
        for row in rows:
            item = dict(row)
            item["evidence_status"] = self.classify(item)
            item["ranking_score"] = self.score(item)
            evaluated.append(item)
        certified = sorted(
            (item for item in evaluated if item["evidence_status"] == "CERTIFIED_CANDIDATE"),
            key=lambda item: (-item["ranking_score"], item.get("research_id", "")),
        )
        rejected = sorted(
            (item for item in evaluated if item["evidence_status"] != "CERTIFIED_CANDIDATE"),
            key=lambda item: (item["ranking_score"], -_number(item, "maximum_drawdown_percentage")),
        )
        return {
            "schema_version": "1.0",
            "top_overall": certified[:limit],
            "top_low_drawdown": sorted(certified, key=lambda item: (_number(item, "maximum_drawdown_percentage"), -item["ranking_score"]))[:limit],
            "top_capital_preservation": sorted(certified, key=lambda item: (-_number(item, "recovery_factor"), _number(item, "maximum_drawdown_percentage")))[:limit],
            "bottom_and_quarantined": rejected[:limit],
            "evaluated_count": len(evaluated),
        }
