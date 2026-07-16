from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .aggregator import ResearchDatasetAggregator


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
        aggregate = ResearchDatasetAggregator(self.root).build()
        rows = list(aggregate["top_100_patterns"])
        active = next((item for item in queue if item.get("status") == "RUNNING"), None)
        return {"historical_data": {"coverage": record.get("historical_coverage", "UNKNOWN"), "start_date": record.get("historical_start_date", "UNKNOWN"),
                    "end_date": record.get("historical_end_date", "UNKNOWN"), "candle_count": int(record.get("historical_candle_count", 0) or 0),
                    "tick_count": int(record.get("historical_tick_count", 0) or 0), "missing_data": int(record.get("historical_missing_data", 0) or 0),
                    "data_quality": record.get("historical_data_quality", "UNKNOWN")},
                "replay": {**replay, "active_replay": active.get("replay_id") if active else "NONE", "replay_speed": record.get("replay_speed", "RECORDER_ONLY")},
                "dataset": {"trade_case_count": len(cases), "pattern_count": len(aggregate["pattern_statistics"]), "unknown_pattern_count": aggregate["dataset_health"]["unknown_pattern_count"],
                    "historical_simulations": int(replay.get("completed", 0) or 0), "recorded_decisions": int(replay.get("decisions_recorded", 0) or 0),
                    "recorded_exits": int(replay.get("exits_recorded", 0) or 0)}, "top_100_patterns": rows,
                "dataset_health": aggregate["dataset_health"], "lifecycle_states": aggregate["lifecycle_states"],
                "pending_checkpoints": aggregate["pending_checkpoints"],
                "similar_pattern_monitor": {"research_only": True, "similarity_percent": record.get("similarity_percent", 0),
                    "similar_pattern_id": record.get("similar_pattern_id", "NONE"), "historical_occurrences": record.get("similar_pattern_occurrences", 0),
                    "historical_win_rate": record.get("similar_pattern_win_rate", 0), "historical_profit_factor": record.get("similar_pattern_profit_factor", 0),
                    "affects_trading": False}}
