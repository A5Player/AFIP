from pathlib import Path

import pytest

from afip.exit_evidence_research import A17ReplayResearchIntake
from afip.exit_outcome_research import A16PolicySet, A16ResearchContext, PositionResearchCase
from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_replay import ReplayCandle


def _context() -> A16ResearchContext:
    return A16ResearchContext("PATTERN", "BREAKOUT", "PLAN-1", "2026-01-01T00:00:00Z", "TREND", "LONDON", "OPEN", "NONE", "NORMAL", "VERIFIED")


def _case(units: int = 1) -> PositionResearchCase:
    return PositionResearchCase("CASE-1", "REPLAY-1", "RUN-1", "DATA-1", "SCENARIO-1", "BUY", 0, 100.0, units)


def _candles() -> tuple[ReplayCandle, ...]:
    return (
        ReplayCandle("2026-01-01T00:00:00Z", 100, 101, 99, 100.5, 1),
        ReplayCandle("2026-01-01T01:00:00Z", 100.5, 104, 100, 103, 1),
        ReplayCandle("2026-01-01T02:00:00Z", 103, 105, 102, 104, 1),
    )


def test_intake_writes_blind_forward_evidence_and_waits_for_minimum_sample(tmp_path: Path) -> None:
    dataset = AppendOnlyResearchDataset(tmp_path / "research")
    observations, report, certification = A17ReplayResearchIntake(dataset, minimum_sample_size=2).intake(
        case=_case(), policy_set=A16PolicySet(2), candles=_candles(), context=_context(), execution_cost_r=.1,
    )
    assert len(observations) == 7 and certification.status == "WAIT"
    assert report.status == "WAIT" and dataset.count("a17_exit_replay_intake_runs") == 1
    assert dataset.verify("a16_exit_evidence_observations") and dataset.verify("a17_exit_replay_intake_runs")


def test_intake_includes_partial_runner_only_for_multiple_units(tmp_path: Path) -> None:
    dataset = AppendOnlyResearchDataset(tmp_path / "research")
    observations, _, _ = A17ReplayResearchIntake(dataset).intake(
        case=_case(2), policy_set=A16PolicySet(2), candles=_candles(), context=_context(), execution_cost_r=0,
    )
    assert {item.policy_id for item in observations} >= {"PARTIAL_RUNNER", "R_STEP"}


def test_intake_rejects_negative_cost(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cost"):
        A17ReplayResearchIntake(AppendOnlyResearchDataset(tmp_path)).intake(
            case=_case(), policy_set=A16PolicySet(2), candles=_candles(), context=_context(), execution_cost_r=-.1,
        )
