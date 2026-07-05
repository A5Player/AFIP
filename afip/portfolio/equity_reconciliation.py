"""Equity reconciliation controls for production portfolio accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class EquityReconciliationResult:
    """Equity reconciliation outcome for portfolio runtime controls."""

    status: str
    reconciled: bool
    account_id: str
    equity: float
    net_asset_value: float
    failed_rules: tuple[str, ...]
    reason: str


class EquityReconciliation:
    """Validate equity and NAV against configured portfolio limits."""

    def evaluate(
        self,
        equity_snapshot: Mapping[str, object] | object | None,
        nav_result: Mapping[str, object] | object | None,
        limits: Mapping[str, object] | None = None,
    ) -> EquityReconciliationResult:
        equity = self._mapping(equity_snapshot)
        nav = self._mapping(nav_result)
        limit_config = dict(limits or {})
        failed: list[str] = []

        if equity.get("status") != "EQUITY_READY":
            failed.append("equity_snapshot_not_ready")
        if nav.get("status") != "NET_ASSET_VALUE_READY":
            failed.append("net_asset_value_not_ready")

        equity_value = self._number(equity.get("equity"))
        nav_value = self._number(nav.get("net_asset_value"))
        minimum_equity = self._number(limit_config.get("minimum_equity", 0.0))
        maximum_nav_to_equity = self._number(limit_config.get("maximum_nav_to_equity_ratio", 10.0)) or 10.0

        if equity_value < minimum_equity:
            failed.append("minimum_equity_not_met")
        if equity_value > 0 and abs(nav_value / equity_value) > maximum_nav_to_equity:
            failed.append("net_asset_value_ratio_exceeded")

        status = "EQUITY_RECONCILIATION_READY" if not failed else "EQUITY_RECONCILIATION_REVIEW"
        return EquityReconciliationResult(
            status=status,
            reconciled=not failed,
            account_id=str(equity.get("account_id", nav.get("account_id", "ACCOUNT_UNSPECIFIED"))),
            equity=round(equity_value, 8),
            net_asset_value=round(nav_value, 8),
            failed_rules=tuple(failed),
            reason="equity_reconciled" if not failed else "equity_reconciliation_requires_review",
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
            "net_asset_value": getattr(value, "net_asset_value", 0.0),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
