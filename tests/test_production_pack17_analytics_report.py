from afip.report.analytics_report_builder import AnalyticsReportBuilder
from afip.report.runtime_status_report import RuntimeStatusReport


def payload():
    return {
        "trades": [
            {"symbol": "GOLD#", "action": "BUY", "session": "US", "weekday": "MON", "hour": 14, "profit": 10.0},
            {"symbol": "GOLD#", "action": "SELL", "session": "ASIA", "weekday": "TUE", "hour": 2, "profit": -2.0},
            {"symbol": "GOLD#", "action": "BUY", "session": "US", "weekday": "MON", "hour": 15, "profit": 6.0},
        ],
        "equity_points": [100.0, 110.0, 108.0, 118.0],
        "walk_forward_windows": [{"train_score": 72.0, "test_score": 66.0}],
        "stress_scenarios": [{"name": "normal volatility", "net_profit": 12.0, "drawdown_percent": 8.0, "recovery_factor": 1.4}],
    }


def test_analytics_report_builder_produces_production_score():
    result = AnalyticsReportBuilder().build(payload())
    assert result["status"] == "READY"
    assert result["production_score"] >= 55.0
    assert result["performance"]["total_trades"] == 3


def test_runtime_status_report_formats_lines():
    report = AnalyticsReportBuilder().build(payload())
    lines = RuntimeStatusReport().build_lines(report)
    assert lines[0] == "Runtime Analytics:"
    assert any("Production Score" in line for line in lines)
    assert any("Profit Factor" in line for line in lines)
