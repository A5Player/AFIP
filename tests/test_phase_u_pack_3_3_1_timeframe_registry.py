from pathlib import Path

import pytest

from afip.historical_data_manager.download_pipeline import DEFAULT_TIMEFRAMES, HistoricalDataDownloadPipeline
from afip.market.timeframe_adapter import TimeframeAdapter
from afip.timeframe_registry import (
    SUPPORTED_TIMEFRAMES,
    TIMEFRAME_REGISTRY,
    get_minutes,
    get_mt5_timeframe_code,
    get_seconds,
    get_supported_timeframes,
    get_timeframe_metadata,
    is_supported,
)


def test_registry_has_deterministic_universal_order_with_m30() -> None:
    assert SUPPORTED_TIMEFRAMES == ("M1", "M5", "M15", "M30", "H1", "H4", "D1")
    assert get_supported_timeframes(capability="historical_collection") == SUPPORTED_TIMEFRAMES
    assert get_supported_timeframes(capability="chronological_replay") == SUPPORTED_TIMEFRAMES
    assert get_supported_timeframes(capability="research") == SUPPORTED_TIMEFRAMES


def test_m30_metadata_is_complete_and_schema_safe() -> None:
    metadata = get_timeframe_metadata("m30")
    assert metadata["name"] == "M30"
    assert metadata["minutes"] == 30
    assert metadata["seconds"] == 1800
    assert metadata["mt5_constant_name"] == "TIMEFRAME_M30"
    assert metadata["historical_collection_enabled"] is True
    assert metadata["chronological_replay_enabled"] is True
    assert metadata["research_enabled"] is True


def test_registry_is_immutable_and_rejects_unknown_timeframes() -> None:
    with pytest.raises(TypeError):
        TIMEFRAME_REGISTRY["M2"] = TIMEFRAME_REGISTRY["M1"]  # type: ignore[index]
    assert is_supported("M30") is True
    assert is_supported("M2") is False
    with pytest.raises(ValueError, match="Unsupported timeframe"):
        get_minutes("M2")


def test_timeframe_conversion_uses_registry_without_behavior_change() -> None:
    adapter = TimeframeAdapter()
    assert adapter.to_minutes("m1") == 1
    assert adapter.to_minutes("M30") == 30
    assert adapter.to_minutes("d1") == 1440
    assert get_seconds("H4") == 14_400
    assert adapter.DEFAULTS == {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


def test_mt5_code_resolution_is_data_driven() -> None:
    class FakeMT5:
        TIMEFRAME_M30 = 30

    assert get_mt5_timeframe_code(FakeMT5, "M30") == 30


def test_historical_pipeline_requires_m30_and_preserves_defaults() -> None:
    assert DEFAULT_TIMEFRAMES == SUPPORTED_TIMEFRAMES
    report = HistoricalDataDownloadPipeline().evaluate_one({
        "historical_download_requested": True,
        "requested_days": 1,
        "downloaded_bars": 168,
        "timeframes": ["M1", "M5", "M15", "H1", "H4", "D1"],
    })
    assert "required_timeframes_missing" in report.validation_items


def test_automatic_runtime_no_longer_owns_a_duplicated_timeframe_tuple() -> None:
    source = Path("afip/automatic_research_runtime/runtime.py").read_text(encoding="utf-8")
    assert 'get_supported_timeframes(capability="chronological_replay")' in source
    assert 'get_supported_timeframes(capability="historical_collection")' in source
    assert '("M1", "M5", "M15", "H1", "H4", "D1")' not in source


def test_pack_does_not_enable_live_execution_or_order_send() -> None:
    source = Path("afip/timeframe_registry.py").read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "live_execution_enabled" not in source
