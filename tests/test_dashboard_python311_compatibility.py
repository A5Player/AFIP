import ast
from pathlib import Path


def test_split_dashboard_parses_with_python_311_grammar():
    source = (Path(__file__).parents[1] / "afip/dashboard_ui/split_runtime.py").read_text(encoding="utf-8")
    ast.parse(source, filename="split_runtime.py", feature_version=(3, 11))


def test_ranking_table_win_rate_rendering_remains_compatible():
    from afip.dashboard_ui.split_runtime import SplitDashboardRenderer

    html = SplitDashboardRenderer._ranking_table([{
        "name": "PLAN", "samples": 2, "wins": 1, "losses": 1,
        "win_rate": 50.0, "pnl": 1.0, "pnl_observed": True, "drawdown": 0.5,
    }])
    assert "50.00%" in html and "DATA_UNAVAILABLE" not in html
