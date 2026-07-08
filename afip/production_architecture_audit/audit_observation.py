"""Production architecture audit observation contract for Production Freeze Pack P1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionArchitectureAuditObservation:
    """Normalized architecture evidence for deterministic production review."""

    market_regime: str
    signal_context: str
    execution_mode: str
    module_boundary_score: float
    dependency_alignment_score: float
    runtime_flow_score: float
    configuration_score: float
    naming_score: float
    documentation_trace_score: float
    duplicate_logic_findings: int
    circular_dependency_findings: int
    unresolved_findings: int
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionArchitectureAuditObservation":
        return cls(
            market_regime=str(value.get("market_regime", "")).strip().upper(),
            signal_context=str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN",
            execution_mode=_mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY"))),
            module_boundary_score=_ratio(value.get("module_boundary_score", 0.0)),
            dependency_alignment_score=_ratio(value.get("dependency_alignment_score", 0.0)),
            runtime_flow_score=_ratio(value.get("runtime_flow_score", 0.0)),
            configuration_score=_ratio(value.get("configuration_score", 0.0)),
            naming_score=_ratio(value.get("naming_score", 0.0)),
            documentation_trace_score=_ratio(value.get("documentation_trace_score", value.get("traceability_score", 0.0))),
            duplicate_logic_findings=_count(value.get("duplicate_logic_findings", 0)),
            circular_dependency_findings=_count(value.get("circular_dependency_findings", 0)),
            unresolved_findings=_count(value.get("unresolved_findings", value.get("open_findings", 0))),
            source=str(value.get("source", "PRODUCTION_ARCHITECTURE_AUDIT")).strip().upper() or "PRODUCTION_ARCHITECTURE_AUDIT",
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def architecture_quality(self) -> float:
        value = (
            self.module_boundary_score * 0.20
            + self.dependency_alignment_score * 0.20
            + self.runtime_flow_score * 0.18
            + self.configuration_score * 0.14
            + self.naming_score * 0.14
            + self.documentation_trace_score * 0.14
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def finding_quality(self) -> float:
        total = self.duplicate_logic_findings + self.circular_dependency_findings + self.unresolved_findings
        if total <= 0:
            return 1.0
        penalty = min(total * 0.18, 1.0)
        return round(1.0 - penalty, 6)

    @property
    def audit_score(self) -> float:
        value = self.architecture_quality * 0.82 + self.finding_quality * 0.18
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
