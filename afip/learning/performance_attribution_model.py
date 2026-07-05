"""Production Milestone B Pack 8 - performance attribution model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .execution_feedback_record import ExecutionFeedbackRecord


@dataclass(frozen=True)
class PerformanceAttributionResult:
    status: str
    contribution_score: float
    average_net_result: float
    win_rate: float
    cost_ratio: float
    reason: str


class PerformanceAttributionModel:
    """Evaluate execution feedback into a stable performance attribution result."""

    def evaluate(self, records: Iterable[ExecutionFeedbackRecord | Mapping[str, object]]) -> PerformanceAttributionResult:
        normalized = [
            item if isinstance(item, ExecutionFeedbackRecord) else ExecutionFeedbackRecord.from_mapping(item)
            for item in records
        ]
        if not normalized:
            return PerformanceAttributionResult(
                status="ATTRIBUTION_EMPTY",
                contribution_score=0.0,
                average_net_result=0.0,
                win_rate=0.0,
                cost_ratio=0.0,
                reason="no_execution_feedback",
            )

        total_net = sum(item.net_execution_result for item in normalized)
        total_cost = sum(item.spread_cost + item.slippage_cost for item in normalized)
        total_abs_profit = sum(abs(item.realized_profit) for item in normalized) or 1.0
        win_rate = sum(1 for item in normalized if item.is_profitable) / len(normalized)
        average_net = total_net / len(normalized)
        cost_ratio = min(1.0, total_cost / total_abs_profit)
        profit_component = min(1.0, max(0.0, (average_net + 10.0) / 20.0))
        contribution_score = round((profit_component * 0.55 + win_rate * 0.35 + (1.0 - cost_ratio) * 0.10) * 100.0, 2)
        status = "ATTRIBUTION_POSITIVE" if contribution_score >= 60.0 else "ATTRIBUTION_REVIEW"
        reason = "positive_execution_attribution" if status == "ATTRIBUTION_POSITIVE" else "execution_attribution_review"
        return PerformanceAttributionResult(status, contribution_score, round(average_net, 4), round(win_rate, 4), round(cost_ratio, 4), reason)
