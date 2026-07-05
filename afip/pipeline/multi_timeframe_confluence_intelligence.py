"""
AFIP Production Sprint 9 — Multi-Timeframe Confluence Intelligence.

Aggregates official GOLD# OHLC snapshots across M15/H1/H4/D1 into one
transparent market context for the existing Modular Intelligence pipeline.
This is read-only and never unlocks execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TimeframeSignal:
    timeframe: str
    direction: str
    confidence: float
    change: float
    range_size: float
    source: str


class MultiTimeframeConfluenceIntelligence:
    """
    Build one official confluence snapshot from multiple market timeframes.

    Financial naming standard:
    - Execution timeframe: M15/M5 for execution entry context.
    - Intraday trend timeframe: H1.
    - Institutional bias timeframe: H4/D1.
    """

    TIMEFRAME_WEIGHTS = {
        "M1": 0.05,
        "M5": 0.10,
        "M15": 0.15,
        "H1": 0.30,
        "H4": 0.25,
        "D1": 0.15,
    }

    PRIMARY_TIMEFRAME_PRIORITY = ("H1", "H4", "M15", "D1", "M5", "M1")

    def build(self, snapshots: dict[str, dict[str, Any]]) -> dict[str, Any]:
        signals = [self._timeframe_signal(tf, snap) for tf, snap in snapshots.items() if self._has_ohlc(snap)]
        signals = [signal for signal in signals if signal is not None]

        if not signals:
            return {
                "status": "NO_DATA",
                "direction": "WAIT",
                "confidence": 0.0,
                "score": 0.0,
                "primary_timeframe": None,
                "aligned_timeframes": 0,
                "available_timeframes": [],
                "signals": [],
                "snapshot": {},
            }

        weighted_buy = 0.0
        weighted_sell = 0.0
        total_weight = 0.0
        for signal in signals:
            weight = self.TIMEFRAME_WEIGHTS.get(signal.timeframe, 0.10)
            total_weight += weight
            if signal.direction == "BUY":
                weighted_buy += weight * signal.confidence
            elif signal.direction == "SELL":
                weighted_sell += weight * signal.confidence

        buy_score = weighted_buy / total_weight if total_weight else 0.0
        sell_score = weighted_sell / total_weight if total_weight else 0.0
        edge = abs(buy_score - sell_score)

        if buy_score > sell_score and edge >= 5:
            direction = "BUY"
            confidence = min(100.0, 50.0 + edge)
        elif sell_score > buy_score and edge >= 5:
            direction = "SELL"
            confidence = min(100.0, 50.0 + edge)
        else:
            direction = "WAIT"
            confidence = max(0.0, 50.0 - edge)

        aligned = sum(1 for signal in signals if signal.direction == direction) if direction != "WAIT" else 0
        primary_timeframe = self._select_primary_timeframe(snapshots)
        primary_snapshot = dict(snapshots.get(primary_timeframe, {}) if primary_timeframe else {})
        confluence_snapshot = self._merge_snapshot(primary_snapshot, direction, confidence, buy_score, sell_score, signals)

        return {
            "status": "READY",
            "direction": direction,
            "confidence": round(confidence, 2),
            "score": round(max(buy_score, sell_score), 2),
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "primary_timeframe": primary_timeframe,
            "aligned_timeframes": aligned,
            "available_timeframes": [signal.timeframe for signal in signals],
            "signals": [signal.__dict__ for signal in signals],
            "snapshot": confluence_snapshot,
        }

    def _timeframe_signal(self, timeframe: str, snapshot: dict[str, Any]) -> TimeframeSignal | None:
        closes = self._floats(snapshot.get("closes", []))
        highs = self._floats(snapshot.get("highs", []))
        lows = self._floats(snapshot.get("lows", []))
        if len(closes) < 2:
            return None

        first_close = closes[0]
        last_close = closes[-1]
        change = last_close - first_close
        range_size = (max(highs) - min(lows)) if highs and lows else abs(change)
        normalized_change = abs(change) / range_size if range_size else 0.0
        confidence = min(95.0, 55.0 + normalized_change * 40.0)

        if change > 0:
            direction = "BUY"
        elif change < 0:
            direction = "SELL"
        else:
            direction = "WAIT"
            confidence = 50.0

        return TimeframeSignal(
            timeframe=timeframe,
            direction=direction,
            confidence=round(confidence, 2),
            change=round(change, 5),
            range_size=round(range_size, 5),
            source=str(snapshot.get("source", "UNKNOWN")),
        )

    def _merge_snapshot(
        self,
        primary_snapshot: dict[str, Any],
        direction: str,
        confidence: float,
        buy_score: float,
        sell_score: float,
        signals: list[TimeframeSignal],
    ) -> dict[str, Any]:
        snapshot = dict(primary_snapshot)
        snapshot["source"] = f"MTF_CONFLUENCE_{primary_snapshot.get('source', 'UNKNOWN')}"
        snapshot["confluence_direction"] = direction
        snapshot["confluence_confidence"] = round(confidence, 2)
        snapshot["confluence_buy_score"] = round(buy_score, 2)
        snapshot["confluence_sell_score"] = round(sell_score, 2)
        snapshot["confluence_timeframes"] = [signal.timeframe for signal in signals]
        return snapshot

    def _select_primary_timeframe(self, snapshots: dict[str, dict[str, Any]]) -> str | None:
        for timeframe in self.PRIMARY_TIMEFRAME_PRIORITY:
            if self._has_ohlc(snapshots.get(timeframe, {})):
                return timeframe
        for timeframe, snapshot in snapshots.items():
            if self._has_ohlc(snapshot):
                return timeframe
        return None

    @staticmethod
    def _has_ohlc(snapshot: dict[str, Any]) -> bool:
        return bool(snapshot and snapshot.get("closes"))

    @staticmethod
    def _floats(values: list[Any]) -> list[float]:
        output = []
        for value in values:
            try:
                output.append(float(value))
            except (TypeError, ValueError):
                continue
        return output
