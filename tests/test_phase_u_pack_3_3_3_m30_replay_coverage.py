import json
from pathlib import Path

from afip.automatic_research_runtime import AutomaticResearchRuntime
from afip.historical_replay_research import AppendOnlyResearchDataset


def _bars(timeframe: str, count: int) -> list[dict]:
    return [
        {"timeframe": timeframe, "timestamp_utc": f"2026-01-01T00:{i:02d}:00Z", "open": 100+i,
         "high": 102+i, "low": 99+i, "close": 101+i, "tick_volume": 10+i}
        for i in range(count)
    ]


def test_m30_replay_records_complete_coverage_evidence(tmp_path: Path) -> None:
    source = tmp_path / "data" / "historical" / "bars.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(_bars("M30", 4)), encoding="utf-8")
    summary = AutomaticResearchRuntime(tmp_path).run(collect_mt5_when_needed=False, maximum_replay_bars=10)
    evidence = summary.replay_timeframe_evidence["M30"]
    assert evidence["available_bars"] == 4
    assert evidence["bars_processed_this_run"] == 4
    assert evidence["covered_bars_after_run"] == 4
    assert evidence["coverage_complete"] is True
    assert "-GEN-" in evidence["replay_id"]


def test_legacy_partial_checkpoint_is_not_assumed_to_cover_current_window(tmp_path: Path) -> None:
    source = tmp_path / "data" / "historical" / "bars.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(_bars("M5", 5)), encoding="utf-8")
    dataset = AppendOnlyResearchDataset(tmp_path / "runtime" / "research" / "automatic" / "schema_v2")
    for index in range(2):
        dataset.append("timeline", {"replay_id": "AUTO-AFIP-RESEARCH-SCHEMA-V2-M5", "event_type": "BAR_PROCESSED", "replay_index": index})
    summary = AutomaticResearchRuntime(tmp_path).run(collect_mt5_when_needed=False, maximum_replay_bars=10)
    evidence = summary.replay_timeframe_evidence["M5"]
    assert evidence["legacy_checkpoint_next_index"] == 2
    assert evidence["resumed_from_index"] == 0
    assert evidence["bars_processed_this_run"] == 5
    assert evidence["selection_reason"] == "legacy_checkpoint_not_coverage_provable"


def test_exact_window_generation_continues_deterministically(tmp_path: Path) -> None:
    source = tmp_path / "data" / "historical" / "bars.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(_bars("M15", 5)), encoding="utf-8")
    first = AutomaticResearchRuntime(tmp_path).run(collect_mt5_when_needed=False, maximum_replay_bars=2)
    assert first.replay_timeframe_evidence["M15"]["coverage_complete"] is False
    second = AutomaticResearchRuntime(tmp_path).run(collect_mt5_when_needed=False, maximum_replay_bars=10)
    evidence = second.replay_timeframe_evidence["M15"]
    assert evidence["resumed_from_index"] == 2
    assert evidence["bars_processed_this_run"] == 3
    assert evidence["coverage_complete"] is True
    assert evidence["selection_reason"] == "exact_window_checkpoint_continuation"


def test_runtime_still_contains_no_execution_calls() -> None:
    source = Path("afip/automatic_research_runtime/runtime.py").read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "order_check(" not in source
