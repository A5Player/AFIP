from pathlib import Path

from afip.automatic_research_runtime import AutomaticResearchRuntime
from afip.financial_data_lake import FinancialDataLake
from afip.historical_data_manager.live_runtime import HistoricalDataLiveRuntime
from afip.timeframe_registry import get_supported_timeframes


def bar(ts: str, timeframe: str = "M30") -> dict:
    return {"timestamp_utc": ts, "open": 100.0, "high": 101.0, "low": 99.0,
            "close": 100.5, "volume": 10.0, "timeframe": timeframe, "source": "MT5:GOLD#"}


def test_m30_is_historical_collection_capability():
    assert get_supported_timeframes(capability="historical_collection") == (
        "M1", "M5", "M15", "M30", "H1", "H4", "D1"
    )


def test_live_historical_report_includes_m30():
    report = HistoricalDataLiveRuntime().evaluate_one({"bars_per_timeframe": 20})
    assert tuple(name for name, _ in report.timeframe_bars) == (
        "M1", "M5", "M15", "M30", "H1", "H4", "D1"
    )


def test_automatic_runtime_persists_m30_append_only(tmp_path: Path):
    runtime = AutomaticResearchRuntime(tmp_path)
    appended, duplicates = runtime.persist_historical_bars([
        bar("2026-07-19T00:00:00Z"), bar("2026-07-19T00:30:00Z")
    ])
    assert (appended, duplicates) == (2, 0)
    appended2, duplicates2 = runtime.persist_historical_bars([
        bar("2026-07-19T00:00:00Z"), bar("2026-07-19T00:30:00Z")
    ])
    assert (appended2, duplicates2) == (0, 2)
    records = tuple(runtime.historical_lake_root.rglob("records.jsonl"))
    assert records and sum(len(path.read_text(encoding="utf-8").splitlines()) for path in records) == 2


def test_lake_batch_append_preserves_distinct_timeframes(tmp_path: Path):
    lake = FinancialDataLake(tmp_path)
    records = tuple(lake.build_record(
        layer="normalized", domain="market_ohlc", instrument="GOLD#", source_id="MT5:GOLD#",
        observed_at_utc="2026-07-19T00:00:00Z",
        payload={"timeframe": timeframe, "open": 1, "high": 2, "low": 0, "close": 1.5},
        provenance={"provider": "MT5", "timeframe": timeframe}, quality={"ohlc_valid": True},
        research_eligibility="ELIGIBLE") for timeframe in ("M15", "M30"))
    result = lake.append_many(records)
    assert len(result) == 2 and all(not item.duplicate for item in result)


def test_research_persistence_has_no_execution_authority(tmp_path: Path):
    runtime = AutomaticResearchRuntime(tmp_path)
    assert not hasattr(runtime, "order_send")
    assert runtime.persist_historical_bars([bar("2026-07-19T00:00:00Z")]) == (1, 0)
