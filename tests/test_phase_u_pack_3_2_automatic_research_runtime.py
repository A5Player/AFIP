import json
from pathlib import Path

from afip.automatic_research_runtime import AutomaticResearchRuntime


def test_discovers_ohlc_and_replays_without_future_data(tmp_path):
    source = tmp_path / "data" / "research" / "bars.jsonl"
    source.parent.mkdir(parents=True)
    rows = [
        {"timestamp_utc":"2026-01-01T00:00:00Z","timeframe":"H1","open":100,"high":102,"low":99,"close":101,"volume":10},
        {"timestamp_utc":"2026-01-01T01:00:00Z","timeframe":"H1","open":101,"high":104,"low":100,"close":103,"volume":None},
    ]
    source.write_text("\n".join(json.dumps(row) for row in rows)+"\n", encoding="utf-8")
    summary = AutomaticResearchRuntime(tmp_path).run(collect_mt5_when_needed=False)
    assert summary.status == "READY"
    assert summary.usable_bars == 2
    assert summary.replay_bars_processed == 2
    assert summary.order_send_called is False
    assert (tmp_path / "runtime" / "research" / "automatic_research_status.json").exists()


def test_missing_evidence_is_not_added_as_zero_score(tmp_path):
    source = tmp_path / "data" / "research" / "bars.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps([{"timestamp_utc":"2026-01-01T00:00:00Z","timeframe":"H1","open":100,"high":102,"low":99,"close":101}]), encoding="utf-8")
    AutomaticResearchRuntime(tmp_path).run(collect_mt5_when_needed=False)
    candidates = Path(tmp_path / "runtime" / "research" / "automatic" / "schema_v2" / "candidates.jsonl").read_text(encoding="utf-8")
    assert "volume" in candidates
    assert "AVAILABLE_EVIDENCE_ONLY" in candidates


def test_runtime_source_contains_no_execution_calls():
    source = Path("afip/automatic_research_runtime/runtime.py").read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "order_check(" not in source
