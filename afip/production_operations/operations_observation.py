"""Production operations observation contract for Production Freeze Pack P4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionOperationsObservation:
    """Normalized deployment and operations readiness evidence."""

    market_regime: str
    signal_context: str
    execution_mode: str
    vps_readiness_score: float
    mt5_readiness_score: float
    startup_readiness_score: float
    backup_readiness_score: float
    restore_readiness_score: float
    rollback_readiness_score: float
    operations_checklist_score: float
    monitoring_readiness_score: float
    unresolved_operations_items: int
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionOperationsObservation":
        return cls(
            market_regime=str(value.get("market_regime", "")).strip().upper(),
            signal_context=str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN",
            execution_mode=_mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY"))),
            vps_readiness_score=_ratio(value.get("vps_readiness_score", value.get("vps_score", 0.0))),
            mt5_readiness_score=_ratio(value.get("mt5_readiness_score", value.get("mt5_score", 0.0))),
            startup_readiness_score=_ratio(value.get("startup_readiness_score", value.get("startup_score", 0.0))),
            backup_readiness_score=_ratio(value.get("backup_readiness_score", value.get("backup_score", 0.0))),
            restore_readiness_score=_ratio(value.get("restore_readiness_score", value.get("restore_score", 0.0))),
            rollback_readiness_score=_ratio(value.get("rollback_readiness_score", value.get("rollback_score", 0.0))),
            operations_checklist_score=_ratio(value.get("operations_checklist_score", value.get("checklist_score", 0.0))),
            monitoring_readiness_score=_ratio(value.get("monitoring_readiness_score", value.get("monitoring_score", 0.0))),
            unresolved_operations_items=_count(value.get("unresolved_operations_items", value.get("open_items", 0))),
            source=str(value.get("source", "PRODUCTION_OPERATIONS")).strip().upper() or "PRODUCTION_OPERATIONS",
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def deployment_score(self) -> float:
        value = (
            self.vps_readiness_score * 0.15
            + self.mt5_readiness_score * 0.15
            + self.startup_readiness_score * 0.12
            + self.backup_readiness_score * 0.12
            + self.restore_readiness_score * 0.12
            + self.rollback_readiness_score * 0.12
            + self.operations_checklist_score * 0.12
            + self.monitoring_readiness_score * 0.10
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def resolution_score(self) -> float:
        penalty = min(self.unresolved_operations_items * 0.15, 1.0)
        return round(1.0 - penalty, 6)

    @property
    def operations_score(self) -> float:
        value = self.deployment_score * 0.84 + self.resolution_score * 0.16
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _count(value: Any) -> int:
    return max(int(value), 0)


def _mode(value: Any) -> str:
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    return text or "LOCKED_SIMULATION_ONLY"
