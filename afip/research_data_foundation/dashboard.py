from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .aggregator import ResearchDatasetAggregator
from .intelligence import ResearchIntelligence


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
        cluster_rows = list(aggregate.get("top_100_research_clusters", ()))
        similarity = ResearchIntelligence(self.root).nearest(record.get("current_market_case", {})) if record.get("current_market_case") else {"status": "NO_CURRENT_MARKET_CASE", "research_only": True, "affects_trading": False}
        active = next((item for item in queue if item.get("status") == "RUNNING"), None)
        closed = [case for case in cases if case.get("exit_context")]
        eligible = [case for case in closed if case.get("exit_context", {}).get("research_feedback_status") == "ELIGIBLE"]
        quarantined = [case for case in closed if case.get("exit_context", {}).get("research_feedback_status") == "QUARANTINED"]
        net_total = round(sum(float(case.get("exit_context", {}).get("net_realized_profit_usd", 0.0) or 0.0) for case in closed), 8)
        r_values = [float(case.get("exit_context", {}).get("realized_r_multiple")) for case in eligible if case.get("exit_context", {}).get("realized_r_multiple") is not None]
        exit_efficiencies = [float(case.get("exit_context", {}).get("exit_efficiency_ratio")) for case in eligible if case.get("exit_context", {}).get("exit_efficiency_ratio") is not None]
        outcome_feedback = {
            "closed_trade_count": len(closed),
            "eligible_feedback_count": len(eligible),
            "quarantined_feedback_count": len(quarantined),
            "net_realized_profit_usd": net_total,
            "average_realized_r_multiple": round(sum(r_values) / len(r_values), 8) if r_values else None,
            "average_exit_efficiency_ratio": round(sum(exit_efficiencies) / len(exit_efficiencies), 8) if exit_efficiencies else None,
            "wins": sum(1 for case in closed if case.get("exit_context", {}).get("outcome_class") == "WIN"),
            "losses": sum(1 for case in closed if case.get("exit_context", {}).get("outcome_class") == "LOSS"),
            "breakeven": sum(1 for case in closed if case.get("exit_context", {}).get("outcome_class") == "BREAKEVEN"),
            "research_only": True,
            "affects_trading": False,
        }
        return {"historical_data": {"coverage": record.get("historical_coverage", "UNKNOWN"), "start_date": record.get("historical_start_date", "UNKNOWN"),
                    "end_date": record.get("historical_end_date", "UNKNOWN"), "candle_count": int(record.get("historical_candle_count", 0) or 0),
                    "tick_count": int(record.get("historical_tick_count", 0) or 0), "missing_data": int(record.get("historical_missing_data", 0) or 0),
                    "data_quality": record.get("historical_data_quality", "UNKNOWN")},
                "replay": {**replay, "active_replay": active.get("replay_id") if active else "NONE", "replay_speed": record.get("replay_speed", "RECORDER_ONLY")},
                "dataset": {"trade_case_count": len(cases), "pattern_count": len(aggregate["pattern_statistics"]), "unknown_pattern_count": aggregate["dataset_health"]["unknown_pattern_count"],
                    "historical_simulations": int(replay.get("completed", 0) or 0), "recorded_decisions": int(replay.get("decisions_recorded", 0) or 0),
                    "recorded_exits": int(replay.get("exits_recorded", 0) or 0)}, "top_100_patterns": rows,
                "dataset_health": aggregate["dataset_health"], "ranking_readiness": aggregate.get("ranking_readiness", {}), "lifecycle_states": aggregate["lifecycle_states"],
                "pending_checkpoints": aggregate["pending_checkpoints"],
                "research_clusters": cluster_rows,
                "research_cluster_policy": aggregate.get("research_cluster_policy"),
                "closed_trade_outcome_feedback": outcome_feedback,
                "similar_pattern_monitor": similarity}
