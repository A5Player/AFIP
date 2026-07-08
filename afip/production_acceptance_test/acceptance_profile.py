"""Production acceptance test profile for Production Freeze Pack P2."""

from __future__ import annotations

from dataclasses import dataclass

from .acceptance_observation import ProductionAcceptanceTestObservation


@dataclass(frozen=True)
class ProductionAcceptanceTestProfile:
    market_regime: str
    signal_context: str
    execution_mode: str
    scenario_type: str
    scenario_quality: float
    execution_control_quality: float
    acceptance_score: float
    blocked_execution_events: int
    unresolved_scenarios: int
    status: str
    reason: str

    @classmethod
    def from_observation(
        cls,
        observation: ProductionAcceptanceTestObservation,
        *,
        status: str,
        reason: str,
    ) -> "ProductionAcceptanceTestProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            execution_mode=observation.execution_mode,
            scenario_type=observation.scenario_type,
            scenario_quality=observation.scenario_quality,
            execution_control_quality=observation.execution_control_quality,
            acceptance_score=observation.acceptance_score,
            blocked_execution_events=observation.blocked_execution_events,
            unresolved_scenarios=observation.unresolved_scenarios,
            status=status,
            reason=reason,
        )

    @property
    def acceptance_gate(self) -> str:
        if self.status == "READY":
            return "PRODUCTION_ACCEPTANCE_READY"
        if self.status == "BLOCKED":
            return "BLOCKED"
        return "REVIEW_REQUIRED"
