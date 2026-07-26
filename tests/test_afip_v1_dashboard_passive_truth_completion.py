from pathlib import Path

from afip.live_mt5_dashboard import render as render_live_mt5
from afip.dashboard_ui.split_runtime import SplitDashboardRenderer


def _profiles():
    base = {
        "runtime_state": "RUNNING",
        "monitoring_mode": "PASSIVE",
        "financial_live": False,
        "financial_snapshot_available": True,
        "connection_evidence_fresh": True,
        "data_fresh": True,
        "evidence_kind": "LAST_VERIFIED_SNAPSHOT",
        "financial_state": "RECENT_SNAPSHOT",
        "balance": 100.0,
        "equity": 100.0,
        "bid": 4052.54,
        "ask": 4053.30,
        "source_metadata": {"mt5_health": {"fresh": True}},
    }
    rows = []
    for index in range(1, 5):
        row = dict(base)
        row.update({
            "profile_id": f"P{index}",
            "profile_name": "TEST",
            "process_alive": index <= 2,
            "mt5_process_alive": index <= 2,
            "connection_status": "CONNECTED_PASSIVE" if index <= 2 else "DISCONNECTED",
        })
        rows.append(row)
    return rows


def test_operations_summary_distinguishes_process_snapshot_and_live_financial():
    html = SplitDashboardRenderer().render_profiles_html({"profiles": _profiles()})
    assert "MT5 processes 2/4" in html
    assert "MT5 process" in html
    assert "Live financial" in html
    assert "Verified snapshot" in html
    assert "Observation current" in html
    assert "Fresh data" not in html
    assert "Financial evidence" in html
    assert "RECENT_SNAPSHOT" in html


def test_live_mt5_labels_passive_observation_and_snapshot_truth():
    html = render_live_mt5({"profiles": _profiles()})
    assert "Passive monitoring never opens or reconnects MT5" in html
    assert "Connection Evidence" in html
    assert "Financial State" in html
    assert "RECENT_SNAPSHOT" in html
    assert "Observation State" in html
    assert "DISCONNECTED" in html
