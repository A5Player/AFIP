"""Production Milestone D Pack 3 execution request normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _clean_text(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value if value is not None else default).strip().upper()
    return text or default


def _clean_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ExecutionRequest:
    """Normalized financial request connecting decision output to execution readiness."""

    stage_key: str
    market_regime: str
    decision_action: str
    decision_confidence: float
    execution_status: str
    execution_readiness_score: float
    cost_status: str
    risk_status: str
    data_pipeline_status: str
    runtime_wiring_status: str
    requested_position_size: float
    maximum_position_size: float

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExecutionRequest":
        return cls(
            stage_key=_clean_text(data.get("stage_key", data.get("stage", "decision_execution"))),
            market_regime=_clean_text(data.get("market_regime", data.get("regime"))),
            decision_action=_clean_text(data.get("decision_action", data.get("action", "WAIT"))),
            decision_confidence=round(_clean_float(data.get("decision_confidence", data.get("confidence"))), 4),
            execution_status=_clean_text(data.get("execution_status", data.get("readiness_status", "WAIT"))),
            execution_readiness_score=round(_clean_float(data.get("execution_readiness_score", data.get("readiness_score"))), 4),
            cost_status=_clean_text(data.get("cost_status", "UNKNOWN")),
            risk_status=_clean_text(data.get("risk_status", "UNKNOWN")),
            data_pipeline_status=_clean_text(data.get("data_pipeline_status", "UNKNOWN")),
            runtime_wiring_status=_clean_text(data.get("runtime_wiring_status", "UNKNOWN")),
            requested_position_size=round(_clean_float(data.get("requested_position_size", data.get("position_size"))), 4),
            maximum_position_size=round(_clean_float(data.get("maximum_position_size", data.get("max_position_size"))), 4),
        )

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN", "NONE"}

    @property
    def has_decision_action(self) -> bool:
        return self.decision_action in {"BUY", "SELL"}

    @property
    def is_execution_ready(self) -> bool:
        return self.execution_status in {"EXECUTION_READY", "EXECUTION_CONFIRMED", "READY"}

    @property
    def cost_is_acceptable(self) -> bool:
        return self.cost_status in {"PASS", "ACCEPTABLE", "READY"}

    @property
    def risk_is_acceptable(self) -> bool:
        return self.risk_status in {"PASS", "ACCEPTABLE", "READY"}

    @property
    def pipeline_is_ready(self) -> bool:
        return self.data_pipeline_status == "DATA_PIPELINE_READY"

    @property
    def runtime_is_ready(self) -> bool:
        return self.runtime_wiring_status == "RUNTIME_WIRING_READY"

    @property
    def position_size_is_valid(self) -> bool:
        return self.requested_position_size > 0 and self.maximum_position_size > 0 and self.requested_position_size <= self.maximum_position_size

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.has_decision_action
            and self.is_execution_ready
            and self.cost_is_acceptable
            and self.risk_is_acceptable
            and self.pipeline_is_ready
            and self.runtime_is_ready
            and self.position_size_is_valid
        )
