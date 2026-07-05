"""Order settlement model for production financial accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class OrderSettlementResult:
    """Settlement result prepared for downstream position accounting."""

    status: str
    settled: bool
    settlement_id: str
    position_quantity: float
    average_price: float
    notional_value: float
    reason: str


class OrderSettlement:
    """Create settlement output after accepted broker fill assessment."""

    def settle(
        self,
        lifecycle_record: Mapping[str, object] | object | None = None,
        fill_assessment: Mapping[str, object] | object | None = None,
        sequence: int = 1,
    ) -> OrderSettlementResult:
        record = self._mapping(lifecycle_record)
        fill = self._mapping(fill_assessment)
        accepted = bool(fill.get("accepted", False))
        quantity = self._number(fill.get("filled_quantity", 0.0))
        price = self._number(fill.get("fill_price", 0.0))
        order_id = str(record.get("order_id", f"AFIP-LIFECYCLE-{int(sequence):06d}"))
        action = str(record.get("action", "WAIT")).upper()
        signed_quantity = -quantity if action == "SELL" else quantity

        if not accepted:
            return OrderSettlementResult(
                status="ORDER_SETTLEMENT_REVIEW",
                settled=False,
                settlement_id=f"AFIP-SETTLEMENT-{int(sequence):06d}-REVIEW",
                position_quantity=0.0,
                average_price=0.0,
                notional_value=0.0,
                reason=str(fill.get("reason", "broker_fill_not_accepted")),
            )

        return OrderSettlementResult(
            status="ORDER_SETTLEMENT_READY",
            settled=True,
            settlement_id=f"AFIP-SETTLEMENT-{int(sequence):06d}-{order_id[-12:]}",
            position_quantity=round(signed_quantity, 8),
            average_price=price,
            notional_value=round(abs(quantity * price), 8),
            reason="order_settled_for_position_accounting",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "accepted": getattr(value, "accepted", False),
            "filled_quantity": getattr(value, "filled_quantity", 0.0),
            "fill_price": getattr(value, "fill_price", 0.0),
            "reason": getattr(value, "reason", "settlement_input"),
            "order_id": getattr(value, "order_id", ""),
            "action": getattr(value, "action", "WAIT"),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
