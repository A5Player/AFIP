from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderSizeResult:
    status: str
    lot_size: float
    exposure_ratio: float
    risk_budget: float
    reason: str


class OrderSizeAllocator:
    """Allocate order size from risk budget, confidence, and volatility state."""

    def allocate(
        self,
        equity: float = 100.0,
        risk_budget: float = 0.01,
        confidence: float = 0.75,
        volatility_state: str = "NORMAL",
        maximum_lot: float = 0.05,
        minimum_lot: float = 0.01,
    ) -> OrderSizeResult:
        equity_value = max(float(equity or 0.0), 0.0)
        budget = self._ratio(risk_budget)
        confidence_ratio = self._ratio(confidence)
        maximum = max(float(maximum_lot or 0.0), 0.0)
        minimum = max(float(minimum_lot or 0.0), 0.0)

        volatility_factor = self._volatility_factor(volatility_state)
        raw_lot = (equity_value / 1000.0) * budget * 10.0 * confidence_ratio * volatility_factor
        lot_size = min(max(raw_lot, minimum), maximum) if maximum > 0 else 0.0
        lot_size = round(lot_size, 2)
        exposure_ratio = round(min(lot_size / maximum, 1.0), 4) if maximum > 0 else 0.0

        return OrderSizeResult(
            status="ORDER_SIZE_READY" if lot_size > 0 else "ORDER_SIZE_REVIEW",
            lot_size=lot_size,
            exposure_ratio=exposure_ratio,
            risk_budget=round(budget, 4),
            reason="confidence_adjusted_risk_budget",
        )

    @staticmethod
    def _ratio(value: float) -> float:
        number = float(value or 0.0)
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))

    @staticmethod
    def _volatility_factor(volatility_state: str) -> float:
        state = str(volatility_state or "NORMAL").upper()
        if state in {"HIGH", "EXPANDING"}:
            return 0.70
        if state in {"LOW", "CONTRACTING"}:
            return 1.10
        return 1.00
