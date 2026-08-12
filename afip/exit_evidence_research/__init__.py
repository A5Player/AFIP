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
from .a16_report import A16ResearchReport, build_a16_research_report
from .a16_completion import A16ResearchCertification, A16ResearchCompletion
from .a17_replay_intake import A17ReplayIntakeRun, A17ReplayResearchIntake

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
    "A16ResearchReport",
    "build_a16_research_report",
    "A16ResearchCertification",
    "A16ResearchCompletion",
    "A17ReplayIntakeRun",
    "A17ReplayResearchIntake",
]
