"""Milestone C Pack 15 learning foundation runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any

from .learning_governor import LearningGovernor
from .learning_observation import LearningObservation
from .learning_profile import LearningProfileRepository


@dataclass(frozen=True)
class LearningFoundationState:
    status: str
    reason: str
    repository: dict[str, object]
    governance_results: list[dict[str, object]]
    best_result: dict[str, object] | None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "repository": self.repository,
            "governance_results": self.governance_results,
            "best_result": self.best_result,
        }


@dataclass(frozen=True)
class LearningFoundationRuntime:
    governor: LearningGovernor = LearningGovernor()

    def run(self, observations: Iterable[LearningObservation | Mapping[str, Any]]) -> LearningFoundationState:
        repository = LearningProfileRepository(observations)
        repository_dict = repository.as_dict()
        if repository_dict["observation_count"] == 0:
            return LearningFoundationState(
                status="LEARNING_DATA_REQUIRED",
                reason="no_learning_observations",
                repository=repository_dict,
                governance_results=[],
                best_result=None,
            )

        results = [self.governor.evaluate(profile.as_dict()).as_dict() for profile in repository.profiles()]
        results.sort(key=lambda item: (-float(item["score"]), str(item["regime_first_key"])))
        ready = [item for item in results if item["status"] == "LEARNING_UPDATE_READY"]
        return LearningFoundationState(
            status="LEARNING_FOUNDATION_READY" if ready else "LEARNING_OBSERVATION_MODE",
            reason="learning_update_candidates_ready" if ready else "no_learning_profile_ready",
            repository=repository_dict,
            governance_results=results,
            best_result=results[0] if results else None,
        )
