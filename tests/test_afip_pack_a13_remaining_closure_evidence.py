import json
from pathlib import Path

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


def _policy() -> dict[str, object]:
    path = Path(__file__).parents[1] / "config" / "research_metrics" / "market_session_closure_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_observed_october_h1_session_window_is_classified_as_expected():
    policy = _policy()
    quality = TimeframeDataQuality(
        expected_closure_dates=policy["expected_closure_dates"],
        daily_session_closure_utc=tuple(policy["daily_session_closure_utc"]),
        daily_session_closure_timeframes=policy["daily_session_closure_timeframes"],
        observed_closure_windows=policy["observed_closure_windows"],
    ).evaluate((_bar("2025-10-27T22:00:00Z", "H1"), _bar("2025-10-28T00:00:00Z", "H1")))

    gap = quality["H1"].gaps[0]

    assert gap.unexpected_missing_bar_count == 0
    assert "OBSERVED_HISTORIC_SESSION_CLOSURE" in gap.reason_codes


def test_h1_observed_window_does_not_whitelist_m30_data():
    policy = _policy()
    quality = TimeframeDataQuality(
        observed_closure_windows=policy["observed_closure_windows"],
    ).evaluate((_bar("2025-10-27T22:00:00Z", "M30"), _bar("2025-10-28T00:00:00Z", "M30")))

    gap = quality["M30"].gaps[0]

    assert gap.unexpected_missing_bar_count == 3
    assert gap.backfill_eligible is True
