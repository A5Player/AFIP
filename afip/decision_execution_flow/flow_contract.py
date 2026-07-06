"""Production Milestone D Pack 3 decision-to-execution flow contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Tuple

from .execution_request import ExecutionRequest

REQUIRED_STAGE_SEQUENCE: Tuple[str, ...] = (
    "RUNTIME_WIRING",
    "DATA_PIPELINE",
    "DECISION_STATE",
    "EXECUTION_READINESS",
)


@dataclass(frozen=True)
class DecisionExecutionFlowContract:
    """Data-first contract proving decision output can become an execution proposal."""

    requests: Tuple[ExecutionRequest, ...]
    stage_keys: Tuple[str, ...]
    missing_stages: Tuple[str, ...]
    active_market_regime: str
    selected_action: str
    average_decision_confidence: float
    average_execution_readiness: float
    requested_position_size: float
    maximum_position_size: float
    flow_score: float
    sequence_is_valid: bool
    all_requests_usable: bool

    @classmethod
    def from_requests(cls, values: Iterable[Mapping[str, Any] | ExecutionRequest]) -> "DecisionExecutionFlowContract":
        requests = tuple(
            value if isinstance(value, ExecutionRequest) else ExecutionRequest.from_mapping(value)
            for value in values
        )
        by_stage = {request.stage_key: request for request in requests}
        ordered_stage_keys = tuple(stage for stage in REQUIRED_STAGE_SEQUENCE if stage in by_stage)
        missing = tuple(stage for stage in REQUIRED_STAGE_SEQUENCE if stage not in by_stage)
        ordered_requests = tuple(by_stage[stage] for stage in ordered_stage_keys)

        regimes = tuple(request.market_regime for request in ordered_requests if request.has_market_regime)
        active_regime = regimes[0] if regimes and all(regime == regimes[0] for regime in regimes) else "UNKNOWN"

        actions = tuple(request.decision_action for request in ordered_requests if request.has_decision_action)
        selected_action = actions[-1] if actions and all(action == actions[-1] for action in actions) else "WAIT"

        decision_values = tuple(request.decision_confidence for request in ordered_requests)
        readiness_values = tuple(request.execution_readiness_score for request in ordered_requests)
        average_decision = round(sum(decision_values) / len(decision_values), 4) if decision_values else 0.0
        average_readiness = round(sum(readiness_values) / len(readiness_values), 4) if readiness_values else 0.0

        requested_size = round(max((request.requested_position_size for request in ordered_requests), default=0.0), 4)
        maximum_size = round(min((request.maximum_position_size for request in ordered_requests if request.maximum_position_size > 0), default=0.0), 4)
        sequence_valid = ordered_stage_keys == REQUIRED_STAGE_SEQUENCE and active_regime != "UNKNOWN"
        all_usable = bool(ordered_requests) and all(request.is_usable for request in ordered_requests)
        flow_score = round((average_decision * 0.45) + (average_readiness * 0.45) + (10.0 if all_usable else 0.0), 4)

        return cls(
            requests=ordered_requests,
            stage_keys=ordered_stage_keys,
            missing_stages=missing,
            active_market_regime=active_regime,
            selected_action=selected_action,
            average_decision_confidence=average_decision,
            average_execution_readiness=average_readiness,
            requested_position_size=requested_size,
            maximum_position_size=maximum_size,
            flow_score=flow_score,
            sequence_is_valid=sequence_valid,
            all_requests_usable=all_usable,
        )

    @property
    def is_ready(self) -> bool:
        return (
            not self.missing_stages
            and self.sequence_is_valid
            and self.all_requests_usable
            and self.selected_action in {"BUY", "SELL"}
            and self.flow_score >= 70.0
            and self.requested_position_size <= self.maximum_position_size
        )
