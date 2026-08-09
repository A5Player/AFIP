from afip.historical_data_manager.timeframe_quality import TimeframeDataQuality


def _bar(timestamp: str, timeframe: str) -> dict[str, object]:
    return {
        "timestamp_utc": timestamp,
        "timeframe": timeframe,
        "open": 1.0,
        "high": 1.0,
        "low": 1.0,
        "close": 1.0,
    }


def test_bounded_observed_session_window_is_expected_only_for_its_evidence_range():
    quality = TimeframeDataQuality(
        observed_closure_windows=(
            {
                "start_utc": "2026-03-09T22:30:00Z",
                "end_utc": "2026-03-10T00:00:00Z",
                "timeframes": ["M30", "H1"],
                "reason_code": "OBSERVED_HISTORIC_SESSION_CLOSURE",
            },
        ),
    ).evaluate((_bar("2026-03-09T22:30:00Z", "M30"), _bar("2026-03-10T00:00:00Z", "M30")))

    gap = quality["M30"].gaps[0]

    assert gap.classification == "EXPECTED_MARKET_CLOSURE"
    assert gap.unexpected_missing_bar_count == 0
    assert "OBSERVED_HISTORIC_SESSION_CLOSURE" in gap.reason_codes


def test_observed_window_does_not_hide_missing_bars_outside_its_timeframe():
    quality = TimeframeDataQuality(
        observed_closure_windows=(
            {
                "start_utc": "2026-03-09T22:30:00Z",
                "end_utc": "2026-03-10T00:00:00Z",
                "timeframes": ["M30"],
            },
        ),
    ).evaluate((_bar("2026-03-09T22:00:00Z", "H1"), _bar("2026-03-10T00:00:00Z", "H1")))

    gap = quality["H1"].gaps[0]

    assert gap.unexpected_missing_bar_count == 1
    assert gap.backfill_eligible is True
