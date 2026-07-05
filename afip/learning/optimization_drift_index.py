"""Production Milestone A Pack 6: optimization drift index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class OptimizationDriftIndexResult:
    """Optimization drift result for learning stability decisions."""

    status: str
    drift_status: str
    drift_score: float
    parameter_delta: float
    learning_delta: float
    calibration_delta: float
    optimization_allowed: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "optimization_drift_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "drift_status": self.drift_status,
            "drift_score": round(self.drift_score, 2),
            "parameter_delta": round(self.parameter_delta, 4),
            "learning_delta": round(self.learning_delta, 4),
            "calibration_delta": round(self.calibration_delta, 4),
            "optimization_allowed": self.optimization_allowed,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class OptimizationDriftIndex:
    """Evaluates whether adaptive optimization remains inside stable production ranges."""

    def evaluate(self, current_parameters: Mapping[str, Any], baseline_parameters: Mapping[str, Any]) -> OptimizationDriftIndexResult:
        entry_current = float(current_parameters.get("entry_threshold", baseline_parameters.get("entry_threshold", 70.0)))
        entry_baseline = float(baseline_parameters.get("entry_threshold", 70.0))
        position_current = float(current_parameters.get("position_threshold", baseline_parameters.get("position_threshold", 62.0)))
        position_baseline = float(baseline_parameters.get("position_threshold", 62.0))
        learning_current = float(current_parameters.get("learning_rate", baseline_parameters.get("learning_rate", 0.05)))
        learning_baseline = float(baseline_parameters.get("learning_rate", 0.05))
        calibration_current = float(current_parameters.get("calibration_factor", baseline_parameters.get("calibration_factor", 1.0)))
        calibration_baseline = float(baseline_parameters.get("calibration_factor", 1.0))

        parameter_delta = abs(entry_current - entry_baseline) + abs(position_current - position_baseline)
        learning_delta = abs(learning_current - learning_baseline)
        calibration_delta = abs(calibration_current - calibration_baseline)
        drift_score = parameter_delta * 3.0 + learning_delta * 220.0 + calibration_delta * 65.0

        blockers: list[str] = []
        if parameter_delta > 10.0:
            blockers.append("parameter_delta_above_production_range")
        if learning_delta > 0.06:
            blockers.append("learning_delta_above_production_range")
        if calibration_delta > 0.18:
            blockers.append("calibration_delta_above_production_range")
        if drift_score > 42.0:
            blockers.append("optimization_drift_score_high")

        optimization_allowed = not blockers
        if drift_score <= 18.0 and optimization_allowed:
            drift_status = "STABLE"
        elif optimization_allowed:
            drift_status = "MODERATE"
        else:
            drift_status = "ELEVATED"

        return OptimizationDriftIndexResult(
            status="READY" if optimization_allowed else "OBSERVE",
            drift_status=drift_status,
            drift_score=drift_score,
            parameter_delta=parameter_delta,
            learning_delta=learning_delta,
            calibration_delta=calibration_delta,
            optimization_allowed=optimization_allowed,
            blockers=blockers,
            reason="optimization_drift_index_ready" if optimization_allowed else "optimization_drift_index_observation_required",
        )
