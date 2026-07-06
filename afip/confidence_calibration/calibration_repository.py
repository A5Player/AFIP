"""Production Milestone E Pack 4 confidence calibration repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .calibration_observation import ConfidenceCalibrationObservation
from .calibration_profile import ConfidenceCalibrationProfile


class ConfidenceCalibrationRepository:
    """Group confidence observations by market regime before confidence bucket logic."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | ConfidenceCalibrationObservation]) -> None:
        self.observations: Tuple[ConfidenceCalibrationObservation, ...] = tuple(
            value if isinstance(value, ConfidenceCalibrationObservation) else ConfidenceCalibrationObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[ConfidenceCalibrationProfile, ...]:
        grouped: dict[str, list[ConfidenceCalibrationObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.regime_confidence_key].append(observation)
        return tuple(
            ConfidenceCalibrationProfile.from_observations(tuple(grouped[key]))
            for key in sorted(grouped)
        )

    def ready_profiles(self) -> Tuple[ConfidenceCalibrationProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
