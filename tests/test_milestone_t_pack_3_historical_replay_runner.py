import json
from pathlib import Path

import pytest

from afip.historical_replay_research import (
    AppendOnlyResearchDataset,
    HistoricalReplayRunner,
    HistoricalSnapshotBuilder,
    ReplayClock,
    ReplayResumeRegistry,
)


def candles():
    return [
        {"timestamp_utc": "2026-01-01T00:00:00Z", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 10},
        {"timestamp_utc": "2026-01-01T01:00:00Z", "open": 101, "high": 104, "low": 100, "close": 103, "volume": 12},
        {"timestamp_utc": "2026-01-01T02:00:00Z", "open": 103, "high": 105, "low": 101, "close": 102, "volume": 8},
        {"timestamp_utc": "2026-01-01T03:00:00Z", "open": 102, "high": 106, "low": 102, "close": 105, "volume": 15},
    ]


def candidate_provider(snapshot):
    if snapshot.market_snapshot["visible_direction"] == "BUY":
        return ({
            "direction": "BUY",
            "pattern_family": "TREND_CONTINUATION",
            "setup_id": f"SETUP-{snapshot.replay_clock['replay_index']}",
            "confidence": 75,
            "rationale_codes": ("visible_direction_buy",),
        },)
    return ()


def runner(tmp_path, **kwargs):
    dataset = AppendOnlyResearchDataset(tmp_path / "research" / "experimental" / "replay-1")
    return dataset, HistoricalReplayRunner(dataset=dataset, **kwargs)


def run_replay(replay_runner, **overrides):
    values = {
        "replay_id": "REPLAY-1",
        "research_run_id": "RUN-1",
        "dataset_version": "DATA-T3-1",
        "scenario_id": "GOLD-H1-1",
        "candles": candles(),
    }
    values.update(overrides)
    return replay_runner.run(**values)


def test_replay_walks_every_bar_in_chronological_order(tmp_path):
    dataset, replay_runner = runner(tmp_path)
    summary = run_replay(replay_runner)
    snapshots = dataset.records("snapshots")
    assert summary.bars_processed == 4
    assert [item["record"]["replay_clock"]["replay_index"] for item in snapshots] == [0, 1, 2, 3]
    assert [item["record"]["replay_clock"]["visible_candle_count"] for item in snapshots] == [1, 2, 3, 4]


def test_snapshot_provider_never_receives_future_candles(tmp_path):
    observed = []

    def provider(visible, clock):
        observed.append((len(visible), clock.replay_index, visible[-1].timestamp_utc))
        return HistoricalSnapshotBuilder.build_default(visible, clock)

    _, replay_runner = runner(tmp_path, snapshot_provider=provider)
    run_replay(replay_runner)
    assert observed == [
        (1, 0, "2026-01-01T00:00:00Z"),
        (2, 1, "2026-01-01T01:00:00Z"),
        (3, 2, "2026-01-01T02:00:00Z"),
        (4, 3, "2026-01-01T03:00:00Z"),
    ]


def test_replay_clock_progress_is_deterministic():
    clock = ReplayClock(1, "2026-01-01T01:00:00Z", 2, 4)
    assert clock.progress_ratio == 0.5
    assert clock.as_dict()["progress_ratio"] == 0.5


def test_default_snapshot_uses_visible_history_only():
    from afip.research_replay import ReplayCandle

    values = tuple(ReplayCandle.from_mapping(value) for value in candles()[:2])
    clock = ReplayClock(1, values[-1].timestamp_utc, 2, 4)
    snapshot = HistoricalSnapshotBuilder.build_default(values, clock)
    assert snapshot["visible_high"] == 104
    assert snapshot["visible_low"] == 99
    assert snapshot["visible_direction"] == "BUY"


def test_candidate_generation_is_append_only_and_experimental(tmp_path):
    dataset, replay_runner = runner(tmp_path, candidate_provider=candidate_provider)
    summary = run_replay(replay_runner)
    candidates = dataset.records("candidates")
    assert summary.candidates_generated == 3
    assert len(candidates) == 3
    assert all(item["record"]["research_state"] == "EXPERIMENTAL" for item in candidates)
    assert all(len(item["record"]["candidate_checksum"]) == 64 for item in candidates)


