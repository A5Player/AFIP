"""Historical data download and quality pipeline for Milestone H Pack 5.

This module plans historical data downloads for XM GOLD# only. It does not open
orders, does not change trading logic, and does not require live execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from afip.timeframe_registry import get_supported_timeframes

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
DEFAULT_TIMEFRAMES = get_supported_timeframes(capability="historical_collection")
MIN_QUALITY_SCORE = 99.0
MIN_RESEARCH_QUALITY_SCORE = 95.0


@dataclass(frozen=True)
class HistoricalDataDownloadStep:
    name: str
    thai_name: str
    description: str
    waiting_reason: str
    output: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalDataQualityReport:
    status: str
    reason: str
    broker: str
    symbol: str
    timeframes: tuple[str, ...]
    requested_days: int
    expected_bars: int
    downloaded_bars: int
    missing_bars: int
    duplicate_bars: int
    invalid_bars: int
    quality_score: float
    missing_bar_policy: str
    walk_forward_ready: bool
    research_ready: bool
    paper_trading_ready: bool
    validation_items: tuple[str, ...]
    download_steps: tuple[HistoricalDataDownloadStep, ...]
    research_statistics_scope: str = "RESEARCH_ONLY"
    live_statistics_scope: str = "LIVE_SEPARATE"
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["download_steps"] = [step.as_dict() for step in self.download_steps]
        return data

    def as_text(self) -> str:
        return (
            "AFIP Historical Data Download Pipeline\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Broker: {self.broker}\n"
            f"Symbol: {self.symbol}\n"
            f"Timeframes: {', '.join(self.timeframes)}\n"
            f"Quality Score: {self.quality_score}\n"
            f"Walk Forward Ready: {self.walk_forward_ready}\n"
            f"Research Ready: {self.research_ready}\n"
            f"Paper Trading Ready: {self.paper_trading_ready}"
        )


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _timeframes(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        parts = [item.strip().upper() for item in value.split(",") if item.strip()]
    elif isinstance(value, Sequence):
        parts = [str(item).strip().upper() for item in value if str(item).strip()]
    else:
        parts = []
    return tuple(parts) or DEFAULT_TIMEFRAMES


def default_download_steps() -> tuple[HistoricalDataDownloadStep, ...]:
    return (
        HistoricalDataDownloadStep("connect_mt5", "เชื่อมต่อ MT5", "Validate MT5 terminal and XM account visibility before downloading data.", "mt5_connection_required", "mt5_ready"),
        HistoricalDataDownloadStep("select_gold", "เลือกสัญลักษณ์ทอง", "Resolve and select GOLD# only for Version 1 historical data.", "gold_symbol_required", "gold_selected"),
        HistoricalDataDownloadStep("download_timeframes", "ดาวน์โหลดหลายกรอบเวลา", "Download M1, M5, M15, M30, H1, H4, and D1 bars for research and walk forward.", "historical_bars_required", "timeframe_bars_downloaded"),
        HistoricalDataDownloadStep("validate_quality", "ตรวจคุณภาพข้อมูล", "Validate missing bars, duplicate bars, invalid bars, and quality score.", "quality_validation_required", "quality_report_ready"),
        HistoricalDataDownloadStep("build_datasets", "สร้างชุดข้อมูลวิจัย", "Build separated Research, Walk Forward, and Paper Trading datasets.", "dataset_build_required", "datasets_ready"),
    )


class HistoricalDataDownloadPipeline:
    """Plan and validate historical data readiness for research and walk forward."""

    def evaluate_one(self, record: Mapping[str, Any]) -> HistoricalDataQualityReport:
        broker = str(record.get("broker", VERSION1_BROKER)).strip().upper() or VERSION1_BROKER
        symbol = str(record.get("symbol", VERSION1_SYMBOL)).strip().upper() or VERSION1_SYMBOL
        download_requested = bool(record.get("historical_download_requested", False))
        timeframes = _timeframes(record.get("timeframes", DEFAULT_TIMEFRAMES))
        requested_days = max(1, _int(record.get("requested_days", 365), 365))
        downloaded_bars = max(0, _int(record.get("downloaded_bars", record.get("bars", 0)), 0))
        missing_bars = max(0, _int(record.get("missing_bars", 0), 0))
        duplicate_bars = max(0, _int(record.get("duplicate_bars", 0), 0))
        invalid_bars = max(0, _int(record.get("invalid_bars", 0), 0))
        expected_bars = requested_days * 24 * max(1, len(timeframes))
        validation_items: list[str] = []
        if broker != VERSION1_BROKER:
            validation_items.append("version1_xm_only_required")
        if symbol != VERSION1_SYMBOL:
            validation_items.append("version1_gold_only_required")
        missing_timeframes = [tf for tf in DEFAULT_TIMEFRAMES if tf not in timeframes]
        if missing_timeframes:
            validation_items.append("required_timeframes_missing")
        if downloaded_bars < expected_bars:
            validation_items.append("downloaded_bars_below_expected_window")
        if missing_bars:
            validation_items.append("missing_bars_detected")
        if duplicate_bars:
            validation_items.append("duplicate_bars_detected")
        if invalid_bars:
            validation_items.append("invalid_bars_detected")
        total = max(1, downloaded_bars + missing_bars + duplicate_bars + invalid_bars)
        quality_score = round(max(0.0, 100.0 - ((missing_bars + duplicate_bars + invalid_bars) / total * 100.0)), 2)
        walk_forward_ready = not validation_items and quality_score >= MIN_QUALITY_SCORE
        research_ready = broker == VERSION1_BROKER and symbol == VERSION1_SYMBOL and downloaded_bars > 0 and quality_score >= MIN_RESEARCH_QUALITY_SCORE
        paper_trading_ready = walk_forward_ready and research_ready
        if walk_forward_ready:
            status, reason = "READY", "historical_data_download_pipeline_ready"
        elif not download_requested:
            status, reason = "READY", "historical_data_download_not_requested"
        elif research_ready:
            status, reason = "REVIEW", "research_dataset_ready_walk_forward_waiting_for_quality"
        else:
            status, reason = "WAITING", "historical_data_download_and_quality_validation_required"
        return HistoricalDataQualityReport(
            status=status,
            reason=reason,
            broker=broker,
            symbol=symbol,
            timeframes=timeframes,
            requested_days=requested_days,
            expected_bars=expected_bars,
            downloaded_bars=downloaded_bars,
            missing_bars=missing_bars,
            duplicate_bars=duplicate_bars,
            invalid_bars=invalid_bars,
            quality_score=quality_score,
            missing_bar_policy="download_then_validate_before_research_or_walk_forward",
            walk_forward_ready=walk_forward_ready,
            research_ready=research_ready,
            paper_trading_ready=paper_trading_ready,
            validation_items=tuple(validation_items),
            download_steps=default_download_steps(),
        )

    def explain_one(self, record: Mapping[str, Any]) -> HistoricalDataQualityReport:
        return self.evaluate_one(record)
