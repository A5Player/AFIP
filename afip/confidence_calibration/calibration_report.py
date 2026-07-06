"""Production Milestone E Pack 4 confidence calibration report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .calibration_policy import ConfidenceCalibrationDecision
from .calibration_profile import ConfidenceCalibrationProfile


@dataclass(frozen=True)
class ConfidenceCalibrationReport:
    """Immutable report for confidence calibration runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_confidence_bucket: str
    selected_direction: str
    average_raw_confidence_score: float
    realized_accuracy_rate: float
    average_calibration_error_score: float
    calibrated_confidence_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(
        cls,
        profiles: Tuple[ConfidenceCalibrationProfile, ...],
        decision: ConfidenceCalibrationDecision,
    ) -> "ConfidenceCalibrationReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_confidence_bucket=selected.confidence_bucket if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            average_raw_confidence_score=selected.average_raw_confidence_score if selected else 0.0,
            realized_accuracy_rate=selected.realized_accuracy_rate if selected else 0.0,
            average_calibration_error_score=selected.average_calibration_error_score if selected else 0.0,
            calibrated_confidence_score=selected.calibrated_confidence_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "CONFIDENCE_CALIBRATION_READY" and selected is not None,
        )
