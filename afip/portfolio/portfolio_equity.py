"""Portfolio equity summary builder for production portfolio state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class PortfolioEquitySummary:
    """Aggregated equity summary across account snapshots."""

    status: str
    account_count: int
    total_balance: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    total_equity: float
    total_net_asset_value: float
    reason: str


class PortfolioEquity:
    """Aggregate account-level equity snapshots into a portfolio summary."""

    def summarize(self, snapshots: Iterable[Mapping[str, object] | object]) -> PortfolioEquitySummary:
        normalized = [self._mapping(snapshot) for snapshot in snapshots]
        ready = [snapshot for snapshot in normalized if snapshot.get("status") == "EQUITY_READY"]
        if not ready:
            return PortfolioEquitySummary(
                status="PORTFOLIO_EQUITY_REVIEW",
                account_count=0,
                total_balance=0.0,
                total_realized_pnl=0.0,
                total_unrealized_pnl=0.0,
                total_equity=0.0,
                total_net_asset_value=0.0,
                reason="no_ready_equity_snapshots",
            )

        total_balance = sum(self._number(item.get("balance")) for item in ready)
        total_realized = sum(self._number(item.get("realized_pnl")) for item in ready)
        total_unrealized = sum(self._number(item.get("unrealized_pnl")) for item in ready)
        total_equity = sum(self._number(item.get("equity")) for item in ready)
        total_nav = sum(self._number(item.get("net_asset_value", item.get("equity"))) for item in ready)
        return PortfolioEquitySummary(
            status="PORTFOLIO_EQUITY_READY",
            account_count=len(ready),
            total_balance=round(total_balance, 8),
            total_realized_pnl=round(total_realized, 8),
            total_unrealized_pnl=round(total_unrealized, 8),
            total_equity=round(total_equity, 8),
            total_net_asset_value=round(total_nav, 8),
            reason="portfolio_equity_ready",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object) -> dict[str, object]:
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "status": getattr(value, "status", ""),
            "balance": getattr(value, "balance", 0.0),
            "realized_pnl": getattr(value, "realized_pnl", 0.0),
            "unrealized_pnl": getattr(value, "unrealized_pnl", 0.0),
            "equity": getattr(value, "equity", 0.0),
            "net_asset_value": getattr(value, "net_asset_value", getattr(value, "equity", 0.0)),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
