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
from .a18_observability import A18ResearchRuntimeStatus, A18ResearchObservability
from .a20_holding_exit import (
    A20HoldingExitObservation,
    A20HoldingExitRanking,
    A20HoldingExitResearch,
)
from .a21_holding_exit_producer import (
    A21HoldingBucket,
    A21HoldingExitEvidenceProducer,
    A21ProductionResult,
)

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
    "A18ResearchRuntimeStatus",
    "A18ResearchObservability",
    "A20HoldingExitObservation",
    "A20HoldingExitRanking",
    "A20HoldingExitResearch",
    "A21HoldingBucket",
    "A21HoldingExitEvidenceProducer",
    "A21ProductionResult",
]
