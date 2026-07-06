"""COMEX gold inventory assessment for supply availability context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ComexInventoryAssessment:
    """COMEX inventory assessment for gold supply pressure context."""

    status: str
    inventory_state: str
    confidence_score: float
    registered_change: float
    eligible_change: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "inventory_state": self.inventory_state,
            "confidence_score": self.confidence_score,
            "registered_change": self.registered_change,
            "eligible_change": self.eligible_change,
            "reason": self.reason,
        }


class ComexInventoryRuntime:
    """Interpret COMEX registered and eligible inventory changes."""

    def assess(self, values: Mapping[str, object]) -> ComexInventoryAssessment:
        registered_change = self._to_float(values.get("comex_registered_change"))
        eligible_change = self._to_float(values.get("comex_eligible_change"))
        total_change = registered_change + eligible_change
        confidence = min(90.0, 44.0 + abs(total_change) * 4.0)

        if registered_change <= -2.5:
            state = "AVAILABLE_SUPPLY_TIGHTENING"
            reason = "registered_inventory_contracting"
        elif registered_change >= 2.5:
            state = "AVAILABLE_SUPPLY_EXPANDING"
            reason = "registered_inventory_expanding"
        else:
            state = "INVENTORY_BALANCED"
            confidence = 43.0
            reason = "comex_inventory_balanced"

        return ComexInventoryAssessment(
            status="COMEX_INVENTORY_READY",
            inventory_state=state,
            confidence_score=round(confidence, 2),
            registered_change=round(registered_change, 2),
            eligible_change=round(eligible_change, 2),
            reason=reason,
        )

    def assess_dict(self, values: Mapping[str, object]) -> dict[str, object]:
        return self.assess(values).as_dict()

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
