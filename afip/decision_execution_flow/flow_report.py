"""Production Milestone D Pack 3 decision execution report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .flow_contract import DecisionExecutionFlowContract
from .flow_policy import DecisionExecutionDecision


@dataclass(frozen=True)
class DecisionExecutionFlowReport:
    """Deterministic audit report for decision-to-execution readiness."""

    status: str
    action: str
    reason: str
    stage_count: int
    request_count: int
    active_market_regime: str
    selected_action: str
    stage_keys: Tuple[str, ...]
    missing_stages: Tuple[str, ...]
    average_decision_confidence: float
    average_execution_readiness: float
    requested_position_size: float
    maximum_position_size: float
    flow_score: float
    sequence_is_valid: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "stage_count": self.stage_count,
            "request_count": self.request_count,
            "active_market_regime": self.active_market_regime,
            "selected_action": self.selected_action,
            "stage_keys": self.stage_keys,
            "missing_stages": self.missing_stages,
            "average_decision_confidence": self.average_decision_confidence,
            "average_execution_readiness": self.average_execution_readiness,
            "requested_position_size": self.requested_position_size,
            "maximum_position_size": self.maximum_position_size,
            "flow_score": self.flow_score,
            "sequence_is_valid": self.sequence_is_valid,
        }


class DecisionExecutionFlowReporter:
    """Build immutable reports from flow contracts and policy decisions."""

    def build(self, contract: DecisionExecutionFlowContract, decision: DecisionExecutionDecision) -> DecisionExecutionFlowReport:
        return DecisionExecutionFlowReport(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            stage_count=len(contract.stage_keys),
            request_count=len(contract.requests),
            active_market_regime=contract.active_market_regime,
            selected_action=contract.selected_action,
            stage_keys=contract.stage_keys,
            missing_stages=contract.missing_stages,
            average_decision_confidence=contract.average_decision_confidence,
            average_execution_readiness=contract.average_execution_readiness,
            requested_position_size=contract.requested_position_size,
            maximum_position_size=contract.maximum_position_size,
            flow_score=contract.flow_score,
            sequence_is_valid=contract.sequence_is_valid,
        )
