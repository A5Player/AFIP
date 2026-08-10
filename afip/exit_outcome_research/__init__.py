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
]
