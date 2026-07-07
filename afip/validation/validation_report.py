"""Validation report contract."""

from __future__ import annotations

from dataclasses import dataclass

from .validation_policy import ValidationDecision
from .validation_profile import ValidationProfile


@dataclass(frozen=True)
class ValidationReport:
    """Serializable validation report."""

    decision: ValidationDecision
    profiles: tuple[ValidationProfile, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.decision.status,
            "ready": self.decision.status == "VALIDATION_READY",
            "profile_count": len(self.profiles),
            "decision": self.decision.as_dict(),
            "profiles": [item.as_dict() for item in self.profiles],
            "architecture": {
                "market_regime_before_signal_context": True,
                "data_first_architecture": True,
                "knowledge_first_architecture": True,
                "deterministic_runtime": True,
                "production_write_allowed": False,
                "validation_before_production_readiness": True,
            },
        }
