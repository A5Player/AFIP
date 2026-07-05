class DrawdownCalculator:
    def calculate(self, equity_curve: list[float]) -> dict:
        if not equity_curve:
            return {"max_drawdown": 0.0, "max_drawdown_pct": 0.0}

        peak = equity_curve[0]
        max_dd = 0.0
        max_dd_pct = 0.0

        for equity in equity_curve:
            peak = max(peak, equity)
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak * 100) if peak else 0.0
            max_dd = max(max_dd, drawdown)
            max_dd_pct = max(max_dd_pct, drawdown_pct)

        return {
            "max_drawdown": round(max_dd, 2),
            "max_drawdown_pct": round(max_dd_pct, 2),
        }
