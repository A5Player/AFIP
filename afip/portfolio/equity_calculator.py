"""Equity calculation service for production portfolio accounting."""

from __future__ import annotations

from typing import Mapping

from afip.portfolio.equity_snapshot import EquitySnapshot


class EquityCalculator:
    """Calculate account equity from balance and profit or loss components."""

    def calculate(self, account_snapshot: Mapping[str, object] | None = None) -> EquitySnapshot:
        account = dict(account_snapshot or {})
        balance = self._number(account.get("balance"))
        if balance < 0:
            return self._review(account, "negative_balance_not_allowed")

        realized_pnl = self._number(account.get("realized_pnl", 0.0))
        unrealized_pnl = self._number(account.get("unrealized_pnl", account.get("floating_pnl", 0.0)))
        equity = round(balance + realized_pnl + unrealized_pnl, 8)
        if equity < 0:
            return EquitySnapshot(
                status="EQUITY_REVIEW",
                account_id=str(account.get("account_id", "ACCOUNT_UNSPECIFIED")),
                balance=round(balance, 8),
                realized_pnl=round(realized_pnl, 8),
                unrealized_pnl=round(unrealized_pnl, 8),
                equity=equity,
                net_asset_value=0.0,
                reason="negative_equity_not_allowed",
            )

        return EquitySnapshot(
            status="EQUITY_READY",
            account_id=str(account.get("account_id", "ACCOUNT_UNSPECIFIED")),
            balance=round(balance, 8),
            realized_pnl=round(realized_pnl, 8),
            unrealized_pnl=round(unrealized_pnl, 8),
            equity=equity,
            net_asset_value=equity,
            reason="equity_calculation_ready",
        )

    def _review(self, account: Mapping[str, object], reason: str) -> EquitySnapshot:
        return EquitySnapshot(
            status="EQUITY_REVIEW",
            account_id=str(account.get("account_id", "ACCOUNT_UNSPECIFIED")),
            balance=max(0.0, self._number(account.get("balance"))),
            realized_pnl=self._number(account.get("realized_pnl", 0.0)),
            unrealized_pnl=self._number(account.get("unrealized_pnl", account.get("floating_pnl", 0.0))),
            equity=0.0,
            net_asset_value=0.0,
            reason=reason,
        )

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
