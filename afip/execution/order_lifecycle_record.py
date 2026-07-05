"""Order lifecycle record for settlement-ready financial execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class OrderLifecycleRecord:
    """Immutable financial order lifecycle state."""

    order_id: str
    account_id: str
    symbol: str
    action: str
    requested_quantity: float
    requested_price: float
    lifecycle_state: str
    approved: bool
    reason: str


class OrderLifecycleRecordBuilder:
    """Build deterministic order lifecycle records from approved execution data."""

    def build(
        self,
        approval_result: Mapping[str, object] | object | None = None,
        execution_plan: Mapping[str, object] | None = None,
        sequence: int = 1,
    ) -> OrderLifecycleRecord:
        approval = self._mapping(approval_result)
        plan = dict(execution_plan or {})
        action = str(plan.get("action", "WAIT")).upper()
        approved = bool(approval.get("approved", False))
        lifecycle_state = "ORDER_LIFECYCLE_ACCEPTED" if approved else "ORDER_LIFECYCLE_REVIEW"
        order_id = str(approval.get("audit_id") or f"AFIP-LIFECYCLE-{int(sequence):06d}-{action}")
        return OrderLifecycleRecord(
            order_id=order_id,
            account_id=str(plan.get("account_id", "PRIMARY_ACCOUNT")),
            symbol=str(plan.get("symbol", "GOLD#")),
            action=action,
            requested_quantity=self._number(plan.get("lot_size", plan.get("quantity", 0.0))),
            requested_price=self._number(plan.get("price", plan.get("requested_price", 0.0))),
            lifecycle_state=lifecycle_state,
            approved=approved,
            reason=str(approval.get("reason", "approval_result_processed")),
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "approved": getattr(value, "approved", False),
            "audit_id": getattr(value, "audit_id", ""),
            "reason": getattr(value, "reason", "approval_result"),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
