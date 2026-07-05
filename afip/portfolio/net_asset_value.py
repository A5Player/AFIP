"""Net asset value calculation for portfolio equity snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class NetAssetValueResult:
    """Net asset value result normalized for portfolio reporting."""

    status: str
    account_id: str
    net_asset_value: float
    equity: float
    cash_balance: float
    invested_value: float
    reason: str


class NetAssetValueCalculator:
    """Calculate portfolio NAV from cash equity and marked position value."""

    def calculate(
        self,
        equity_snapshot: Mapping[str, object] | object | None,
        position_value: float = 0.0,
    ) -> NetAssetValueResult:
        equity = self._mapping(equity_snapshot)
        if equity.get("status") != "EQUITY_READY":
            return self._review(equity, "equity_snapshot_not_ready")

        cash_balance = self._number(equity.get("equity"))
        invested_value = self._number(position_value)
        nav = round(cash_balance + invested_value, 8)
        return NetAssetValueResult(
            status="NET_ASSET_VALUE_READY",
            account_id=str(equity.get("account_id", "ACCOUNT_UNSPECIFIED")),
            net_asset_value=nav,
            equity=round(cash_balance, 8),
            cash_balance=round(cash_balance, 8),
            invested_value=round(invested_value, 8),
            reason="net_asset_value_ready",
        )

    def _review(self, equity: Mapping[str, object], reason: str) -> NetAssetValueResult:
        return NetAssetValueResult(
            status="NET_ASSET_VALUE_REVIEW",
            account_id=str(equity.get("account_id", "ACCOUNT_UNSPECIFIED")),
            net_asset_value=0.0,
            equity=0.0,
            cash_balance=0.0,
            invested_value=0.0,
            reason=reason,
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "status": getattr(value, "status", ""),
            "account_id": getattr(value, "account_id", ""),
            "equity": getattr(value, "equity", 0.0),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
