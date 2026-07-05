"""Unrealized profit and loss calculation for position valuation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class UnrealizedPnlSnapshot:
    """Unrealized PnL result derived from valuation and price movement."""

    status: str
    account_id: str
    symbol: str
    side: str
    unrealized_pnl: float
    return_ratio: float
    pnl_state: str
    reason: str


class UnrealizedPnlCalculator:
    """Calculate unrealized PnL without mutating the position ledger."""

    def calculate(self, valuation_snapshot: Mapping[str, object] | object | None) -> UnrealizedPnlSnapshot:
        valuation = self._mapping(valuation_snapshot)
        if valuation.get("status") != "POSITION_VALUATION_READY":
            return UnrealizedPnlSnapshot(
                status="UNREALIZED_PNL_REVIEW",
                account_id=str(valuation.get("account_id", "ACCOUNT_UNSPECIFIED")),
                symbol=str(valuation.get("symbol", "SYMBOL_UNSPECIFIED")),
                side=str(valuation.get("side", "FLAT")),
                unrealized_pnl=0.0,
                return_ratio=0.0,
                pnl_state="UNAVAILABLE",
                reason="position_valuation_not_ready",
            )

        market_value = self._number(valuation.get("market_value", 0.0))
        cost_basis = self._number(valuation.get("cost_basis", 0.0))
        unrealized_pnl = round(market_value - cost_basis, 8)
        base_value = abs(cost_basis)
        return_ratio = round(unrealized_pnl / base_value, 8) if base_value > 0 else 0.0
        pnl_state = "GAIN" if unrealized_pnl > 0 else "LOSS" if unrealized_pnl < 0 else "NEUTRAL"
        return UnrealizedPnlSnapshot(
            status="UNREALIZED_PNL_READY",
            account_id=str(valuation.get("account_id", "ACCOUNT_UNSPECIFIED")),
            symbol=str(valuation.get("symbol", "SYMBOL_UNSPECIFIED")),
            side=str(valuation.get("side", "FLAT")),
            unrealized_pnl=unrealized_pnl,
            return_ratio=return_ratio,
            pnl_state=pnl_state,
            reason="unrealized_pnl_calculated",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "status": getattr(value, "status", ""),
            "account_id": getattr(value, "account_id", ""),
            "symbol": getattr(value, "symbol", ""),
            "side": getattr(value, "side", ""),
            "market_value": getattr(value, "market_value", 0.0),
            "cost_basis": getattr(value, "cost_basis", 0.0),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
