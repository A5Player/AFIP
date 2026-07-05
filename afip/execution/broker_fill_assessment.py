"""Broker fill assessment for financial order settlement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class BrokerFillAssessmentResult:
    """Broker execution fill quality and settlement eligibility."""

    status: str
    accepted: bool
    filled_quantity: float
    fill_price: float
    slippage_points: float
    failed_rules: tuple[str, ...]
    reason: str


class BrokerFillAssessment:
    """Validate broker fill data before position accounting."""

    def evaluate(
        self,
        lifecycle_record: Mapping[str, object] | object | None = None,
        broker_response: Mapping[str, object] | None = None,
        limits: Mapping[str, object] | None = None,
    ) -> BrokerFillAssessmentResult:
        record = self._mapping(lifecycle_record)
        response = dict(broker_response or {})
        policy = dict(limits or {})
        failed: list[str] = []

        if not bool(record.get("approved", False)):
            failed.append("order_lifecycle_not_approved")

        broker_status = str(response.get("status", "REJECTED")).upper()
        if broker_status not in {"FILLED", "PARTIAL_FILLED"}:
            failed.append("broker_fill_not_confirmed")

        requested_quantity = self._number(record.get("requested_quantity", 0.0))
        filled_quantity = self._number(response.get("filled_quantity", 0.0))
        if filled_quantity <= 0.0:
            failed.append("filled_quantity_missing")
        minimum_fill_ratio = self._ratio(policy.get("minimum_fill_ratio", 1.0))
        fill_ratio = filled_quantity / requested_quantity if requested_quantity > 0 else 0.0
        if requested_quantity > 0 and fill_ratio + 1e-12 < minimum_fill_ratio:
            failed.append("fill_ratio_below_limit")

        requested_price = self._number(record.get("requested_price", 0.0))
        fill_price = self._number(response.get("fill_price", response.get("price", 0.0)))
        point_value = self._number(policy.get("point_value", 0.01)) or 0.01
        slippage_points = abs(fill_price - requested_price) / point_value if requested_price > 0 and fill_price > 0 else 0.0
        maximum_slippage_points = self._number(policy.get("maximum_slippage_points", 30.0))
        if slippage_points > maximum_slippage_points:
            failed.append("slippage_limit_exceeded")

        accepted = not failed
        status = "BROKER_FILL_ACCEPTED" if accepted else "BROKER_FILL_REVIEW"
        reason = "broker_fill_accepted_for_settlement" if accepted else ";".join(failed)
        return BrokerFillAssessmentResult(
            status=status,
            accepted=accepted,
            filled_quantity=filled_quantity,
            fill_price=fill_price,
            slippage_points=round(slippage_points, 5),
            failed_rules=tuple(failed),
            reason=reason,
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "approved": getattr(value, "approved", False),
            "requested_quantity": getattr(value, "requested_quantity", 0.0),
            "requested_price": getattr(value, "requested_price", 0.0),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _ratio(value: object) -> float:
        number = BrokerFillAssessment._number(value)
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))
