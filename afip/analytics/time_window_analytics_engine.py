"""Time window analytics for weekday and hour performance review."""
from __future__ import annotations

from collections import defaultdict

from afip.analytics._common import AnalyticsResult, safe_divide


class TimeWindowAnalyticsEngine:
    """Rank trading windows by profitability and sample quality."""

    name = "TimeWindowAnalyticsEngine"

    def evaluate(self, trades: list[dict], minimum_samples: int = 1) -> dict:
        windows: dict[str, dict] = defaultdict(lambda: {"trades": 0, "wins": 0, "profit": 0.0})
        for trade in trades or []:
            weekday = str(trade.get("weekday", "NA")).upper()
            hour = int(trade.get("hour", 0) or 0)
            key = f"{weekday}:{hour:02d}"
            profit = float(trade.get("profit", 0.0) or 0.0)
            windows[key]["trades"] += 1
            windows[key]["wins"] += 1 if profit > 0 else 0
            windows[key]["profit"] = round(windows[key]["profit"] + profit, 2)
        ranked = []
        for key, item in windows.items():
            if item["trades"] < minimum_samples:
                continue
            win_rate = round(safe_divide(item["wins"] * 100.0, item["trades"]), 2)
            score = round(item["profit"] + win_rate * 0.25 + min(10, item["trades"]), 2)
            ranked.append({"window": key, "score": score, "win_rate": win_rate, **item})
        ranked.sort(key=lambda item: (-item["score"], item["window"]))
        status = "READY" if ranked else "NO_DATA"
        overall_score = ranked[0]["score"] if ranked else 0.0
        return AnalyticsResult(self.name, status, overall_score, "time_windows_ready" if ranked else "no_qualified_windows", {
            "top_windows": ranked[:10],
            "qualified_windows": len(ranked),
        }).as_dict()
