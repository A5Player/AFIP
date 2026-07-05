from afip.analytics.trade_analytics import TradeAnalytics
from afip.analytics.equity_curve_builder import EquityCurveBuilder
from afip.analytics.drawdown_calculator import DrawdownCalculator
from afip.analytics.expectancy_calculator import ExpectancyCalculator

class AnalyticsReport:
    def __init__(self):
        self.trade_analytics = TradeAnalytics()
        self.equity_builder = EquityCurveBuilder()
        self.drawdown_calculator = DrawdownCalculator()
        self.expectancy_calculator = ExpectancyCalculator()

    def generate(self, trades: list, starting_equity: float = 1000.0) -> dict:
        equity_curve = self.equity_builder.build(starting_equity, trades)
        summary = self.trade_analytics.summarize(trades)
        drawdown = self.drawdown_calculator.calculate(equity_curve)
        expectancy = self.expectancy_calculator.calculate(trades)

        return {
            "status": "REPORT_READY",
            "summary": summary,
            "equity_curve": equity_curve,
            "drawdown": drawdown,
            "expectancy": expectancy,
        }
