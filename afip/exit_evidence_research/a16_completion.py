"""Append-only A16 research completion pipeline; never promotes or executes."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Iterable

from afip.historical_replay_research import AppendOnlyResearchDataset
from .a16_evidence import A16ExitObservation, A16PolicyRanking, rank_a16_policies
from .a16_report import A16ResearchReport, build_a16_research_report

@dataclass(frozen=True)
class A16ResearchCertification:
    status: str
    reason: str
    observation_count: int
    ranking_count: int
    append_only_verified: bool
    read_only: bool = True
    execution_authority: str = "NONE"
    automatic_promotion_allowed: bool = False
    def as_dict(self) -> dict[str, object]: return asdict(self)

class A16ResearchCompletion:
    def __init__(self, dataset: AppendOnlyResearchDataset, minimum_sample_size: int = 30) -> None:
        self.dataset = dataset
        self.minimum_sample_size = minimum_sample_size

    def record_and_report(self, observations: Iterable[A16ExitObservation]) -> tuple[A16ResearchReport, A16ResearchCertification]:
        values = tuple(observations)
        for item in values:
            self.dataset.append("a16_exit_evidence_observations", item.as_dict())
        rankings = rank_a16_policies(values, self.minimum_sample_size) if values else ()
        for item in rankings:
            self.dataset.append("a16_exit_policy_rankings", asdict(item))
        report = build_a16_research_report(rankings)
        certification = A16ResearchCertification(
            status="READY" if rankings else "WAIT",
            reason="research_ranking_available" if rankings else "minimum_research_sample_not_met",
            observation_count=len(values), ranking_count=len(rankings),
            append_only_verified=all(self.dataset.verify(name) for name in ("a16_exit_evidence_observations", "a16_exit_policy_rankings")),
        )
        self.dataset.append("a16_exit_research_certifications", certification.as_dict())
        return report, certification
