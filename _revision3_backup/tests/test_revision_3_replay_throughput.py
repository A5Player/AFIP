import json
from pathlib import Path

import pytest

from afip.automatic_research_runtime import AutomaticResearchRuntime


def _write_bars(root: Path, count: int = 12) -> None:
    path = root / "data" / "research" / "revision_3_bars.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(count):
        rows.append({
            "timestamp_utc": f"2026-01-01T{index:02d}:00:00Z",
            "timeframe": "H1",
            "open": 100 + index,
            "high": 102 + index,
            "low": 99 + index,
            "close": 101 + index,
            "volume": 10 + index,
        })
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_revision_3_replay_writes_performance_evidence(tmp_path):
    _write_bars(tmp_path)
    summary = AutomaticResearchRuntime(tmp_path).run(
        collect_mt5_when_needed=False,
        maximum_replay_bars=12,
        progress_interval_bars=5,
    )
    assert summary.replay_bars_processed == 12
    evidence_path = tmp_path / "runtime" / "research" / "replay_performance.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["bars_processed"] == 12
    assert evidence["dashboard_updates"] <= 4
    assert evidence["observatory_updates"] <= 4
    assert evidence["order_send_called"] is False


def test_revision_3_rejects_invalid_progress_interval(tmp_path):
    with pytest.raises(ValueError, match="progress_interval_bars"):
        AutomaticResearchRuntime(tmp_path).run(
            collect_mt5_when_needed=False,
            progress_interval_bars=0,
        )


def test_revision_3_source_uses_grouped_timeframes_and_adaptive_progress():
    source = Path("afip/automatic_research_runtime/runtime.py").read_text(encoding="utf-8")
    assert "bars_by_timeframe" in source
    assert "adaptive_progress_interval" in source
    assert "progress_interval_bars=adaptive_progress_interval" in source
    assert "replay_performance.json" in source
