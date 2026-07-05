"""Production Milestone B Pack 9 - execution memory snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ExecutionMemorySnapshotResult:
    status: str
    execution_count: int
    average_net_result: float
    average_cost: float
    execution_score: float
    reason: str


class ExecutionMemorySnapshot:
    """Create a compact memory snapshot from recent execution outcomes."""

    def evaluate(self, executions: Iterable[Mapping[str, Any]]) -> ExecutionMemorySnapshotResult:
        records = [dict(item) for item in executions]
        if not records:
            return ExecutionMemorySnapshotResult("EXECUTION_MEMORY_EMPTY", 0, 0.0, 0.0, 0.0, "no_execution_memory")
        net_values = [float(item.get("net_result", item.get("realized_profit", 0.0))) - float(item.get("spread_cost", 0.0)) - float(item.get("slippage_cost", 0.0)) for item in records]
        costs = [max(0.0, float(item.get("spread_cost", 0.0)) + float(item.get("slippage_cost", 0.0))) for item in records]
        average_net = round(sum(net_values) / len(net_values), 4)
        average_cost = round(sum(costs) / len(costs), 4)
        profit_component = min(1.0, max(0.0, (average_net + 10.0) / 20.0)) * 80.0
        cost_component = max(0.0, 20.0 - average_cost)
        execution_score = round(min(100.0, profit_component + cost_component), 2)
        status = "EXECUTION_MEMORY_READY" if execution_score >= 60.0 else "EXECUTION_MEMORY_REVIEW"
        reason = "execution_memory_positive" if status == "EXECUTION_MEMORY_READY" else "execution_memory_review"
        return ExecutionMemorySnapshotResult(status, len(records), average_net, average_cost, execution_score, reason)
