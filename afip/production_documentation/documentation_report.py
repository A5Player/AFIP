"""Production documentation report for Production Freeze Pack P3."""

from __future__ import annotations

from dataclasses import asdict

from .documentation_profile import ProductionDocumentationProfile


class ProductionDocumentationReport:
    """Human-readable documentation readiness report."""

    def __init__(self, profile: ProductionDocumentationProfile) -> None:
        self.profile = profile

    def as_dict(self) -> dict[str, object]:
        data = asdict(self.profile)
        data["documentation_gate"] = self.profile.documentation_gate
        return data

    def as_text(self) -> str:
        return (
            "Production Documentation Report\n"
            f"Status: {self.profile.status}\n"
            f"Gate: {self.profile.documentation_gate}\n"
            f"Market regime: {self.profile.market_regime}\n"
            f"Signal context: {self.profile.signal_context}\n"
            f"Coverage score: {self.profile.coverage_score:.4f}\n"
            f"Documentation score: {self.profile.documentation_score:.4f}\n"
            f"Decision reason: {self.profile.reason}"
        )
