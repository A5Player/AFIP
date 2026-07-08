"""Production documentation observation contract for Production Freeze Pack P3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionDocumentationObservation:
    """Normalized documentation readiness evidence for deterministic review."""

    market_regime: str
    signal_context: str
    execution_mode: str
    architecture_coverage_score: float
    runtime_flow_coverage_score: float
    installation_coverage_score: float
    configuration_coverage_score: float
    recovery_coverage_score: float
    troubleshooting_coverage_score: float
    thai_manual_score: float
    english_manual_score: float
    unresolved_documentation_items: int
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionDocumentationObservation":
        return cls(
            market_regime=str(value.get("market_regime", "")).strip().upper(),
            signal_context=str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN",
            execution_mode=_mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY"))),
            architecture_coverage_score=_ratio(value.get("architecture_coverage_score", value.get("architecture_score", 0.0))),
            runtime_flow_coverage_score=_ratio(value.get("runtime_flow_coverage_score", value.get("runtime_score", 0.0))),
            installation_coverage_score=_ratio(value.get("installation_coverage_score", value.get("installation_score", 0.0))),
            configuration_coverage_score=_ratio(value.get("configuration_coverage_score", value.get("configuration_score", 0.0))),
            recovery_coverage_score=_ratio(value.get("recovery_coverage_score", value.get("recovery_score", 0.0))),
            troubleshooting_coverage_score=_ratio(value.get("troubleshooting_coverage_score", value.get("troubleshooting_score", 0.0))),
            thai_manual_score=_ratio(value.get("thai_manual_score", value.get("thai_score", 0.0))),
            english_manual_score=_ratio(value.get("english_manual_score", value.get("english_score", 0.0))),
            unresolved_documentation_items=_count(value.get("unresolved_documentation_items", value.get("open_items", 0))),
            source=str(value.get("source", "PRODUCTION_DOCUMENTATION")).strip().upper() or "PRODUCTION_DOCUMENTATION",
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def coverage_score(self) -> float:
        value = (
            self.architecture_coverage_score * 0.16
            + self.runtime_flow_coverage_score * 0.14
            + self.installation_coverage_score * 0.12
            + self.configuration_coverage_score * 0.12
            + self.recovery_coverage_score * 0.12
            + self.troubleshooting_coverage_score * 0.12
            + self.thai_manual_score * 0.11
            + self.english_manual_score * 0.11
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def completeness_score(self) -> float:
        penalty = min(self.unresolved_documentation_items * 0.15, 1.0)
        return round(1.0 - penalty, 6)

    @property
    def documentation_score(self) -> float:
        value = self.coverage_score * 0.82 + self.completeness_score * 0.18
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
