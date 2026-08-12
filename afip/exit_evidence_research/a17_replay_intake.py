"""A17 historical replay intake for A16 evidence; research-only and append-only."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from afip.exit_outcome_research import A16ExitResearchRunner, A16PolicySet, A16ResearchContext
from afip.exit_outcome_research.runtime import ExitPolicyExperimentRunner, PositionResearchCase
from afip.historical_replay_research import AppendOnlyResearchDataset

from .a16_bridge import outcome_to_a16_evidence
from .a16_completion import A16ResearchCertification, A16ResearchCompletion
from .a16_evidence import A16ExitObservation
from .a16_report import A16ResearchReport


@dataclass(frozen=True)
class A17ReplayIntakeRun:
    position_case_id: str
    plan_id: str
    policy_count: int
    observation_count: int
    status: str
    future_data_used: bool = False
    research_only: bool = True
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class A17ReplayResearchIntake:
    """Connect existing chronological exit replay to A16 evidence collection.

    The class has no broker imports and only writes the existing append-only
    research datasets.  It never selects, promotes, sends, modifies or closes
    an order.
    """

    def __init__(self, dataset: AppendOnlyResearchDataset, minimum_sample_size: int = 30) -> None:
        if minimum_sample_size <= 0:
            raise ValueError("minimum sample size must be positive")
        self.dataset = dataset
        self.minimum_sample_size = minimum_sample_size

    def intake(
        self,
        *,
        case: PositionResearchCase,
        policy_set: A16PolicySet,
        candles: Iterable[object],
        context: A16ResearchContext,
        execution_cost_r: float,
    ) -> tuple[tuple[A16ExitObservation, ...], A16ResearchReport, A16ResearchCertification]:
        if execution_cost_r < 0:
            raise ValueError("execution cost cannot be negative")
        if not context.plan_id.strip():
            raise ValueError("research context plan id is required")
        values = tuple(candles)
        if not values:
            raise ValueError("chronological replay candles are required")

        outcomes = A16ExitResearchRunner(ExitPolicyExperimentRunner(self.dataset)).run(
            case=case, policy_set=policy_set, candles=values,
        )
        observations = tuple(
            outcome_to_a16_evidence(
                outcome=outcome.as_dict(), context=context, execution_cost_r=execution_cost_r,
            )
            for outcome in outcomes
        )
        for observation in observations:
            self.dataset.append("a16_exit_evidence_observations", observation.as_dict())
        completion = A16ResearchCompletion(self.dataset, self.minimum_sample_size)
        report, certification = completion.rank_recorded_evidence()
        run = A17ReplayIntakeRun(
            position_case_id=case.position_case_id,
            plan_id=context.plan_id,
            policy_count=len(outcomes),
            observation_count=len(observations),
            status=certification.status,
        )
        self.dataset.append("a17_exit_replay_intake_runs", run.as_dict())
        return observations, report, certification
