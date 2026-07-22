from pathlib import Path

from afip.dashboard_ui.research_operations import render_research_operations
from afip.dashboard_ui.split_runtime import _profile_rows
from afip.four_profile_operations.mt5_connection import MT5ProfileHealth


def test_mt5_health_retains_live_financial_compatibility_aliases():
    names = set(MT5ProfileHealth.__dataclass_fields__)
    assert {"margin_free", "profit", "free_margin", "floating_profit"} <= names


def test_dashboard_spread_label_remains_backward_compatible():
    rows = {
        label: value
        for _icon, label, value in _profile_rows({"spread_points": 20})
    }
    assert rows["Spread points"] == "20"


def test_dashboard_four_declares_research_only_contract(tmp_path: Path):
    html = render_research_operations(tmp_path)
    assert "execution_authority=false" in html
    assert "order_send_called=false" in html


def test_obsolete_capital_tier_presentation_is_absent():
    source = Path("afip/dashboard_ui/split_runtime.py").read_text(encoding="utf-8")
    assert "Capital / 0.01" not in source
    assert "capital_per_001" not in source
    assert "Current tier" not in source
    assert "Tier lots" not in source
    assert "Next tier / Remaining" not in source
