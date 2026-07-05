from __future__ import annotations

from dataclasses import dataclass

from afip.execution.execution_plan_allocator import ExecutionPlanAllocator


@dataclass(frozen=True)
class ProductionMilestoneBExecutionRuntimeResult:
    status: str
    action: str
    readiness: str
    strategy: str
    timing: str
    lot_size: float
    reason: str


class ProductionMilestoneBExecutionRuntime:
    """Runtime integration for Milestone B execution allocation."""

    def run(self) -> ProductionMilestoneBExecutionRuntimeResult:
        plan = ExecutionPlanAllocator().create(
            decision_profile={"action": "BUY", "confidence": 0.88, "risk_status": "ACCEPTED"},
            context_profile={
                "market_state": "TRENDING",
                "volatility_state": "NORMAL",
                "liquidity_state": "EXPANDING",
                "spread_points": 22.0,
                "spread_limit": 35.0,
            },
            risk_profile={"risk_status": "ACCEPTED", "risk_budget": 0.01},
            account_profile={"equity": 100.0, "maximum_lot": 0.05, "minimum_lot": 0.01},
        )
        return ProductionMilestoneBExecutionRuntimeResult(
            status="MILESTONE_B_EXECUTION_RUNTIME_READY",
            action=plan.action,
            readiness=plan.readiness,
            strategy=plan.strategy,
            timing=plan.timing,
            lot_size=plan.lot_size,
            reason=plan.reason,
        )
