"""Version 1 production freeze runtime for Production Freeze Pack P6."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .freeze_observation import Version1FreezeObservation
from .freeze_policy import Version1FreezePolicy
from .freeze_profile import Version1FreezeProfile
from .freeze_report import Version1FreezeReport
from .freeze_repository import Version1FreezeRepository


class Version1FreezeRuntime:
    """Evaluates final release readiness without changing trading decisions."""

    def __init__(
        self, policy: Version1FreezePolicy | None = None, repository: Version1FreezeRepository | None = None
    ) -> None:
        self.policy = policy or Version1FreezePolicy()
        self.repository = repository or Version1FreezeRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> Version1FreezeProfile:
        observation = Version1FreezeObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = Version1FreezeProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[Version1FreezeProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> Version1FreezeReport:
        return Version1FreezeReport(self.evaluate_one(record))
