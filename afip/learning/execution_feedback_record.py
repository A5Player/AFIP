"""Production Milestone B Pack 8 - execution feedback record.

This module provides a compact, deterministic record for closed execution
outcomes. It is additive and has no runtime side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True)
class ExecutionFeedbackRecord:
    """Normalized execution outcome used by the adaptive learning loop."""

    action: str
    entry_confidence: float
    exit_confidence: float
    realized_profit: float
    drawdown: float
    spread_cost: float
    slippage_cost: float
    market_regime: str = "NEUTRAL"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ExecutionFeedbackRecord":
        """Build a record from a mapping while preserving backward compatibility."""
        return cls(
            action=str(payload.get("action", "NO_ACTION")).upper(),
            entry_confidence=_bounded_float(payload.get("entry_confidence", 0.0)),
            exit_confidence=_bounded_float(payload.get("exit_confidence", 0.0)),
            realized_profit=float(payload.get("realized_profit", 0.0)),
            drawdown=max(0.0, float(payload.get("drawdown", 0.0))),
            spread_cost=max(0.0, float(payload.get("spread_cost", 0.0))),
            slippage_cost=max(0.0, float(payload.get("slippage_cost", 0.0))),
            market_regime=str(payload.get("market_regime", "NEUTRAL")).upper(),
        )

    @property
    def net_execution_result(self) -> float:
        """Return realized profit after transaction costs."""
        return self.realized_profit - self.spread_cost - self.slippage_cost

    @property
    def confidence_delta(self) -> float:
        """Return exit confidence minus entry confidence."""
        return round(self.exit_confidence - self.entry_confidence, 4)

    @property
    def is_profitable(self) -> bool:
        """Return True when the net execution result is positive."""
        return self.net_execution_result > 0.0


def _bounded_float(value: Any) -> float:
    numeric = float(value)
    return min(1.0, max(0.0, numeric))
