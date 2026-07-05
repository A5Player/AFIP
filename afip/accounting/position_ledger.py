"""Position ledger aggregation for production accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class PositionLedgerSnapshot:
    """Aggregated position ledger snapshot for one account and symbol."""

    status: str
    account_id: str
    symbol: str
    net_quantity: float
    side: str
    average_price: float
    gross_notional_value: float
    entry_count: int
    reason: str


class PositionLedger:
    """Aggregate position accounting entries into a ledger snapshot."""

    def summarize(self, entries: Iterable[Mapping[str, object] | object]) -> PositionLedgerSnapshot:
        normalized = [self._mapping(entry) for entry in entries]
        ready_entries = [entry for entry in normalized if entry.get("accounting_state") == "POSITION_ACCOUNTING_READY"]
        if not ready_entries:
            return PositionLedgerSnapshot(
                status="POSITION_LEDGER_EMPTY",
                account_id="ACCOUNT_UNSPECIFIED",
                symbol="SYMBOL_UNSPECIFIED",
                net_quantity=0.0,
                side="FLAT",
                average_price=0.0,
                gross_notional_value=0.0,
                entry_count=0,
                reason="no_ready_position_accounting_entries",
            )

        account_id = str(ready_entries[0].get("account_id", "ACCOUNT_UNSPECIFIED"))
        symbol = str(ready_entries[0].get("symbol", "SYMBOL_UNSPECIFIED"))
        net_quantity = round(sum(self._number(entry.get("quantity", 0.0)) for entry in ready_entries), 8)
        gross_notional = round(sum(abs(self._number(entry.get("notional_value", 0.0))) for entry in ready_entries), 8)
        gross_quantity = sum(abs(self._number(entry.get("quantity", 0.0))) for entry in ready_entries)
        weighted_price = 0.0
        if gross_quantity > 0:
            weighted_price = sum(
                abs(self._number(entry.get("quantity", 0.0))) * self._number(entry.get("average_price", 0.0))
                for entry in ready_entries
            ) / gross_quantity
        side = "LONG" if net_quantity > 0 else "SHORT" if net_quantity < 0 else "FLAT"
        return PositionLedgerSnapshot(
            status="POSITION_LEDGER_READY",
            account_id=account_id,
            symbol=symbol,
            net_quantity=net_quantity,
            side=side,
            average_price=round(weighted_price, 8),
            gross_notional_value=gross_notional,
            entry_count=len(ready_entries),
            reason="position_ledger_snapshot_ready",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object) -> dict[str, object]:
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "accounting_state": getattr(value, "accounting_state", ""),
            "account_id": getattr(value, "account_id", ""),
            "symbol": getattr(value, "symbol", ""),
            "quantity": getattr(value, "quantity", 0.0),
            "average_price": getattr(value, "average_price", 0.0),
            "notional_value": getattr(value, "notional_value", 0.0),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
