"""Production architecture audit report for Production Freeze Pack P1."""

from __future__ import annotations

from dataclasses import dataclass

from .audit_profile import ProductionArchitectureAuditProfile


@dataclass(frozen=True)
class ProductionArchitectureAuditReport:
    profile: ProductionArchitectureAuditProfile

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.profile.market_regime,
            "signal_context": self.profile.signal_context,
            "execution_mode": self.profile.execution_mode,
            "architecture_quality": self.profile.architecture_quality,
            "finding_quality": self.profile.finding_quality,
            "audit_score": self.profile.audit_score,
            "audit_gate": self.profile.audit_gate,
            "status": self.profile.status,
            "reason": self.profile.reason,
        }

    def as_text(self) -> str:
        return "\n".join([
            "Production Architecture Audit Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Execution mode: {self.profile.execution_mode}",
            f"Audit gate: {self.profile.audit_gate}",
            f"Architecture quality: {self.profile.architecture_quality:.4f}",
            f"Finding quality: {self.profile.finding_quality:.4f}",
            f"Audit score: {self.profile.audit_score:.4f}",
            f"Decision reason: {self.profile.reason}",
        ])
