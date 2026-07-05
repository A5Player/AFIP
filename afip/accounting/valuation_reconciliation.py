"""Valuation reconciliation controls for mark-to-market accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ValuationReconciliationResult:
    """Production control result for position valuation and unrealized PnL."""

    status: str
    reconciled: bool
    pnl_limit_ratio: float
    absolute_return_ratio: float
    failed_rules: tuple[str, ...]
    reason: str


class ValuationReconciliation:
    """Validate valuation readiness and unrealized return limits."""

    def evaluate(
        self,
        valuation_snapshot: Mapping[str, object] | object | None,
        pnl_snapshot: Mapping[str, object] | object | None,
        limits: Mapping[str, object] | None = None,
    ) -> ValuationReconciliationResult:
        valuation = self._mapping(valuation_snapshot)
        pnl = self._mapping(pnl_snapshot)
        controls = limits or {}
        pnl_limit_ratio = self._number(controls.get("maximum_absolute_return_ratio", 0.25))
        failed: list[str] = []
        if valuation.get("status") != "POSITION_VALUATION_READY":
            failed.append("position_valuation_not_ready")
        if pnl.get("status") != "UNREALIZED_PNL_READY":
            failed.append("unrealized_pnl_not_ready")
        absolute_return_ratio = abs(self._number(pnl.get("return_ratio", 0.0)))
        if pnl_limit_ratio >= 0 and absolute_return_ratio > pnl_limit_ratio:
            failed.append("unrealized_return_limit_exceeded")
        reconciled = not failed
        return ValuationReconciliationResult(
            status="VALUATION_RECONCILIATION_READY" if reconciled else "VALUATION_RECONCILIATION_REVIEW",
            reconciled=reconciled,
            pnl_limit_ratio=round(pnl_limit_ratio, 8),
            absolute_return_ratio=round(absolute_return_ratio, 8),
            failed_rules=tuple(failed),
            reason="valuation_reconciled" if reconciled else "valuation_requires_review",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "status": getattr(value, "status", ""),
            "return_ratio": getattr(value, "return_ratio", 0.0),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
