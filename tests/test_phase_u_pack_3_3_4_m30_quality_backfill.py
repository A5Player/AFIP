from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from afip.automatic_research_runtime import AutomaticResearchRuntime
from afip.historical_data_manager import GapRange, TimeframeDataQuality
from afip.timeframe_registry import get_supported_timeframes


def bar(timeframe: str, timestamp: str, close: float = 100.0) -> dict[str, object]:
    return {
        "timeframe": timeframe,
        "timestamp_utc": timestamp,
        "open": close,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": 1.0,
        "source": "TEST",
    }


def test_registry_gap_detection_contains_m30() -> None:
    assert "M30" in get_supported_timeframes(capability="gap_detection")


def test_m30_gap_detection_reports_exact_missing_bar_count() -> None:
    engine = TimeframeDataQuality()
    evidence = engine.evaluate(
        [
            bar("M30", "2026-07-19T00:00:00Z"),
            bar("M30", "2026-07-19T01:30:00Z"),
        ],
        now_utc=datetime(2026, 7, 19, 2, 0, tzinfo=timezone.utc),
    )["M30"]
    assert evidence.gap_count == 1
    assert evidence.missing_bars == 2
    assert evidence.gaps[0].expected_interval_seconds == 1800
    assert evidence.gaps[0].observed_interval_seconds == 5400


def test_m30_integrity_rejects_invalid_ohlc_and_deduplicates() -> None:
    engine = TimeframeDataQuality()
    duplicate = bar("M30", "2026-07-19T00:00:00Z")
    invalid = bar("M30", "2026-07-19T00:30:00Z")
    invalid["high"] = 98.0
    evidence = engine.evaluate(
        [duplicate, dict(duplicate), invalid],
        now_utc=datetime(2026, 7, 19, 1, 0, tzinfo=timezone.utc),
    )["M30"]
    assert evidence.valid_bars == 1
    assert evidence.duplicate_bars == 1
    assert evidence.invalid_bars == 1
    assert evidence.integrity_status == "REVIEW"
    assert evidence.research_eligible is False


def test_freshness_is_timeframe_specific() -> None:
    engine = TimeframeDataQuality(freshness_multiplier=3)
    evidence = engine.evaluate(
        [bar("M30", "2026-07-19T00:00:00Z")],
        now_utc=datetime(2026, 7, 19, 1, 0, tzinfo=timezone.utc),
    )["M30"]
    assert evidence.freshness_limit_seconds == 5400
    assert evidence.fresh is True


def test_backfill_merges_valid_m30_records_without_rewriting_existing() -> None:
    engine = TimeframeDataQuality()
    original = [
        bar("M30", "2026-07-19T00:00:00Z"),
        bar("M30", "2026-07-19T01:30:00Z"),
    ]
    evidence = engine.evaluate(original, now_utc=datetime(2026, 7, 19, 2, 0, tzinfo=timezone.utc))

    def provider(gap: GapRange):
        assert gap.timeframe == "M30"
        return [
            bar("M30", "2026-07-19T00:30:00Z"),
            bar("M30", "2026-07-19T01:00:00Z"),
            bar("M30", "2026-07-19T00:00:00Z"),
        ]

    result = engine.backfill(original, evidence, provider)
    assert result.requested_ranges == 1
    assert result.returned_bars == 3
    assert result.accepted_bars == 2
    assert result.duplicate_bars == 1
    assert len(result.merged_bars) == 4
    assert len(original) == 2


def test_backfill_rejects_wrong_timeframe_and_invalid_bars() -> None:
    engine = TimeframeDataQuality()
    original = [bar("M30", "2026-07-19T00:00:00Z"), bar("M30", "2026-07-19T01:00:00Z")]
    evidence = engine.evaluate(original, now_utc=datetime(2026, 7, 19, 2, 0, tzinfo=timezone.utc))

    def provider(_: GapRange):
        invalid = bar("M30", "2026-07-19T00:30:00Z")
        invalid["low"] = 102.0
        return [bar("M15", "2026-07-19T00:30:00Z"), invalid]

    result = engine.backfill(original, evidence, provider)
    assert result.accepted_bars == 0
    assert result.invalid_bars == 2


def test_runtime_status_contains_m30_quality_evidence(tmp_path: Path) -> None:
    runtime = AutomaticResearchRuntime(tmp_path)
    source = tmp_path / "data" / "historical"
    source.mkdir(parents=True)
    (source / "m30.json").write_text(
        '[{"timeframe":"M30","timestamp_utc":"2026-07-19T00:00:00Z",'
        '"open":100,"high":101,"low":99,"close":100,"volume":1}]',
        encoding="utf-8",
    )
    result = runtime.run(collect_mt5_when_needed=False, maximum_replay_bars=10)
    assert result.timeframe_data_quality is not None
    assert result.timeframe_data_quality["M30"]["valid_bars"] == 1
    assert result.backfill_ranges_requested == 0
    assert result.live_execution_enabled is False
    assert result.order_send_called is False
