"""Capital reserve model for production portfolio allocation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CapitalReserveResult:
    """Capital held back before allocation to positions."""

    status: str
    total_equity: float
    reserve_amount: float
    available_capital: float
    reserve_ratio: float
    minimum_reserve_ratio: float
    ready: bool
    reason: str


class CapitalReserve:
    """Calculate reserved capital and capital available for allocation."""

    def calculate(
        self,
        portfolio_equity: Mapping[str, object] | object,
        policy: Mapping[str, object] | None = None,
    ) -> CapitalReserveResult:
        policy = policy or {}
        status = self._text(portfolio_equity, "status")
        equity = self._number(portfolio_equity, "total_equity", self._number(portfolio_equity, "equity"))
        minimum_reserve_ratio = self._number(policy, "minimum_reserve_ratio", 0.20)
        if status not in {"PORTFOLIO_EQUITY_READY", "EQUITY_READY"}:
            return CapitalReserveResult("CAPITAL_RESERVE_REVIEW", equity, 0.0, 0.0, 0.0, minimum_reserve_ratio, False, "portfolio_equity_not_ready")
        if equity <= 0:
            return CapitalReserveResult("CAPITAL_RESERVE_REVIEW", equity, 0.0, 0.0, 0.0, minimum_reserve_ratio, False, "equity_not_positive")
        reserve_amount = round(equity * minimum_reserve_ratio, 8)
        available_capital = round(equity - reserve_amount, 8)
        return CapitalReserveResult(
            status="CAPITAL_RESERVE_READY",
            total_equity=round(equity, 8),
            reserve_amount=reserve_amount,
            available_capital=available_capital,
            reserve_ratio=round(reserve_amount / equity, 8),
            minimum_reserve_ratio=minimum_reserve_ratio,
            ready=True,
            reason="capital_reserve_ready",
        )

    @staticmethod
    def _number(value: Mapping[str, object] | object, key: str, default: float = 0.0) -> float:
        raw = value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _text(value: Mapping[str, object] | object, key: str) -> str:
        raw = value.get(key, "") if isinstance(value, Mapping) else getattr(value, key, "")
        return str(raw)
