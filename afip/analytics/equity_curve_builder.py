class EquityCurveBuilder:
    def build(self, starting_equity: float, trades: list) -> list:
        curve = [starting_equity]
        equity = starting_equity

        for trade in trades:
            equity += float(trade.get("profit", 0))
            curve.append(round(equity, 2))

        return curve
