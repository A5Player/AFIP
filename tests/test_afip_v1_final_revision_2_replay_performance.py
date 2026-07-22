from pathlib import Path

from afip.historical_replay_research.runtime import AppendOnlyResearchDataset


def test_append_uses_cached_chain_state_without_reparsing_records(tmp_path: Path, monkeypatch):
    dataset = AppendOnlyResearchDataset(tmp_path)
    dataset.append("timeline", {"value": 1})

    def fail_records(_dataset_name: str):
        raise AssertionError("append must not reparse the complete JSONL dataset")

    monkeypatch.setattr(dataset, "records", fail_records)
    second = dataset.append("timeline", {"value": 2})

    assert second["record_sequence"] == 2
    assert second["previous_chain_checksum"] != "GENESIS"
    assert dataset.count("timeline") == 2


def test_cached_append_chain_remains_verifiable(tmp_path: Path):
    dataset = AppendOnlyResearchDataset(tmp_path)
    for index in range(100):
        dataset.append("timeline", {"index": index})

    assert dataset.count("timeline") == 100
    assert dataset.verify("timeline") is True
