"""Position accounting entry model for settled execution records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PositionAccountingEntry:
    """Normalized accounting entry derived from a settled order."""

    entry_id: str
    account_id: str
    symbol: str
    side: str
    quantity: float
    average_price: float
    notional_value: float
    settlement_id: str
    accounting_state: str
    reason: str


class PositionAccountingEntryBuilder:
    """Build position accounting entries from settlement output."""

    def build(
        self,
        settlement_result: Mapping[str, object] | object | None = None,
        lifecycle_record: Mapping[str, object] | object | None = None,
        sequence: int = 1,
    ) -> PositionAccountingEntry:
        settlement = self._mapping(settlement_result)
        record = self._mapping(lifecycle_record)
        settled = bool(settlement.get("settled", False))
        quantity = self._number(settlement.get("position_quantity", 0.0))
        side = "LONG" if quantity > 0 else "SHORT" if quantity < 0 else "FLAT"
        settlement_id = str(settlement.get("settlement_id", f"AFIP-SETTLEMENT-{int(sequence):06d}"))
        symbol = str(record.get("symbol", "GOLD#"))
        account_id = str(record.get("account_id", "ACCOUNT_UNSPECIFIED"))

        if not settled or quantity == 0.0:
            return PositionAccountingEntry(
                entry_id=f"AFIP-POSITION-ENTRY-{int(sequence):06d}-REVIEW",
                account_id=account_id,
                symbol=symbol,
                side="FLAT",
                quantity=0.0,
                average_price=0.0,
                notional_value=0.0,
                settlement_id=settlement_id,
                accounting_state="POSITION_ACCOUNTING_REVIEW",
                reason=str(settlement.get("reason", "settlement_not_ready")),
            )

        return PositionAccountingEntry(
            entry_id=f"AFIP-POSITION-ENTRY-{int(sequence):06d}-{settlement_id[-12:]}",
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=round(quantity, 8),
            average_price=self._number(settlement.get("average_price", 0.0)),
            notional_value=round(abs(self._number(settlement.get("notional_value", 0.0))), 8),
            settlement_id=settlement_id,
            accounting_state="POSITION_ACCOUNTING_READY",
            reason="settlement_recorded_for_position_ledger",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "settled": getattr(value, "settled", False),
            "position_quantity": getattr(value, "position_quantity", 0.0),
            "average_price": getattr(value, "average_price", 0.0),
            "notional_value": getattr(value, "notional_value", 0.0),
            "settlement_id": getattr(value, "settlement_id", ""),
            "reason": getattr(value, "reason", "position_accounting_input"),
            "account_id": getattr(value, "account_id", ""),
            "symbol": getattr(value, "symbol", ""),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
