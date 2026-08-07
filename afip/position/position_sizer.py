from math import floor


class PositionSizer:
    def __init__(self, min_lot: float = 0.01, max_lot: float = 0.03, lot_step: float = 0.01):
        self.min_lot = min_lot
        self.max_lot = max_lot
        self.lot_step = lot_step

    def calculate(
        self,
        balance: float,
        risk_usd: float | None = None,
        stop_loss_points: float | None = None,
    ) -> dict:
        """Size only from explicitly approved risk and stop inputs.

        The position sizer is not an authority for risk or stop loss.  Missing
        inputs must be rejected rather than silently inheriting legacy fixed
        simulation defaults.
        """
        if risk_usd is None or stop_loss_points is None:
            raise ValueError("approved risk_usd and stop_loss_points are required")

        risk = float(risk_usd)
        stop = float(stop_loss_points)
        if risk <= 0:
            raise ValueError("risk_usd must be positive")
        if stop <= 0:
            raise ValueError("stop_loss_points must be positive")

        raw_lot = risk / stop
        if self.lot_step <= 0 or self.min_lot <= 0 or self.max_lot < self.min_lot:
            raise ValueError("invalid lot bounds")
        bounded = min(self.max_lot, raw_lot)
        lot = floor((bounded + 1e-12) / self.lot_step) * self.lot_step
        lot = round(lot, 8)
        eligible = lot + 1e-12 >= self.min_lot
        if not eligible:
            lot = 0.0
        return {
            "lot": lot,
            "eligible": eligible,
            "reason": "approved_risk_stop_sizing" if eligible else "minimum_lot_exceeds_approved_risk_budget",
            "raw_risk_lot": round(raw_lot, 8),
            "risk_usd": risk,
            "stop_loss_points": stop,
            "balance": balance,
            "method": "approved_risk_stop_sizing",
        }
