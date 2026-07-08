"""Production acceptance test observation contract for Production Freeze Pack P2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionAcceptanceTestObservation:
    """Normalized production scenario evidence for deterministic acceptance review."""

    market_regime: str
    signal_context: str
    execution_mode: str
    scenario_type: str
    spread_quality_score: float
    margin_quality_score: float
    data_continuity_score: float
    engine_agreement_score: float
    confidence_quality_score: float
    risk_gate_score: float
    decision_consistency_score: float
    blocked_execution_events: int
    unresolved_scenarios: int
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionAcceptanceTestObservation":
        return cls(
            market_regime=str(value.get("market_regime", "")).strip().upper(),
            signal_context=str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN",
            execution_mode=_mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY"))),
            scenario_type=str(value.get("scenario_type", value.get("scenario", "GENERAL"))).strip().upper() or "GENERAL",
            spread_quality_score=_ratio(value.get("spread_quality_score", value.get("spread_score", 0.0))),
            margin_quality_score=_ratio(value.get("margin_quality_score", value.get("margin_score", 0.0))),
            data_continuity_score=_ratio(value.get("data_continuity_score", value.get("data_quality_score", 0.0))),
            engine_agreement_score=_ratio(value.get("engine_agreement_score", value.get("agreement_score", 0.0))),
            confidence_quality_score=_ratio(value.get("confidence_quality_score", value.get("confidence_score", 0.0))),
            risk_gate_score=_ratio(value.get("risk_gate_score", value.get("risk_score", 0.0))),
            decision_consistency_score=_ratio(value.get("decision_consistency_score", value.get("consistency_score", 0.0))),
            blocked_execution_events=_count(value.get("blocked_execution_events", value.get("blocked_events", 0))),
            unresolved_scenarios=_count(value.get("unresolved_scenarios", value.get("open_scenarios", 0))),
            source=str(value.get("source", "PRODUCTION_ACCEPTANCE_TEST")).strip().upper() or "PRODUCTION_ACCEPTANCE_TEST",
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def scenario_quality(self) -> float:
        value = (
            self.spread_quality_score * 0.13
            + self.margin_quality_score * 0.13
            + self.data_continuity_score * 0.16
            + self.engine_agreement_score * 0.15
            + self.confidence_quality_score * 0.13
            + self.risk_gate_score * 0.15
            + self.decision_consistency_score * 0.15
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def execution_control_quality(self) -> float:
        penalty = min((self.blocked_execution_events * 0.05) + (self.unresolved_scenarios * 0.20), 1.0)
        return round(1.0 - penalty, 6)

    @property
    def acceptance_score(self) -> float:
        value = self.scenario_quality * 0.84 + self.execution_control_quality * 0.16
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
