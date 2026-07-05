class PositionSizer:
    def __init__(self, min_lot: float = 0.01, max_lot: float = 0.03):
        self.min_lot = min_lot
        self.max_lot = max_lot

    def calculate(self, balance: float, risk_usd: float = 30.0, stop_loss_points: float = 3000.0) -> dict:
        if stop_loss_points <= 0:
            raise ValueError("stop_loss_points must be positive")

        raw_lot = risk_usd / stop_loss_points
        lot = max(self.min_lot, min(self.max_lot, round(raw_lot, 2)))

        return {
            "lot": lot,
            "risk_usd": risk_usd,
            "stop_loss_points": stop_loss_points,
            "balance": balance,
            "method": "fixed_risk_simulation",
        }
