from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping

from .intelligence import ResearchIntelligence


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
            for path in sorted((self.root / "trade_cases").glob("*.json"))
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
            eligible_exits = [
                exit_ for exit_ in exits
                if isinstance(exit_, Mapping)
                and exit_.get("research_feedback_status") == "ELIGIBLE"
                and exit_.get("net_realized_profit_usd") not in (None, "")
            ]
            quarantined_exits = [
                exit_ for exit_ in exits
                if isinstance(exit_, Mapping)
                and exit_.get("research_feedback_status") == "QUARANTINED"
            ]
            completed_exits = eligible_exits
            profits = [_number(exit_.get("net_realized_profit_usd")) for exit_ in completed_exits]
            wins = sum(value > 0 for value in profits)
            gross_profit = sum(max(value, 0.0) for value in profits)
            gross_loss = abs(sum(min(value, 0.0) for value in profits))
            completed = len(profits)
            losses = completed - wins
            net_profit = sum(profits)
            average_profit = mean(profits) if profits else 0.0
            expectancy = average_profit if completed else None
            profit_factor = (gross_profit / gross_loss) if gross_loss else (None if completed == 0 else gross_profit)
            equity = 0.0
            peak = 0.0
            maximum_drawdown = 0.0
            for value in profits:
                equity += value
                peak = max(peak, equity)
                maximum_drawdown = max(maximum_drawdown, peak - equity)
            rows.append({
                "pattern_id": pattern_id,
                "occurrences": len(items),
                "completed_trades": completed,
                "wins": wins,
                "losses": losses,
                "win_rate": round((wins / completed * 100.0), 2) if completed else None,
                "gross_profit": round(gross_profit, 2),
                "gross_loss": round(gross_loss, 2),
                "net_profit": round(net_profit, 2),
                "average_profit": round(average_profit, 2) if completed else None,
                "expectancy": round(expectancy, 2) if expectancy is not None else None,
                "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
                "maximum_drawdown": round(maximum_drawdown, 2) if completed else None,
                "average_holding": round(mean([_number(x.get("holding_seconds")) for x in completed_exits]) if completed_exits else 0.0, 2),
                "average_mfe": round(mean([_number(x.get("mfe")) for x in completed_exits]) if completed_exits else 0.0, 2),
                "average_mae": round(mean([_number(x.get("mae")) for x in completed_exits]) if completed_exits else 0.0, 2),
                "average_exit_quality": round(mean([_number(x.get("exit_quality")) for x in completed_exits]) if completed_exits else 0.0, 2),
                "eligible_feedback_count": len(eligible_exits),
                "quarantined_feedback_count": len(quarantined_exits),
                "statistics_status": "AVAILABLE" if completed else "INSUFFICIENT_ELIGIBLE_COMPLETED_TRADES",
                "research_only": True,
                "affects_trading": False,
            })
        rows.sort(key=lambda row: (row["profit_factor"] if row["profit_factor"] is not None else -1.0, row["win_rate"] if row["win_rate"] is not None else -1.0, row["occurrences"], row["pattern_id"]), reverse=True)
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
        intelligence = ResearchIntelligence(self.root)
        cluster_rows = intelligence.cluster_rows(cases)
        closed = sum(1 for case in cases if str(case.get("lifecycle_state", "")).startswith(("CLOSED", "COMPLETE")))
        active = len(cases) - closed
        unknown = sum(1 for case in cases if _pattern_id(case) == "UNKNOWN")
        malformed = sum(1 for case in cases if not case.get("trade_case_id") or not case.get("data_lineage"))
        case_ids = [str(case.get("trade_case_id", "")) for case in cases if case.get("trade_case_id")]
        duplicate_case_count = len(case_ids) - len(set(case_ids))
        closed_cases = [case for case in cases if case.get("exit_context")]
        eligible_closed = [case for case in closed_cases if case.get("exit_context", {}).get("research_feedback_status") == "ELIGIBLE"]
        quarantined_closed = [case for case in closed_cases if case.get("exit_context", {}).get("research_feedback_status") == "QUARANTINED"]
        regimes = {
            str(case.get("market_context", {}).get("market_regime") or case.get("market_context", {}).get("regime") or "UNKNOWN")
            for case in eligible_closed
        }
        regimes.discard("UNKNOWN")
        eligible_patterns = [row for row in rows if row.get("eligible_feedback_count", 0) > 0]
        sample_ready_patterns = [row for row in rows if row.get("eligible_feedback_count", 0) >= 30]
        blockers = []
        if malformed:
            blockers.append("malformed_trade_cases")
        if duplicate_case_count:
            blockers.append("duplicate_trade_case_ids")
        if unknown:
            blockers.append("unknown_pattern_cases")
        if not eligible_closed:
            blockers.append("no_eligible_closed_trade_feedback")
        dataset_health = "READY" if malformed == 0 and duplicate_case_count == 0 else "CAUTION"
        ranking_status = "READY_FOR_RESEARCH_RANKING" if sample_ready_patterns and not blockers else "NOT_READY_FOR_AUTOMATIC_RANKING"
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
                "duplicate_trade_case_id_count": duplicate_case_count,
                "eligible_closed_trade_count": len(eligible_closed),
                "quarantined_closed_trade_count": len(quarantined_closed),
                "eligible_pattern_count": len(eligible_patterns),
                "sample_ready_pattern_count": len(sample_ready_patterns),
                "eligible_market_regime_count": len(regimes),
                "eligible_market_regimes": sorted(regimes),
                "lineage_coverage_percent": round(((len(cases) - malformed) / len(cases) * 100.0) if cases else 100.0, 2),
                "certification_blockers": blockers,
            },
            "ranking_readiness": {
                "status": ranking_status,
                "minimum_eligible_sample_per_pattern": 30,
                "eligible_feedback_only": True,
                "uses_net_realized_profit_after_costs": True,
                "quarantined_feedback_excluded": True,
                "automatic_ranking_mutation": False,
                "research_only": True,
                "affects_trading": False,
            },
            "lifecycle_states": dict(sorted(lifecycle.items())),
            "pending_checkpoints": {name: due_or_pending.get(name, 0) for name in ("M15", "M30", "H1", "H4", "D1")},
            "checkpoint_status_counts": dict(sorted(checkpoint_counts.items())),
            "pattern_statistics": rows,
            "top_100_patterns": rows[:100],
            "research_clusters": cluster_rows,
            "top_100_research_clusters": cluster_rows[:100],
            "research_cluster_policy": "PROFILE_INDEPENDENT_PATTERN_REGIME_SESSION_TIMEFRAME_CONTEXT",
        }
