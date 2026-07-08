"""Production acceptance test report for Production Freeze Pack P2."""

from __future__ import annotations

from dataclasses import dataclass

from .acceptance_profile import ProductionAcceptanceTestProfile


@dataclass(frozen=True)
class ProductionAcceptanceTestReport:
    profile: ProductionAcceptanceTestProfile

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.profile.market_regime,
            "signal_context": self.profile.signal_context,
            "execution_mode": self.profile.execution_mode,
            "scenario_type": self.profile.scenario_type,
            "scenario_quality": self.profile.scenario_quality,
            "execution_control_quality": self.profile.execution_control_quality,
            "acceptance_score": self.profile.acceptance_score,
            "acceptance_gate": self.profile.acceptance_gate,
            "status": self.profile.status,
            "reason": self.profile.reason,
        }

    def as_text(self) -> str:
        return "\n".join([
            "Production Acceptance Test Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Execution mode: {self.profile.execution_mode}",
            f"Scenario type: {self.profile.scenario_type}",
            f"Acceptance gate: {self.profile.acceptance_gate}",
            f"Scenario quality: {self.profile.scenario_quality:.4f}",
            f"Execution control quality: {self.profile.execution_control_quality:.4f}",
            f"Acceptance score: {self.profile.acceptance_score:.4f}",
            f"Decision reason: {self.profile.reason}",
        ])
