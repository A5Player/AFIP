"""Research-only exit experiment aggregation and evidence evaluation."""
from .runtime import (
    ContextSegment,
    EvidenceEvaluation,
    EvidenceObservation,
    ExitEvidenceResearchEngine,
    PolicyComparison,
    SegmentEvidenceSummary,
)
from .a16_evidence import A16ExitObservation, A16PolicyRanking, rank_a16_policies
from .a16_bridge import outcome_to_a16_evidence

__all__ = [
    "ContextSegment",
    "EvidenceEvaluation",
    "EvidenceObservation",
    "ExitEvidenceResearchEngine",
    "PolicyComparison",
    "SegmentEvidenceSummary",
    "A16ExitObservation",
    "A16PolicyRanking",
    "rank_a16_policies",
    "outcome_to_a16_evidence",
]
