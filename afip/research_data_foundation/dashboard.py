from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


class ResearchDashboardSnapshot:
    """Read-only dashboard projection for Pack 5.2 research artifacts."""

    def __init__(self, root: Path | str = Path("runtime/research")) -> None:
        self.root = Path(root)

    def build(self, record: Mapping[str, Any] | None = None) -> dict[str, Any]:
        record = dict(record or {})
        cases = [_json(path, {}) for path in sorted((self.root / "trade_cases").glob("CASE-*.json"))]
        replay = _json(self.root / "replay" / "replay_statistics.json", {})
        queue = _json(self.root / "replay" / "replay_queue.json", {"jobs": []}).get("jobs", [])
        patterns: dict[str, list[dict[str, Any]]] = {}
        for case in cases:
            pattern = str(case.get("market_context", {}).get("pattern_id") or case.get("market_context", {}).get("pattern") or "UNKNOWN")
            patterns.setdefault(pattern, []).append(case)
        rows = []
        for pattern, items in patterns.items():
            profits = [float(item.get("exit_context", {}).get("net_profit", 0.0) or 0.0) for item in items]
            wins = sum(value > 0 for value in profits)
            gross_profit = sum(max(0.0, value) for value in profits)
            gross_loss = abs(sum(min(0.0, value) for value in profits))
            rows.append({"pattern_id": pattern, "occurrences": len(items), "win_rate": round(wins / len(items) * 100, 2),
                         "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else round(gross_profit, 2),
                         "average_holding": round(sum(float(i.get("exit_context", {}).get("holding_seconds", 0) or 0) for i in items) / len(items), 2),
                         "average_mfe": round(sum(float(i.get("exit_context", {}).get("mfe", 0) or 0) for i in items) / len(items), 2),
                         "average_mae": round(sum(float(i.get("exit_context", {}).get("mae", 0) or 0) for i in items) / len(items), 2),
                         "average_exit_quality": round(sum(float(i.get("exit_context", {}).get("exit_quality", 0) or 0) for i in items) / len(items), 2)})
        rows.sort(key=lambda item: (item["profit_factor"], item["win_rate"], item["occurrences"]), reverse=True)
        active = next((item for item in queue if item.get("status") == "RUNNING"), None)
        return {"historical_data": {"coverage": record.get("historical_coverage", "UNKNOWN"), "start_date": record.get("historical_start_date", "UNKNOWN"),
                    "end_date": record.get("historical_end_date", "UNKNOWN"), "candle_count": int(record.get("historical_candle_count", 0) or 0),
                    "tick_count": int(record.get("historical_tick_count", 0) or 0), "missing_data": int(record.get("historical_missing_data", 0) or 0),
                    "data_quality": record.get("historical_data_quality", "UNKNOWN")},
                "replay": {**replay, "active_replay": active.get("replay_id") if active else "NONE", "replay_speed": record.get("replay_speed", "RECORDER_ONLY")},
                "dataset": {"trade_case_count": len(cases), "pattern_count": len(patterns), "unknown_pattern_count": len(patterns.get("UNKNOWN", [])),
                    "historical_simulations": int(replay.get("completed", 0) or 0), "recorded_decisions": int(replay.get("decisions_recorded", 0) or 0),
                    "recorded_exits": int(replay.get("exits_recorded", 0) or 0)}, "top_100_patterns": rows[:100],
                "similar_pattern_monitor": {"research_only": True, "similarity_percent": record.get("similarity_percent", 0),
                    "similar_pattern_id": record.get("similar_pattern_id", "NONE"), "historical_occurrences": record.get("similar_pattern_occurrences", 0),
                    "historical_win_rate": record.get("similar_pattern_win_rate", 0), "historical_profit_factor": record.get("similar_pattern_profit_factor", 0),
                    "affects_trading": False}}
