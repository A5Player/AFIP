import json
from pathlib import Path

from afip.automatic_research_runtime import AutomaticResearchRuntime
from afip.historical_replay_research import AppendOnlyResearchDataset


def test_stale_replay_checkpoint_starts_new_generation(tmp_path: Path) -> None:
    historical = tmp_path / "data" / "historical"
    historical.mkdir(parents=True)
    bars = [
        {"timeframe": "M1", "timestamp_utc": "2026-01-01T00:00:00Z", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "tick_volume": 10},
        {"timeframe": "M1", "timestamp_utc": "2026-01-01T00:01:00Z", "open": 1.5, "high": 2.5, "low": 1, "close": 2, "tick_volume": 11},
    ]
    (historical / "bars.json").write_text(json.dumps(bars), encoding="utf-8")

    dataset = AppendOnlyResearchDataset(tmp_path / "runtime" / "research" / "automatic" / "schema_v2")
    for replay_index in range(3):
        dataset.append("timeline", {
            "replay_id": "AUTO-AFIP-RESEARCH-SCHEMA-V2-M1",
            "event_type": "BAR_PROCESSED",
            "replay_index": replay_index,
        })

    messages: list[str] = []
    summary = AutomaticResearchRuntime(tmp_path, progress=messages.append).run(
        collect_mt5_when_needed=False,
        maximum_replay_bars=10,
    )

    assert summary.replay_bars_processed == 2
    assert any("stale checkpoint" in message for message in messages)
    assert summary.status == "READY"


def test_recovery_keeps_research_append_only() -> None:
    source = Path("afip/automatic_research_runtime/runtime.py").read_text(encoding="utf-8")
    assert "stale checkpoint" in source
    assert "GEN-{window_identity}" in source
    assert "unlink(" not in source
