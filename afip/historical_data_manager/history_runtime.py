"""Historical data validation runtime for Milestone H Pack 3."""

from __future__ import annotations

from typing import Any, Mapping

from .history_report import HistoricalDataManagerReport


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


class HistoricalDataManagerRuntime:
    """Validate historical data readiness without downloading in tests."""

    def evaluate_one(self, record: Mapping[str, Any]) -> HistoricalDataManagerReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        requested_days = max(1, _int(record.get("requested_days", 365), 365))
        downloaded_bars = max(0, _int(record.get("downloaded_bars", record.get("bars", 0)), 0))
        missing_bars = max(0, _int(record.get("missing_bars", 0), 0))
        duplicate_bars = max(0, _int(record.get("duplicate_bars", 0), 0))
        expected_minimum = requested_days * 24
        validation_items: list[str] = []
        if broker != "XM" or symbol != "GOLD#":
            validation_items.append("version1_xm_gold_only_required")
        if downloaded_bars < expected_minimum:
            validation_items.append("historical_bar_count_below_requested_window")
        if missing_bars > 0:
            validation_items.append("missing_bars_detected")
        if duplicate_bars > 0:
            validation_items.append("duplicate_bars_detected")
        total_expected = max(1, downloaded_bars + missing_bars + duplicate_bars)
        quality_score = round(max(0.0, 100.0 - ((missing_bars + duplicate_bars) / total_expected * 100.0)), 2)
        walk_forward_ready = not validation_items and downloaded_bars >= expected_minimum and quality_score >= 99.0
        research_ready = downloaded_bars > 0 and quality_score >= 95.0 and broker == "XM" and symbol == "GOLD#"
        if walk_forward_ready:
            status, reason, gate = "READY", "historical_data_ready", "HISTORICAL_DATA_READY"
        elif research_ready:
            status, reason, gate = "REVIEW", "historical_data_research_ready_walk_forward_review", "REVIEW"
        else:
            status, reason, gate = "WAITING", "historical_data_download_or_validation_required", "WAITING"
        return HistoricalDataManagerReport(status, reason, gate, broker, symbol, requested_days, downloaded_bars, missing_bars, duplicate_bars, quality_score, walk_forward_ready, research_ready, tuple(validation_items))

    def explain_one(self, record: Mapping[str, Any]) -> HistoricalDataManagerReport:
        return self.evaluate_one(record)
