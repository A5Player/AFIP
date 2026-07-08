"""Version 1 production freeze profile for Production Freeze Pack P6."""

from __future__ import annotations

from dataclasses import dataclass

from .freeze_observation import Version1FreezeObservation


@dataclass(frozen=True)
class Version1FreezeProfile:
    """Deterministic final release profile for AFIP Version 1."""

    market_regime: str
    signal_context: str
    status: str
    reason: str
    release_version: str
    architecture_audit_status: str
    acceptance_test_status: str
    documentation_status: str
    operations_status: str
    walk_forward_status: str
    release_candidate_status: str
    unresolved_release_items: int
    deterministic_runtime_score: float
    backward_compatibility_score: float
    documentation_coverage_score: float
    operations_readiness_score: float
    walk_forward_standard_score: float
    final_quality_score: float
    release_score: float
    source: str

    @classmethod
    def from_observation(
        cls, observation: Version1FreezeObservation, *, status: str, reason: str
    ) -> "Version1FreezeProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            status=status,
            reason=reason,
            release_version=observation.release_version,
            architecture_audit_status=observation.architecture_audit_status,
            acceptance_test_status=observation.acceptance_test_status,
            documentation_status=observation.documentation_status,
            operations_status=observation.operations_status,
            walk_forward_status=observation.walk_forward_status,
            release_candidate_status=observation.release_candidate_status,
            unresolved_release_items=observation.unresolved_release_items,
            deterministic_runtime_score=observation.deterministic_runtime_score,
            backward_compatibility_score=observation.backward_compatibility_score,
            documentation_coverage_score=observation.documentation_coverage_score,
            operations_readiness_score=observation.operations_readiness_score,
            walk_forward_standard_score=observation.walk_forward_standard_score,
            final_quality_score=observation.final_quality_score,
            release_score=observation.release_score,
            source=observation.source,
        )

    @property
    def freeze_gate(self) -> str:
        if self.status == "READY":
            return "VERSION1_PRODUCTION_FREEZE_READY"
        if self.status == "REVIEW":
            return "REVIEW_REQUIRED"
        return "BLOCKED"
