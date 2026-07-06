"""Deterministic research platform runtime for Milestone C Pack 14."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .research_dataset import ResearchDataset, ResearchSample
from .research_hypothesis import ResearchHypothesis


@dataclass(frozen=True)
class ResearchRuntimeState:
    status: str
    reason: str
    dataset: dict[str, object]
    hypothesis_results: list[dict[str, object]]
    best_result: dict[str, object] | None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "dataset": self.dataset,
            "hypothesis_results": self.hypothesis_results,
            "best_result": self.best_result,
        }


@dataclass(frozen=True)
class ResearchPlatformRuntime:
    hypothesis: ResearchHypothesis = ResearchHypothesis()

    def run(self, samples: Iterable[ResearchSample]) -> ResearchRuntimeState:
        dataset = ResearchDataset()
        dataset.extend(samples)
        dataset_dict = dataset.as_dict()
        if dataset_dict["sample_count"] == 0:
            return ResearchRuntimeState(
                status="RESEARCH_DATA_REQUIRED",
                reason="no_research_samples",
                dataset=dataset_dict,
                hypothesis_results=[],
                best_result=None,
            )

        results = [self.hypothesis.evaluate(group).as_dict() for group in dataset.group_summary()]
        results.sort(key=lambda item: (-float(item["score"]), str(item["regime_first_key"])))
        ready = [item for item in results if item["status"] == "RESEARCH_REVIEW_READY"]
        status = "RESEARCH_PLATFORM_READY" if ready else "RESEARCH_OBSERVATION_MODE"
        reason = "research_review_ready" if ready else "no_research_group_ready"
        return ResearchRuntimeState(
            status=status,
            reason=reason,
            dataset=dataset_dict,
            hypothesis_results=results,
            best_result=results[0] if results else None,
        )
