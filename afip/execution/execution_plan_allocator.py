from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.execution.execution_readiness_assessment import ExecutionReadinessAssessment
from afip.execution.execution_strategy_selection import ExecutionStrategySelection
from afip.execution.execution_timing_model import ExecutionTimingModel
from afip.execution.order_size_allocator import OrderSizeAllocator


@dataclass(frozen=True)
class ExecutionPlanResult:
    status: str
    action: str
    readiness: str
    strategy: str
    timing: str
    lot_size: float
    exposure_ratio: float
    confidence: float
    reason: str


class ExecutionPlanAllocator:
    """Create a production execution plan from decision, context, risk, and account profiles."""

    def create(
        self,
        decision_profile: Mapping[str, object] | None = None,
        context_profile: Mapping[str, object] | None = None,
        risk_profile: Mapping[str, object] | None = None,
        account_profile: Mapping[str, object] | None = None,
    ) -> ExecutionPlanResult:
        decision = dict(decision_profile or {})
        context = dict(context_profile or {})
        risk = dict(risk_profile or {})
        account = dict(account_profile or {})

        action = str(decision.get("action", "WAIT")).upper()
        confidence = self._ratio(decision.get("confidence", 0.0))
        market_state = str(context.get("market_state", context.get("state", "TRENDING"))).upper()
        volatility_state = str(context.get("volatility_state", context.get("volatility", "NORMAL"))).upper()
        liquidity_state = str(context.get("liquidity_state", context.get("liquidity", "EXPANDING"))).upper()
        spread_points = float(context.get("spread_points", 25.0) or 0.0)
        spread_limit = float(context.get("spread_limit", 35.0) or 35.0)

        strategy = ExecutionStrategySelection().select(action, market_state, volatility_state, liquidity_state)
        timing = ExecutionTimingModel().evaluate(spread_points, spread_limit, volatility_state, liquidity_state, confidence)
        risk_status = str(risk.get("risk_status", risk.get("status", "ACCEPTED"))).upper()
        readiness = ExecutionReadinessAssessment().assess(action, confidence, risk_status, timing.timing, strategy.strategy)
        size = OrderSizeAllocator().allocate(
            equity=float(account.get("equity", 100.0) or 100.0),
            risk_budget=float(risk.get("risk_budget", risk.get("budget", 0.01)) or 0.01),
            confidence=confidence,
            volatility_state=volatility_state,
            maximum_lot=float(account.get("maximum_lot", 0.05) or 0.05),
            minimum_lot=float(account.get("minimum_lot", 0.01) or 0.01),
        )

        if readiness.readiness == "NOT_READY":
            lot_size = 0.0
            exposure_ratio = 0.0
            status = "EXECUTION_PLAN_REVIEW"
        else:
            lot_size = size.lot_size
            exposure_ratio = size.exposure_ratio
            status = "EXECUTION_PLAN_READY" if readiness.readiness == "READY" else "EXECUTION_PLAN_SELECTIVE"

        return ExecutionPlanResult(
            status=status,
            action=action,
            readiness=readiness.readiness,
            strategy=strategy.strategy,
            timing=timing.timing,
            lot_size=lot_size,
            exposure_ratio=exposure_ratio,
            confidence=confidence,
            reason=readiness.reason,
        )

    @staticmethod
    def _ratio(value: object) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))
