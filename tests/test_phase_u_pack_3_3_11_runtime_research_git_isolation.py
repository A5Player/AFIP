from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = ROOT / ".gitignore"
GENERATED_SCHEMA_FILES = (
    "runtime/research/automatic/schema_v2/candidates.jsonl",
    "runtime/research/automatic/schema_v2/decisions.jsonl",
    "runtime/research/automatic/schema_v2/run_summaries.jsonl",
    "runtime/research/automatic/schema_v2/snapshots.jsonl",
    "runtime/research/automatic/schema_v2/timeline.jsonl",
)


def test_runtime_research_ignore_policy_is_present() -> None:
    policy = GITIGNORE.read_text(encoding="utf-8")
    assert "runtime/research/automatic/schema_v2/*.jsonl" in policy
    assert "runtime/research/historical_data_lake/" in policy
    assert "runtime/research/checkpoints/" in policy
    assert "runtime/research/exports/" in policy
    assert "runtime/research/quarantine/" in policy


def test_generated_schema_v2_files_are_ignored() -> None:
    for relative_path in GENERATED_SCHEMA_FILES:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", relative_path],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0, relative_path


def test_historical_data_lake_artifacts_are_ignored() -> None:
    sample = (
        "runtime/research/historical_data_lake/"
        "layer=normalized/domain=market_ohlc/instrument=GOLD_/"
        "timeframe=M30/year=2026/month=07/sample.jsonl"
    )
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", sample],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_source_and_configuration_are_not_broadly_ignored() -> None:
    protected_paths = (
        "afip/automatic_research_runtime/runtime.py",
        "config/four_profile_demo.json",
        "tests/test_phase_u_pack_3_3_11_runtime_research_git_isolation.py",
    )
    for relative_path in protected_paths:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", relative_path],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 1, relative_path
