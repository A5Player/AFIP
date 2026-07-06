"""Production Milestone E Pack 4 confidence calibration runtime adapter."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.confidence_calibration import ConfidenceCalibrationReport, ConfidenceCalibrationRuntime


class ProductionMilestoneEConfidenceCalibrationRuntime:
    """Production adapter for deterministic confidence calibration intelligence."""

    def __init__(self, runtime: ConfidenceCalibrationRuntime | None = None) -> None:
        self.runtime = runtime or ConfidenceCalibrationRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> ConfidenceCalibrationReport:
        return self.runtime.run(observations)
