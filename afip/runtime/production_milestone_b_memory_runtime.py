"""Production Milestone B Pack 9 - memory runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from afip.memory.intelligence_memory_bank import IntelligenceMemoryBank


@dataclass(frozen=True)
class ProductionMilestoneBMemoryRuntimeResult:
    status: str
    memory_score: float
    execution_mode: str
    reason: str


class ProductionMilestoneBMemoryRuntime:
    """Runtime adapter for the additive intelligence memory layer."""

    def __init__(self) -> None:
        self._memory_bank = IntelligenceMemoryBank()

    def run(
        self,
        signals: Iterable[Mapping[str, Any]],
        market_profile: Mapping[str, Any] | None,
        confidence_values: Iterable[Any],
        executions: Iterable[Mapping[str, Any]],
    ) -> ProductionMilestoneBMemoryRuntimeResult:
        result = self._memory_bank.build(signals, market_profile, confidence_values, executions)
        runtime_status = "MEMORY_RUNTIME_READY" if result.status == "INTELLIGENCE_MEMORY_READY" else "MEMORY_RUNTIME_REVIEW"
        return ProductionMilestoneBMemoryRuntimeResult(runtime_status, result.memory_score, "LOCKED_SIMULATION_ONLY", result.reason)


def run_production_milestone_b_memory_runtime() -> ProductionMilestoneBMemoryRuntimeResult:
    """Run a deterministic memory sample for local quality and CI compatibility."""
    signals = [
        {"signal_name": "trend", "direction": "BUY", "confidence": 0.86, "market_regime": "TRENDING"},
        {"signal_name": "liquidity", "direction": "BUY", "confidence": 0.78, "market_regime": "TRENDING"},
        {"signal_name": "execution", "direction": "BUY", "confidence": 0.82, "market_regime": "TRENDING"},
    ]
    market_profile = {"market_regime": "TRENDING", "volatility_state": "NORMAL", "liquidity_state": "EXPANDING", "confidence": 0.84}
    confidence_values = [0.78, 0.81, 0.84, 0.86]
    executions = [
        {"realized_profit": 12.0, "spread_cost": 0.8, "slippage_cost": 0.2},
        {"realized_profit": 8.0, "spread_cost": 0.7, "slippage_cost": 0.2},
    ]
    return ProductionMilestoneBMemoryRuntime().run(signals, market_profile, confidence_values, executions)