def test_decision_dataset_records_wait_and_candidate_states(tmp_path):
    dataset, replay_runner = runner(tmp_path, candidate_provider=candidate_provider)
    run_replay(replay_runner)
    statuses = [item["record"]["decision_status"] for item in dataset.records("decisions")]
    assert statuses == ["NO_CANDIDATE", "CANDIDATES_GENERATED", "CANDIDATES_GENERATED", "CANDIDATES_GENERATED"]
    assert all(item["record"]["production_usable"] is False for item in dataset.records("decisions"))


def test_dataset_chain_checksum_verifies(tmp_path):
    dataset, replay_runner = runner(tmp_path, candidate_provider=candidate_provider)
    run_replay(replay_runner)
    assert all(dataset.verify(name) for name in dataset.DATASET_NAMES)
    timeline = dataset.records("timeline")
    assert timeline[0]["previous_chain_checksum"] == "GENESIS"
    assert timeline[1]["previous_chain_checksum"] == timeline[0]["chain_checksum"]


def test_dataset_tampering_is_detected(tmp_path):
    dataset, replay_runner = runner(tmp_path)
    run_replay(replay_runner)
    path = dataset.path_for("snapshots")
    lines = path.read_text(encoding="utf-8").splitlines()
    envelope = json.loads(lines[0])
    envelope["record"]["market_snapshot"]["latest_close"] = 999
    lines[0] = json.dumps(envelope, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert dataset.verify("snapshots") is False


def test_replay_resume_continues_after_last_processed_bar(tmp_path):
    dataset, replay_runner = runner(tmp_path, candidate_provider=candidate_provider)
    first = run_replay(replay_runner, maximum_bars=2)
    assert first.completed is False
    assert ReplayResumeRegistry.next_index(dataset, "REPLAY-1") == 2
    second = run_replay(replay_runner, resume=True)
    assert second.resumed_from_index == 2
    assert second.bars_processed == 2
    assert second.completed is True
    assert [item["record"]["replay_index"] for item in dataset.records("timeline")] == [0, 1, 2, 3]


def test_replay_without_resume_starts_new_append_history(tmp_path):
    dataset, replay_runner = runner(tmp_path)
    run_replay(replay_runner, maximum_bars=1)
    run_replay(replay_runner, maximum_bars=1)
    assert dataset.count("snapshots") == 2
    assert dataset.verify("snapshots") is True


def test_dashboard_metadata_reports_quarantine_and_not_production(tmp_path):
    dataset, replay_runner = runner(tmp_path, candidate_provider=candidate_provider)
    run_replay(replay_runner)
    metadata = dataset.dashboard_metadata()
    assert metadata["research_state"] == "EXPERIMENTAL"
    assert metadata["production_usable"] is False
    assert metadata["append_only_verified"] is True
    assert metadata["dataset_counts"]["snapshots"] == 4
    assert metadata["quarantine_size"] == metadata["research_dataset_size"]


def test_summary_has_integrity_and_no_future_leakage(tmp_path):
    dataset, replay_runner = runner(tmp_path)
    summary = run_replay(replay_runner)
    assert summary.future_leakage_detected is False
    assert summary.research_state == "EXPERIMENTAL"
    assert len(summary.summary_checksum) == 64
    assert dataset.count("run_summaries") == 1


def test_runner_requires_all_research_identifiers(tmp_path):
    _, replay_runner = runner(tmp_path)
    with pytest.raises(ValueError, match="required historical replay identifiers"):
        run_replay(replay_runner, replay_id="")


def test_runner_rejects_non_positive_maximum_bars(tmp_path):
    _, replay_runner = runner(tmp_path)
    with pytest.raises(ValueError, match="maximum_bars must be positive"):
        run_replay(replay_runner, maximum_bars=0)


def test_candidate_validation_rejects_invalid_confidence(tmp_path):
    def invalid_provider(snapshot):
        return ({"direction": "BUY", "confidence": 101},)

    _, replay_runner = runner(tmp_path, candidate_provider=invalid_provider)
    with pytest.raises(ValueError, match="confidence"):
        run_replay(replay_runner)


def test_module_contains_no_mt5_execution_calls():
    source = Path("afip/historical_replay_research/runtime.py").read_text(encoding="utf-8")
    forbidden = ("order_send(", "order_check(", "positions_get(", "MetaTrader5")
    assert not any(value in source for value in forbidden)
