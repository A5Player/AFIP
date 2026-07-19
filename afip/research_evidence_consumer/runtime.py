"""Read-only research evidence lookup for runtime decision support."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class EvidenceQuery:
    pattern_id: str
    market_regime: str
    session: str
    volatility_band: str
    trading_cost_band: str

class EvidenceConsumer:
    def __init__(self, records: Iterable[Mapping[str, Any]]) -> None:
        self._records = tuple(dict(record) for record in records)

    def query(self, request: EvidenceQuery) -> dict[str, Any]:
        matches = []
        for record in self._records:
            if record.get("evidence_status") not in {"CERTIFIED", "CERTIFIED_CANDIDATE"}:
                continue
            if (
                record.get("pattern_id") == request.pattern_id
                and record.get("market_regime") == request.market_regime
                and record.get("session") == request.session
                and record.get("volatility_band") == request.volatility_band
                and record.get("trading_cost_band") == request.trading_cost_band
            ):
                matches.append(record)
        matches.sort(key=lambda row: (-float(row.get("ranking_score", 0.0)), str(row.get("research_id", ""))))
        if not matches:
            return {
                "status": "NO_CERTIFIED_EVIDENCE",
                "comparable_cases": 0,
                "execution_permission": False,
                "evidence": None,
            }
        best = matches[0]
        return {
            "status": "CERTIFIED_EVIDENCE_AVAILABLE",
            "comparable_cases": int(best.get("trade_count", 0)),
            "execution_permission": False,
            "evidence": {
                "research_id": best.get("research_id"),
                "expected_win_rate_percentage": best.get("win_rate_percentage"),
                "expected_maximum_drawdown_percentage": best.get("maximum_drawdown_percentage"),
                "expected_expectancy": best.get("expectancy"),
                "preferred_entry_method": best.get("entry_method"),
                "preferred_protection_method": best.get("protection_method"),
                "preferred_profit_method": best.get("profit_method"),
                "ranking_score": best.get("ranking_score"),
            },
        }
