"""Research-only exit, loss-control, and position-outcome engine."""
from .runtime import (
    ExitAlternativeRecord,
    ExitOutcomeResearchEngine,
    ExitPolicyExperimentRunner,
    ExitResearchPolicy,
    PositionOutcome,
    PositionResearchCase,
)
from .a16_contract import A16ResearchContext, candidate_policy_ids, validate_advisory_record
from .a16_core import A16ExitResearchRunner, A16PolicySet
from .a16_r_ladder import RLadderProposal, RLadderResearch

__all__ = [
    "ExitAlternativeRecord",
    "ExitOutcomeResearchEngine",
    "ExitPolicyExperimentRunner",
    "ExitResearchPolicy",
    "PositionOutcome",
    "PositionResearchCase",
    "A16ResearchContext",
    "candidate_policy_ids",
    "validate_advisory_record",
    "A16ExitResearchRunner",
    "A16PolicySet",
    "RLadderProposal",
    "RLadderResearch",
]
