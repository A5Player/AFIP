"""Trade distribution analytics by symbol, action, and session."""
from __future__ import annotations

from collections import defaultdict

from afip.analytics._common import AnalyticsResult


class TradeDistributionEngine:
    """Aggregate trade outcomes into practical review buckets."""

    name = "TradeDistributionEngine"

    def evaluate(self, trades: list[dict]) -> dict:
        if not trades:
            return AnalyticsResult(self.name, "NO_DATA", 0.0, "no_trades", {"buckets": {}, "largest_bucket": None}).as_dict()
        buckets: dict[str, dict] = defaultdict(lambda: {"count": 0, "profit": 0.0})
        for trade in trades:
            symbol = str(trade.get("symbol", "UNKNOWN")).upper()
            action = str(trade.get("action", "UNKNOWN")).upper()
            session = str(trade.get("session", "UNKNOWN")).upper()
            key = f"{symbol}:{action}:{session}"
            buckets[key]["count"] += 1
            buckets[key]["profit"] = round(buckets[key]["profit"] + float(trade.get("profit", 0.0) or 0.0), 2)
        normalized = dict(sorted(buckets.items(), key=lambda item: (-item[1]["count"], item[0])))
        largest = next(iter(normalized), None)
        profitable = sum(1 for item in normalized.values() if item["profit"] > 0)
        score = 50.0 + min(30.0, profitable * 5.0) + min(20.0, len(normalized) * 2.0)
        return AnalyticsResult(self.name, "READY", score, "trade_distribution_ready", {
            "buckets": normalized,
            "largest_bucket": largest,
            "bucket_count": len(normalized),
        }).as_dict()
