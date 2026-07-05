"""Portfolio return calculation for production performance attribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PortfolioReturnResult:
    """Portfolio return calculation output."""

    status: str
    ready: bool
    opening_equity: float
    closing_equity: float
    net_profit: float
    return_ratio: float
    return_percent: float
    reason: str


class PortfolioReturn:
    """Calculate portfolio return from opening and closing equity."""

    def calculate(self, portfolio_snapshot: Mapping[str, object] | object) -> PortfolioReturnResult:
        status = str(_read_value(portfolio_snapshot, "status", ""))
        opening_equity = float(_read_value(portfolio_snapshot, "opening_equity", 0.0) or 0.0)
        closing_equity = float(_read_value(portfolio_snapshot, "closing_equity", 0.0) or 0.0)
        net_profit = float(_read_value(portfolio_snapshot, "net_profit", closing_equity - opening_equity) or 0.0)
        if status not in {"PORTFOLIO_EQUITY_READY", "PORTFOLIO_SNAPSHOT_READY", "CAPITAL_ALLOCATION_READY"}:
            return PortfolioReturnResult("PORTFOLIO_RETURN_REVIEW", False, opening_equity, closing_equity, net_profit, 0.0, 0.0, "portfolio_snapshot_not_ready")
        if opening_equity <= 0.0:
            return PortfolioReturnResult("PORTFOLIO_RETURN_REVIEW", False, opening_equity, closing_equity, net_profit, 0.0, 0.0, "opening_equity_not_positive")
        return_ratio = net_profit / opening_equity
        return PortfolioReturnResult(
            status="PORTFOLIO_RETURN_READY",
            ready=True,
            opening_equity=opening_equity,
            closing_equity=closing_equity,
            net_profit=net_profit,
            return_ratio=round(return_ratio, 6),
            return_percent=round(return_ratio * 100.0, 4),
            reason="portfolio_return_calculated",
        )


def _read_value(source: Mapping[str, object] | object, name: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)
