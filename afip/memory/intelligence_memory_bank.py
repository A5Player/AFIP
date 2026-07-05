"""Production Milestone B Pack 9 - intelligence memory bank."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .confidence_memory_tracker import ConfidenceMemoryTracker
from .execution_memory_snapshot import ExecutionMemorySnapshot
from .market_memory_profile import MarketMemoryProfile
from .signal_history_repository import SignalHistoryRepository


@dataclass(frozen=True)
class IntelligenceMemoryBankResult:
    status: str
    memory_score: float
    signal_status: str
    market_status: str
    confidence_status: str
    execution_status: str
    reason: str


class IntelligenceMemoryBank:
    """Aggregate signal, market, confidence, and execution memory into one result."""

    def build(
        self,
        signals: Iterable[Mapping[str, Any]],
        market_profile: Mapping[str, Any] | None,
        confidence_values: Iterable[Any],
        executions: Iterable[Mapping[str, Any]],
    ) -> IntelligenceMemoryBankResult:
        signal_result = SignalHistoryRepository().build(signals)
        market_result = MarketMemoryProfile().evaluate(market_profile)
        confidence_result = ConfidenceMemoryTracker().evaluate(confidence_values)
        execution_result = ExecutionMemorySnapshot().evaluate(executions)

        memory_score = round(
            signal_result.average_confidence * 0.25
            + market_result.profile_score * 0.25
            + confidence_result.stability_score * 0.25
            + execution_result.execution_score * 0.25,
            2,
        )
        ready_count = sum(
            1
            for status in (
                signal_result.status,
                market_result.status,
                confidence_result.status,
                execution_result.status,
            )
            if status.endswith("READY")
        )
        status = "INTELLIGENCE_MEMORY_READY" if ready_count >= 3 and memory_score >= 60.0 else "INTELLIGENCE_MEMORY_REVIEW"
        reason = "intelligence_memory_available" if status == "INTELLIGENCE_MEMORY_READY" else "intelligence_memory_review"
        return IntelligenceMemoryBankResult(
            status,
            memory_score,
            signal_result.status,
            market_result.status,
            confidence_result.status,
            execution_result.status,
            reason,
        )
