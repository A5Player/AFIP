from afip.historical_data_manager import HistoricalDataDownloadPipeline


UNIVERSAL_TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def _record(timeframes, downloaded_bars, requested_days=365):
    return {
        "broker": "XM",
        "symbol": "GOLD#",
        "historical_download_requested": True,
        "requested_days": requested_days,
        "downloaded_bars": downloaded_bars,
        "missing_bars": 0,
        "duplicate_bars": 0,
        "invalid_bars": 0,
        "timeframes": timeframes,
    }


def test_legacy_six_timeframes_require_universal_contract_alignment():
    report = HistoricalDataDownloadPipeline().evaluate_one(
        _record(("M1", "M5", "M15", "H1", "H4", "D1"), 70000)
    )
    assert report.status == "REVIEW"
    assert report.walk_forward_ready is False
    assert "required_timeframes_missing" in report.validation_items
    assert report.expected_bars == 365 * 24 * 7


def test_dashboard_fixture_uses_universal_bar_count():
    report = HistoricalDataDownloadPipeline().evaluate_one(
        _record(UNIVERSAL_TIMEFRAMES, 168, requested_days=1)
    )
    assert report.status == "READY"
    assert report.expected_bars == 168


def test_m30_is_required_by_universal_readiness_contract():
    report = HistoricalDataDownloadPipeline().evaluate_one(
        _record(UNIVERSAL_TIMEFRAMES, 70000)
    )
    assert "M30" in report.timeframes
    assert report.status == "READY"
    assert "required_timeframes_missing" not in report.validation_items
