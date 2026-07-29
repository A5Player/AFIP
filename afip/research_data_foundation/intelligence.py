from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping

UNKNOWN = "UNKNOWN"


def _text(value: Any, default: str = UNKNOWN) -> str:
    value = str(value or "").strip().upper()
    return value or default


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _context(case: Mapping[str, Any]) -> Mapping[str, Any]:
    value = case.get("market_context", {})
    return value if isinstance(value, Mapping) else {}


def research_dimensions(case: Mapping[str, Any]) -> dict[str, str]:
    """Canonical, profile-independent research dimensions."""
    market = _context(case)
    return {
        "symbol": _text(case.get("symbol")),
        "pattern_id": _text(market.get("pattern_id") or market.get("pattern")),
        "pattern_family": _text(market.get("pattern_family") or market.get("family")),
        "market_regime": _text(market.get("market_regime") or market.get("regime")),
        "session": _text(market.get("session") or market.get("market_session")),
        "timeframe": _text(market.get("timeframe") or market.get("primary_timeframe")),
        "trend_context": _text(market.get("trend_context") or market.get("trend")),
        "volatility_regime": _text(market.get("volatility_regime") or market.get("volatility")),
        "decision_action": _text(case.get("decision_action")),
    }


def research_cluster_id(case: Mapping[str, Any]) -> str:
    dims = research_dimensions(case)
    canonical = "|".join(f"{key}={dims[key]}" for key in sorted(dims))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16].upper()
    return f"RC-{digest}"


def completed_profit(case: Mapping[str, Any]) -> float | None:
    exit_context = case.get("exit_context", {})
    if not isinstance(exit_context, Mapping):
        return None
    for key in ("net_profit", "realized_profit", "profit_retained", "profit"):
        if exit_context.get(key) not in (None, ""):
            return _number(exit_context.get(key))
    return None


@dataclass(frozen=True)
class SimilarityResult:
    status: str
    query_cluster_id: str
    matched_trade_case_id: str
    matched_cluster_id: str
    similarity_percent: float
    historical_occurrences: int
    completed_trades: int
    win_rate: float | None
    profit_factor: float | None
    dimensions_compared: int
    exact_dimensions: tuple[str, ...]
    differing_dimensions: tuple[str, ...]
    research_only: bool = True
    affects_trading: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchIntelligence:
    """Read-only research clustering and similarity. Never imported by execution."""

    DIMENSION_WEIGHTS = {
        "symbol": 2.0,
        "pattern_id": 4.0,
        "pattern_family": 2.5,
        "market_regime": 3.0,
        "session": 1.5,
        "timeframe": 2.0,
        "trend_context": 2.0,
        "volatility_regime": 2.0,
        "decision_action": 2.0,
    }

    def __init__(self, root: Path | str = Path("runtime/research")) -> None:
        self.root = Path(root)

    def cases(self) -> list[dict[str, Any]]:
        rows = []
        for path in sorted((self.root / "trade_cases").glob("*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if isinstance(value, dict):
                rows.append(value)
        return rows

    @classmethod
    def similarity(cls, left: Mapping[str, Any], right: Mapping[str, Any]) -> tuple[float, tuple[str, ...], tuple[str, ...]]:
        a, b = research_dimensions(left), research_dimensions(right)
        total = matched = 0.0
        exact, differing = [], []
        for key, weight in cls.DIMENSION_WEIGHTS.items():
            if a[key] == UNKNOWN and b[key] == UNKNOWN:
                continue
            total += weight
            if a[key] == b[key]:
                matched += weight
                exact.append(key)
            else:
                differing.append(key)
        return (round((matched / total * 100.0) if total else 0.0, 2), tuple(exact), tuple(differing))

    @staticmethod
    def _statistics(cases: Iterable[Mapping[str, Any]]) -> tuple[int, int, float | None, float | None]:
        items = list(cases)
        profits = [value for case in items if (value := completed_profit(case)) is not None]
        wins = sum(value > 0 for value in profits)
        gross_profit = sum(max(value, 0.0) for value in profits)
        gross_loss = abs(sum(min(value, 0.0) for value in profits))
        return len(items), len(profits), (round(wins / len(profits) * 100.0, 2) if profits else None), (round(gross_profit / gross_loss, 2) if gross_loss else (gross_profit if profits else None))

    def cluster_rows(self, cases: Iterable[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for case in list(cases) if cases is not None else self.cases():
            grouped[research_cluster_id(case)].append(case)
        rows = []
        for cluster_id, items in grouped.items():
            occurrences, completed, win_rate, profit_factor = self._statistics(items)
            profits = [value for case in items if (value := completed_profit(case)) is not None]
            rows.append({
                "research_cluster_id": cluster_id,
                "dimensions": research_dimensions(items[0]),
                "occurrences": occurrences,
                "completed_trades": completed,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "net_profit": round(sum(profits), 2),
                "average_profit": round(mean(profits), 2) if profits else None,
                "statistics_status": "AVAILABLE" if completed else "INSUFFICIENT_COMPLETED_TRADES",
                "profile_independent": True,
                "research_only": True,
                "affects_trading": False,
            })
        rows.sort(key=lambda row: (row["completed_trades"], row["profit_factor"] if row["profit_factor"] is not None else -1.0, row["win_rate"] if row["win_rate"] is not None else -1.0, row["occurrences"]), reverse=True)
        return rows

    def nearest(self, query: Mapping[str, Any], *, exclude_trade_case_id: str = "") -> dict[str, Any]:
        cases = [case for case in self.cases() if str(case.get("trade_case_id", "")) != exclude_trade_case_id]
        if not cases:
            return SimilarityResult("NO_REFERENCE_CASE", research_cluster_id(query), "", "", 0.0, 0, 0, None, None, 0, (), ()).as_dict()
        ranked = []
        for case in cases:
            score, exact, differing = self.similarity(query, case)
            ranked.append((score, str(case.get("trade_case_id", "")), case, exact, differing))
        score, case_id, matched, exact, differing = max(ranked, key=lambda item: (item[0], item[1]))
        cluster = research_cluster_id(matched)
        members = [case for case in cases if research_cluster_id(case) == cluster]
        occurrences, completed, win_rate, profit_factor = self._statistics(members)
        return SimilarityResult("READY", research_cluster_id(query), case_id, cluster, score, occurrences, completed, win_rate, profit_factor, len(exact) + len(differing), exact, differing).as_dict()
