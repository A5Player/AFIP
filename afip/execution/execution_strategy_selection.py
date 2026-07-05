from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionStrategyResult:
    status: str
    strategy: str
    participation: str
    reason: str


class ExecutionStrategySelection:
    """Select execution strategy from decision action and market context."""

    def select(
        self,
        action: str = "WAIT",
        market_state: str = "TRENDING",
        volatility_state: str = "NORMAL",
        liquidity_state: str = "EXPANDING",
    ) -> ExecutionStrategyResult:
        normalized_action = str(action or "WAIT").upper()
        state = str(market_state or "UNKNOWN").upper()
        volatility = str(volatility_state or "NORMAL").upper()
        liquidity = str(liquidity_state or "NORMAL").upper()

        if normalized_action not in {"BUY", "SELL", "REDUCE"}:
            return ExecutionStrategyResult(
                status="EXECUTION_STRATEGY_REVIEW",
                strategy="NO_EXECUTION",
                participation="NONE",
                reason="decision_not_actionable",
            )
        if normalized_action == "REDUCE" or volatility in {"HIGH", "EXPANDING"}:
            return ExecutionStrategyResult(
                status="EXECUTION_STRATEGY_READY",
                strategy="LIMITED_RISK_ENTRY",
                participation="REDUCED",
                reason="volatility_adjusted_execution",
            )
        if state in {"BREAKOUT", "TRENDING"} and liquidity in {"EXPANDING", "NORMAL"}:
            return ExecutionStrategyResult(
                status="EXECUTION_STRATEGY_READY",
                strategy="BREAKOUT_CONTINUATION",
                participation="FULL",
                reason="directional_market_participation",
            )
        if state in {"SIDEWAYS", "PULLBACK"}:
            return ExecutionStrategyResult(
                status="EXECUTION_STRATEGY_READY",
                strategy="LIQUIDITY_CONFIRMATION",
                participation="SELECTIVE",
                reason="liquidity_confirmed_execution",
            )
        return ExecutionStrategyResult(
            status="EXECUTION_STRATEGY_SELECTIVE",
            strategy="MEASURED_PARTICIPATION",
            participation="SELECTIVE",
            reason="balanced_market_participation",
        )
