class PositionSizer:
    def __init__(self, min_lot: float = 0.01, max_lot: float = 0.03):
        self.min_lot = min_lot
        self.max_lot = max_lot

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
        lot = max(self.min_lot, min(self.max_lot, round(raw_lot, 2)))
        return {
            "lot": lot,
            "risk_usd": risk,
            "stop_loss_points": stop,
            "balance": balance,
            "method": "approved_risk_stop_sizing",
        }
