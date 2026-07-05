"""Position mark-to-market valuation for production accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PositionValuationSnapshot:
    """Mark-to-market valuation snapshot for one position ledger."""

    status: str
    account_id: str
    symbol: str
    side: str
    net_quantity: float
    average_price: float
    market_price: float
    market_value: float
    cost_basis: float
    reason: str


class PositionValuation:
    """Build a deterministic mark-to-market valuation from a position ledger."""

    def value(
        self,
        ledger_snapshot: Mapping[str, object] | object | None,
        market_snapshot: Mapping[str, object] | None = None,
    ) -> PositionValuationSnapshot:
        ledger = self._mapping(ledger_snapshot)
        if ledger.get("status") != "POSITION_LEDGER_READY":
            return self._review("position_ledger_not_ready", ledger)

        market_price = self._resolve_market_price(market_snapshot)
        if market_price <= 0:
            return self._review("market_price_not_available", ledger)

        net_quantity = self._number(ledger.get("net_quantity", 0.0))
        average_price = self._number(ledger.get("average_price", 0.0))
        market_value = round(net_quantity * market_price, 8)
        cost_basis = round(net_quantity * average_price, 8)
        return PositionValuationSnapshot(
            status="POSITION_VALUATION_READY",
            account_id=str(ledger.get("account_id", "ACCOUNT_UNSPECIFIED")),
            symbol=str(ledger.get("symbol", "SYMBOL_UNSPECIFIED")),
            side=str(ledger.get("side", "FLAT")),
            net_quantity=round(net_quantity, 8),
            average_price=round(average_price, 8),
            market_price=round(market_price, 8),
            market_value=market_value,
            cost_basis=cost_basis,
            reason="position_mark_to_market_ready",
        )

    def _review(self, reason: str, ledger: Mapping[str, object]) -> PositionValuationSnapshot:
        return PositionValuationSnapshot(
            status="POSITION_VALUATION_REVIEW",
            account_id=str(ledger.get("account_id", "ACCOUNT_UNSPECIFIED")),
            symbol=str(ledger.get("symbol", "SYMBOL_UNSPECIFIED")),
            side=str(ledger.get("side", "FLAT")),
            net_quantity=self._number(ledger.get("net_quantity", 0.0)),
            average_price=self._number(ledger.get("average_price", 0.0)),
            market_price=0.0,
            market_value=0.0,
            cost_basis=0.0,
            reason=reason,
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
            "net_quantity": getattr(value, "net_quantity", 0.0),
            "average_price": getattr(value, "average_price", 0.0),
        }

    @classmethod
    def _resolve_market_price(cls, market_snapshot: Mapping[str, object] | None) -> float:
        if not market_snapshot:
            return 0.0
        for key in ("market_price", "mid_price", "last_price", "bid", "ask"):
            price = cls._number(market_snapshot.get(key))
            if price > 0:
                return price
        return 0.0

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
