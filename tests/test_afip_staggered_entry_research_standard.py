from pathlib import Path

from afip.research_standardization import (
    PatternResearchIdentity,
    PatternShapeSignature,
    StaggeredEntryObservation,
    StaggeredEntryStandardRecalibrator,
)


def _identity() -> PatternResearchIdentity:
    return PatternResearchIdentity(
        "GOLD#", "M15", "TREND", "PULLBACK", "SHORT_LOWER_WICK", "BUY",
        "UPTREND", "UP", "SUPPORTIVE", "NORMAL", "LONDON", "NORMAL",
        "H1_UP_M15_PULLBACK", "TREND_PULLBACK", "STRUCTURAL_STOP", "ATR_TARGET",
    )


def _shape() -> PatternShapeSignature:
    return PatternShapeSignature(5, 4500, .5, .1, .4, .6, 1.2, .7)


def test_staggered_research_waits_until_new_1000_boundary(tmp_path: Path) -> None:
    rows = [
        StaggeredEntryObservation(
            f"P{i}", i, _identity(), _shape(), mode, "WIN", 25, 8, 10,
            3 if mode != "SINGLE_ENTRY" else 1, mode == "SINGLE_ENTRY", False, 1, "XMARKET-A",
        )
        for i in range(1, 1000)
        for mode in StaggeredEntryStandardRecalibrator.MODES
    ]
    result = StaggeredEntryStandardRecalibrator(str(tmp_path)).evaluate(rows)
    assert result[-1]["status"] == "WAITING"
    assert not (tmp_path / "staggered_entry_research_standards.jsonl").exists()


def test_new_1000_is_merged_with_prior_cumulative_state(tmp_path: Path) -> None:
    def rows(start: int, stop: int):
        return [
            StaggeredEntryObservation(
                f"P{i}", i, _identity(), _shape(), mode,
                "WIN" if mode == "STAGGERED_TREND_PULLBACK_1_1_1" else "LOSS",
                25 if mode == "STAGGERED_TREND_PULLBACK_1_1_1" else -5,
                8, 10, 3 if mode != "SINGLE_ENTRY" else 1,
                mode == "SINGLE_ENTRY", False, 1, "XMARKET-A",
            )
            for i in range(start, stop)
            for mode in StaggeredEntryStandardRecalibrator.MODES
        ]

    first = StaggeredEntryStandardRecalibrator(str(tmp_path)).evaluate(rows(1, 1001))
    assert first[0]["standard"]["pattern_count"] == 1000
    assert first[0]["standard"]["entry_mode"] == "STAGGERED_TREND_PULLBACK_1_1_1"
    second = StaggeredEntryStandardRecalibrator(str(tmp_path)).evaluate(rows(1001, 2001))
    assert second[0]["standard"]["pattern_count"] == 2000
    assert second[0]["reason"] == "incremental_1000_merged_into_cumulative_standard"
    assert (tmp_path / "staggered_entry_cumulative_aggregates.jsonl").exists()
