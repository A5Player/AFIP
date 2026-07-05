from afip.report.analytics_report import AnalyticsReport
from afip.analytics.drawdown_calculator import DrawdownCalculator

def test_analytics_report_ready():
    trades = [
        {"symbol": "XAUUSD", "action": "BUY", "profit": 10},
        {"symbol": "XAUUSD", "action": "SELL", "profit": -5},
        {"symbol": "XAUUSD", "action": "BUY", "profit": 15},
    ]
    report = AnalyticsReport().generate(trades, starting_equity=1000)
    assert report["status"] == "REPORT_READY"
    assert report["summary"]["total_trades"] == 3
    assert report["summary"]["net_profit"] == 20
    assert len(report["equity_curve"]) == 4

def test_drawdown_calculator():
    result = DrawdownCalculator().calculate([1000, 1020, 990, 1030])
    assert result["max_drawdown"] == 30
