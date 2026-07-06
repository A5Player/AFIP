"""Production Milestone E Pack 4 confidence calibration policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .calibration_profile import ConfidenceCalibrationProfile


@dataclass(frozen=True)
class ConfidenceCalibrationDecision:
    """Deterministic decision describing confidence calibration readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class ConfidenceCalibrationPolicy:
    """Select the strongest data-derived confidence calibration profile."""

    def decide(self, profiles: Tuple[ConfidenceCalibrationProfile, ...]) -> ConfidenceCalibrationDecision:
        if not profiles:
            return ConfidenceCalibrationDecision(
                status="CONFIDENCE_CALIBRATION_WAIT",
                action="WAIT",
                reason="no_usable_confidence_calibration_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return ConfidenceCalibrationDecision(
                status="CONFIDENCE_CALIBRATION_WAIT",
                action="WAIT",
                reason="insufficient_confidence_calibration_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.calibrated_confidence_score,
                item.average_calibration_error_score,
                item.average_confidence_drift_score,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return ConfidenceCalibrationDecision(
            status="CONFIDENCE_CALIBRATION_READY",
            action="USE_CALIBRATED_CONFIDENCE",
            reason="confidence_calibration_profile_ready",
            selected_profile_key=selected.profile_key,
        )
