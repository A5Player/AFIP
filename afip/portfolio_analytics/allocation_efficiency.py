"""Capital allocation efficiency analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class AllocationEfficiencyResult:
    """Allocation efficiency analytics output."""

    status: str
    ready: bool
    allocated_capital: float
    available_capital: float
    utilization_percent: float
    efficiency_status: str
    reason: str


class AllocationEfficiency:
    """Evaluate how efficiently available portfolio capital is allocated."""

    def calculate(self, capital_snapshot: Mapping[str, object] | object) -> AllocationEfficiencyResult:
        capital_status = str(_read_value(capital_snapshot, "status", ""))
        allocated = float(_read_value(capital_snapshot, "allocated_capital", 0.0) or 0.0)
        available = float(_read_value(capital_snapshot, "available_capital", 0.0) or 0.0)
        if capital_status not in {"CAPITAL_ALLOCATION_READY", "PRODUCTION_MILESTONE_B_CAPITAL_READY"}:
            return AllocationEfficiencyResult("ALLOCATION_EFFICIENCY_REVIEW", False, allocated, available, 0.0, "REVIEW", "capital_snapshot_not_ready")
        if available <= 0:
            return AllocationEfficiencyResult("ALLOCATION_EFFICIENCY_REVIEW", False, allocated, available, 0.0, "REVIEW", "available_capital_not_positive")
        utilization = round(allocated / available * 100.0, 4)
        if utilization < 40.0:
            efficiency = "UNDER_ALLOCATED"
        elif utilization > 90.0:
            efficiency = "OVER_ALLOCATED"
        else:
            efficiency = "BALANCED"
        return AllocationEfficiencyResult("ALLOCATION_EFFICIENCY_READY", True, allocated, available, utilization, efficiency, "allocation_efficiency_ready")


def _read_value(source: Mapping[str, object] | object, name: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)
