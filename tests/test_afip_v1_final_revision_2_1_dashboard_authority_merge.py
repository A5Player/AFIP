from pathlib import Path

from afip.dashboard_ui.research_operations import render_research_operations
from afip.runtime_observatory import RuntimeProgressAuthority


def test_dashboard_uses_observatory_progress_and_keeps_research_only_markers(tmp_path: Path):
    RuntimeProgressAuthority(tmp_path).update(
        state="RUNNING",
        stage="HISTORICAL_REPLAY",
        activity="Replay M5 25/100",
        current_timeframe="M5",
        replay_processed=25,
        replay_total=100,
        replay_percent=25.0,
        replay_speed_bars_per_second=12.5,
        eta_seconds=6.0,
        current_replay_timestamp_utc="2026-01-01T00:25:00Z",
    )
    html = render_research_operations(tmp_path)
    assert "25.0%" in html
    assert "M5" in html
    assert "execution_authority=false" in html
    assert "order_send_called=false" in html
