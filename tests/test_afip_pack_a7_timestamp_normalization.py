from afip.automatic_research_runtime.runtime import _ohlc


def _bar(timestamp: str) -> dict[str, object]:
    return {
        "timeframe": "H1",
        "timestamp_utc": timestamp,
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
    }


def test_equivalent_utc_timestamp_forms_have_one_canonical_dedup_key() -> None:
    zulu = _ohlc(_bar("2026-08-08T14:00:00Z"), source="first")
    offset = _ohlc(_bar("2026-08-08T14:00:00+00:00"), source="second")

    assert zulu is not None and offset is not None
    assert zulu["timestamp_utc"] == "2026-08-08T14:00:00Z"
    assert zulu["timestamp_utc"] == offset["timestamp_utc"]


def test_unparseable_timestamp_is_excluded_before_replay() -> None:
    assert _ohlc(_bar("not-a-timestamp"), source="invalid") is None
