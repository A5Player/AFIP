"""Production Milestone E Pack 4 confidence calibration profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .calibration_observation import ConfidenceCalibrationObservation


@dataclass(frozen=True)
class ConfidenceCalibrationProfile:
    """Data-derived profile for one market-regime confidence bucket."""

    profile_key: str
    market_regime: str
    confidence_bucket: str
    direction: str
    sample_count: int
    average_raw_confidence_score: float
    realized_accuracy_rate: float
    average_calibration_error_score: float
    average_confidence_stability_score: float
    average_confidence_drift_score: float
    average_execution_cost_score: float
    calibrated_confidence_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[ConfidenceCalibrationObservation, ...]

    @classmethod
    def from_observations(
        cls,
        observations: Tuple[ConfidenceCalibrationObservation, ...],
    ) -> "ConfidenceCalibrationProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                confidence_bucket="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                average_raw_confidence_score=0.0,
                realized_accuracy_rate=0.0,
                average_calibration_error_score=0.0,
                average_confidence_stability_score=0.0,
                average_confidence_drift_score=0.0,
                average_execution_cost_score=0.0,
                calibrated_confidence_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        total_samples = sum(item.sample_count for item in observations)
        avg_raw = round(sum(item.raw_confidence_score for item in observations) / len(observations), 4)
        avg_accuracy = round(sum(item.realized_accuracy_rate for item in observations) / len(observations), 4)
        avg_error = round(sum(item.calibration_error_score for item in observations) / len(observations), 4)
        avg_stability = round(sum(item.confidence_stability_score for item in observations) / len(observations), 4)
        avg_drift = round(sum(item.confidence_drift_score for item in observations) / len(observations), 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / len(observations), 4)
        calibrated_score = round(
            (avg_raw * 0.2)
            + (avg_accuracy * 0.3)
            + ((100.0 - avg_error) * 0.2)
            + (avg_stability * 0.15)
            + ((100.0 - avg_drift) * 0.1)
            + (avg_cost * 0.05),
            4,
        )
        return cls(
            profile_key=first.regime_confidence_key,
            market_regime=first.market_regime,
            confidence_bucket=first.confidence_bucket,
            direction=first.direction,
            sample_count=total_samples,
            average_raw_confidence_score=avg_raw,
            realized_accuracy_rate=avg_accuracy,
            average_calibration_error_score=avg_error,
            average_confidence_stability_score=avg_stability,
            average_confidence_drift_score=avg_drift,
            average_execution_cost_score=avg_cost,
            calibrated_confidence_score=calibrated_score,
            trace_ids=tuple(sorted(item.trace_id for item in observations if item.trace_id)),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.confidence_bucket != "UNKNOWN"
            and self.sample_count >= 20
            and self.average_raw_confidence_score >= 50.0
            and self.realized_accuracy_rate >= 55.0
            and self.average_calibration_error_score <= 20.0
            and self.average_confidence_stability_score >= 55.0
            and self.average_confidence_drift_score <= 30.0
            and self.average_execution_cost_score >= 50.0
            and self.calibrated_confidence_score >= 60.0
            and bool(self.trace_ids)
        )
