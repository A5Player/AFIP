"""Production operations report for Production Freeze Pack P4."""

from __future__ import annotations

from dataclasses import asdict

from .operations_profile import ProductionOperationsProfile


class ProductionOperationsReport:
    """Human-readable deployment and operations readiness report."""

    def __init__(self, profile: ProductionOperationsProfile) -> None:
        self.profile = profile

    def as_dict(self) -> dict[str, object]:
        data = asdict(self.profile)
        data["operations_gate"] = self.profile.operations_gate
        return data

    def as_text(self) -> str:
        return (
            "Production Operations Report\n"
            f"Status: {self.profile.status}\n"
            f"Gate: {self.profile.operations_gate}\n"
            f"Market regime: {self.profile.market_regime}\n"
            f"Signal context: {self.profile.signal_context}\n"
            f"Deployment score: {self.profile.deployment_score:.4f}\n"
            f"Operations score: {self.profile.operations_score:.4f}\n"
            f"Decision reason: {self.profile.reason}"
        )
