"""Read-only historical data manager for Production Bring-up Pack 7."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from afip.timeframe_registry import get_supported_timeframes

_TIMEFRAMES = get_supported_timeframes(capability="historical_collection")

@dataclass(frozen=True)
class HistoricalDataLiveReport:
    status: str
    reason: str
    broker: str
    symbol: str
    source: str
    total_bars: int
    timeframe_bars: tuple[tuple[str, int], ...]
    missing_bars: int
    duplicate_bars: int
    quality_score: float
    storage_status: str
    research_ready: bool
    walk_forward_ready: bool
    next_action_en: str
    next_action_th: str
    live_execution_enabled: bool = False
    trading_logic_changed: bool = False
    def as_dict(self) -> dict[str, Any]: return asdict(self)

class HistoricalDataLiveRuntime:
    """Evaluate visible historical-data readiness without downloading or trading."""
    def evaluate_one(self, record: Mapping[str, Any]) -> HistoricalDataLiveReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        source = str(record.get("historical_data_source", "MT5_OHLC")).strip() or "MT5_OHLC"
        bars = tuple((tf, max(0, int(record.get(f"{tf.lower()}_bars", record.get("bars_per_timeframe", 20)) or 0))) for tf in _TIMEFRAMES)
        total = sum(value for _, value in bars)
        missing = max(0, int(record.get("historical_missing_bars", 0) or 0))
        duplicate = max(0, int(record.get("historical_duplicate_bars", 0) or 0))
        denominator = max(1, total + missing + duplicate)
        quality = round(max(0.0, 100.0 - ((missing + duplicate) / denominator * 100.0)), 2)
        policy_ok = broker == "XM" and symbol == "GOLD#" and not bool(record.get("live_execution_enabled", False))
        research_ready = policy_ok and total > 0 and quality >= 95.0
        walk_forward_ready = research_ready and all(value >= 20 for _, value in bars) and missing == 0 and duplicate == 0
        if not policy_ok:
            status, reason = "BLOCKED", "historical_data_blocked_by_version1_or_live_policy"
            en, th = "Use XM, GOLD#, and disabled live execution.", "ใช้ XM, GOLD# และปิดการส่งคำสั่งจริง"
        elif walk_forward_ready:
            status, reason = "READY", "historical_data_ready_for_research_and_walk_forward"
            en, th = "Continue scheduled historical-data review.", "ดำเนินการตรวจสอบข้อมูลย้อนหลังตามรอบต่อไป"
        elif research_ready:
            status, reason = "REVIEW", "historical_data_research_ready_walk_forward_pending"
            en, th = "Complete missing timeframe coverage before walk-forward use.", "เติมข้อมูลทุก Timeframe ให้ครบก่อนใช้ Walk-Forward"
        else:
            status, reason = "WAITING", "historical_data_collection_or_quality_review_required"
            en, th = "Collect and validate historical bars.", "รวบรวมและตรวจสอบแท่งข้อมูลย้อนหลัง"
        return HistoricalDataLiveReport(status, reason, broker, symbol, source, total, bars, missing, duplicate, quality, "READ_ONLY", research_ready, walk_forward_ready, en, th)
    def explain_one(self, record: Mapping[str, Any]) -> HistoricalDataLiveReport:
        return self.evaluate_one(record)
