"""Production Milestone E Pack 4 confidence calibration observation model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _norm(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value or "").strip().upper().replace(" ", "_").replace("-", "_")
    return text or default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ConfidenceCalibrationObservation:
    """Single realized confidence observation after market regime is known."""

    market_regime: str
    confidence_bucket: str
    direction: str
    sample_count: int
    raw_confidence_score: float
    realized_accuracy_rate: float
    calibration_error_score: float
    confidence_stability_score: float
    confidence_drift_score: float
    execution_cost_score: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ConfidenceCalibrationObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            confidence_bucket=_norm(value.get("confidence_bucket") or value.get("bucket") or value.get("confidence_band")),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            raw_confidence_score=_float(value.get("raw_confidence_score") or value.get("raw_confidence")),
            realized_accuracy_rate=_float(value.get("realized_accuracy_rate") or value.get("accuracy_rate")),
            calibration_error_score=_float(value.get("calibration_error_score") or value.get("calibration_error")),
            confidence_stability_score=_float(value.get("confidence_stability_score") or value.get("stability_score")),
            confidence_drift_score=_float(value.get("confidence_drift_score") or value.get("drift_score")),
            execution_cost_score=_float(value.get("execution_cost_score") or value.get("cost_score")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def regime_confidence_key(self) -> str:
        return f"{self.market_regime}:{self.confidence_bucket}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.confidence_bucket not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.raw_confidence_score > 0
            and self.realized_accuracy_rate > 0
            and self.calibration_error_score >= 0
            and self.confidence_stability_score > 0
            and self.confidence_drift_score >= 0
            and self.execution_cost_score > 0
            and bool(self.trace_id)
        )
