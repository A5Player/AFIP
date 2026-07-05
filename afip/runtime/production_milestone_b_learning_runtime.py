"""Production Milestone B Pack 8 - adaptive learning runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any

from afip.learning.adaptive_learning_loop import AdaptiveLearningLoop


@dataclass(frozen=True)
class ProductionMilestoneBLearningRuntimeResult:
    status: str
    learning_score: float
    updated_weights: dict[str, float]
    records_processed: int
    execution_mode: str
    reason: str


class ProductionMilestoneBLearningRuntime:
    """Runtime adapter for adaptive learning without changing legacy execution."""

    def __init__(self) -> None:
        self._loop = AdaptiveLearningLoop()

    def run(
        self,
        feedback_records: Iterable[Mapping[str, Any]],
        current_weights: Mapping[str, float] | None = None,
    ) -> ProductionMilestoneBLearningRuntimeResult:
        result = self._loop.process(feedback_records, current_weights)
        runtime_status = "LEARNING_RUNTIME_READY" if result.status == "LEARNING_LOOP_READY" else "LEARNING_RUNTIME_REVIEW"
        return ProductionMilestoneBLearningRuntimeResult(
            status=runtime_status,
            learning_score=result.learning_score,
            updated_weights=result.updated_weights,
            records_processed=result.records_processed,
            execution_mode="LOCKED_SIMULATION_ONLY",
            reason=result.reason,
        )


def run_production_milestone_b_learning_runtime() -> ProductionMilestoneBLearningRuntimeResult:
    """Run deterministic sample feedback for local validation and CI compatibility."""
    sample_feedback = [
        {"action": "BUY", "entry_confidence": 0.82, "exit_confidence": 0.88, "realized_profit": 12.0, "drawdown": 3.0, "spread_cost": 0.8, "slippage_cost": 0.2, "market_regime": "TRENDING"},
        {"action": "BUY", "entry_confidence": 0.78, "exit_confidence": 0.81, "realized_profit": 8.0, "drawdown": 2.5, "spread_cost": 0.7, "slippage_cost": 0.2, "market_regime": "TRENDING"},
    ]
    return ProductionMilestoneBLearningRuntime().run(sample_feedback)
