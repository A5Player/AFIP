"""Exposure reconciliation checks for position ledger snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ExposureReconciliationResult:
    """Exposure reconciliation result for production controls."""

    status: str
    reconciled: bool
    exposure_ratio: float
    net_quantity: float
    maximum_quantity: float
    failed_rules: tuple[str, ...]
    reason: str


class ExposureReconciliation:
    """Validate ledger exposure against production accounting limits."""

    def evaluate(
        self,
        ledger_snapshot: Mapping[str, object] | object | None = None,
        exposure_limits: Mapping[str, object] | None = None,
    ) -> ExposureReconciliationResult:
        ledger = self._mapping(ledger_snapshot)
        limits = dict(exposure_limits or {})
        net_quantity = abs(self._number(ledger.get("net_quantity", 0.0)))
        maximum_quantity = self._number(limits.get("maximum_net_quantity", 1.0))
        if maximum_quantity <= 0:
            maximum_quantity = 1.0
        exposure_ratio = round(net_quantity / maximum_quantity, 8)
        failed: list[str] = []
        if str(ledger.get("status", "")) != "POSITION_LEDGER_READY":
            failed.append("position_ledger_not_ready")
        if exposure_ratio > 1.0:
            failed.append("net_quantity_limit_exceeded")

        if failed:
            return ExposureReconciliationResult(
                status="EXPOSURE_RECONCILIATION_REVIEW",
                reconciled=False,
                exposure_ratio=exposure_ratio,
                net_quantity=round(net_quantity, 8),
                maximum_quantity=round(maximum_quantity, 8),
                failed_rules=tuple(failed),
                reason=";".join(failed),
            )

        return ExposureReconciliationResult(
            status="EXPOSURE_RECONCILIATION_READY",
            reconciled=True,
            exposure_ratio=exposure_ratio,
            net_quantity=round(net_quantity, 8),
            maximum_quantity=round(maximum_quantity, 8),
            failed_rules=(),
            reason="ledger_exposure_within_limits",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "status": getattr(value, "status", ""),
            "net_quantity": getattr(value, "net_quantity", 0.0),
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
