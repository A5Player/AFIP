from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _pattern_id(case: Mapping[str, Any]) -> str:
    market = case.get("market_context", {})
    if not isinstance(market, Mapping):
        return "UNKNOWN"
    return str(market.get("pattern_id") or market.get("pattern") or "UNKNOWN")


class ResearchDatasetAggregator:
    """Deterministic, read-only aggregation for the AFIP research dashboard."""

    def __init__(self, root: Path | str = Path("runtime/research")) -> None:
        self.root = Path(root)

    def cases(self) -> list[dict[str, Any]]:
        return [
            case
            for path in sorted((self.root / "trade_cases").glob("CASE-*.json"))
            if (case := _read_json(path))
        ]

    @staticmethod
    def _pattern_rows(cases: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for case in cases:
            grouped[_pattern_id(case)].append(case)
        rows: list[dict[str, Any]] = []
        for pattern_id, items in grouped.items():
            exits = [item.get("exit_context", {}) for item in items]
            profits = [_number(exit_.get("net_profit")) for exit_ in exits if isinstance(exit_, Mapping)]
            wins = sum(value > 0 for value in profits)
            gross_profit = sum(max(value, 0.0) for value in profits)
            gross_loss = abs(sum(min(value, 0.0) for value in profits))
            completed = len(profits)
            rows.append({
                "pattern_id": pattern_id,
                "occurrences": len(items),
                "completed_trades": completed,
                "win_rate": round((wins / completed * 100.0) if completed else 0.0, 2),
                "profit_factor": round((gross_profit / gross_loss) if gross_loss else gross_profit, 2),
                "average_holding": round(mean([_number(x.get("holding_seconds")) for x in exits]) if exits else 0.0, 2),
                "average_mfe": round(mean([_number(x.get("mfe")) for x in exits]) if exits else 0.0, 2),
                "average_mae": round(mean([_number(x.get("mae")) for x in exits]) if exits else 0.0, 2),
                "average_exit_quality": round(mean([_number(x.get("exit_quality")) for x in exits]) if exits else 0.0, 2),
                "research_only": True,
                "affects_trading": False,
            })
        rows.sort(key=lambda row: (row["profit_factor"], row["win_rate"], row["occurrences"], row["pattern_id"]), reverse=True)
        return rows

    def build(self) -> dict[str, Any]:
        cases = self.cases()
        lifecycle = Counter(str(case.get("lifecycle_state", "UNKNOWN")) for case in cases)
        checkpoint_counts = Counter()
        due_or_pending = Counter()
        for case in cases:
            checkpoints = case.get("post_trade_checkpoints", {})
            if not isinstance(checkpoints, Mapping):
                continue
            for name, item in checkpoints.items():
                status = str(item.get("status", "PENDING")) if isinstance(item, Mapping) else "PENDING"
                checkpoint_counts[f"{name}:{status}"] += 1
                if status != "COMPLETED":
                    due_or_pending[str(name)] += 1
        rows = self._pattern_rows(cases)
        closed = sum(1 for case in cases if str(case.get("lifecycle_state", "")).startswith(("CLOSED", "COMPLETE")))
        active = len(cases) - closed
        unknown = sum(1 for case in cases if _pattern_id(case) == "UNKNOWN")
        malformed = sum(1 for case in cases if not case.get("trade_case_id") or not case.get("data_lineage"))
        dataset_health = "READY" if malformed == 0 else "CAUTION"
        return {
            "status": "READY",
            "research_only": True,
            "affects_trading": False,
            "dataset_health": {
                "status": dataset_health,
                "trade_case_count": len(cases),
                "active_lifecycle_count": active,
                "closed_case_count": closed,
                "unknown_pattern_count": unknown,
                "malformed_case_count": malformed,
                "lineage_coverage_percent": round(((len(cases) - malformed) / len(cases) * 100.0) if cases else 100.0, 2),
            },
            "lifecycle_states": dict(sorted(lifecycle.items())),
            "pending_checkpoints": {name: due_or_pending.get(name, 0) for name in ("M15", "M30", "H1", "H4", "D1")},
            "checkpoint_status_counts": dict(sorted(checkpoint_counts.items())),
            "pattern_statistics": rows,
            "top_100_patterns": rows[:100],
        }
