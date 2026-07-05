"""Production evidence index for AFIP Production Milestone A Pack 13."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for evidence scoring."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class ProductionEvidenceResult:
    """Evidence score supporting production milestone acceptance."""

    evidence_score: float
    status: str
    action: str
    reason: str


class ProductionEvidenceIndex:
    """Combine test, quality, runtime, and documentation evidence."""

    def evaluate(self, metrics: Mapping[str, float]) -> ProductionEvidenceResult:
        """Return a deterministic production evidence index."""
        test_evidence = _ratio(metrics.get("test_evidence", 0.50))
        quality_evidence = _ratio(metrics.get("quality_evidence", 0.50))
        runtime_evidence = _ratio(metrics.get("runtime_evidence", 0.50))
        documentation_evidence = _ratio(metrics.get("documentation_evidence", 0.50))
        naming_evidence = _ratio(metrics.get("naming_evidence", 0.50))
        evidence_gap = _ratio(metrics.get("evidence_gap", 0.50))

        raw_score = (
            test_evidence * 0.26
            + quality_evidence * 0.22
            + runtime_evidence * 0.20
            + documentation_evidence * 0.16
            + naming_evidence * 0.16
        )
        evidence_score = _ratio(raw_score * (1.0 - evidence_gap * 0.25))

        if evidence_score >= 0.86 and evidence_gap <= 0.16:
            status = "PRODUCTION_EVIDENCE_COMPLETE"
            action = "ACCEPT_MILESTONE_A_EVIDENCE"
            reason = "production_evidence_supports_release_acceptance"
        elif evidence_score >= 0.68:
            status = "PRODUCTION_EVIDENCE_REVIEW"
            action = "CONTINUE_EVIDENCE_REVIEW"
            reason = "production_evidence_requires_additional_review"
        else:
            status = "PRODUCTION_EVIDENCE_INCOMPLETE"
            action = "KEEP_MILESTONE_IN_VALIDATION"
            reason = "production_evidence_below_acceptance_threshold"

        return ProductionEvidenceResult(
            evidence_score=round(evidence_score, 4),
            status=status,
            action=action,
            reason=reason,
        )
