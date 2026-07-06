"""Production Milestone E Pack 4 confidence calibration runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .calibration_policy import ConfidenceCalibrationPolicy
from .calibration_report import ConfidenceCalibrationReport
from .calibration_repository import ConfidenceCalibrationRepository


class ConfidenceCalibrationRuntime:
    """Build deterministic confidence calibration from regime-first observations."""

    def __init__(self, policy: ConfidenceCalibrationPolicy | None = None) -> None:
        self.policy = policy or ConfidenceCalibrationPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> ConfidenceCalibrationReport:
        repository = ConfidenceCalibrationRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return ConfidenceCalibrationReport.from_profiles(profiles, decision)
