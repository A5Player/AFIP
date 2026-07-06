"""Production Milestone D Pack 3 decision execution policy."""

from __future__ import annotations

from dataclasses import dataclass

from .flow_contract import DecisionExecutionFlowContract


@dataclass(frozen=True)
class DecisionExecutionDecision:
    """Policy result for a decision-to-execution flow."""

    status: str
    action: str
    reason: str


class DecisionExecutionFlowPolicy:
    """Confirm whether a decision can be promoted to an execution proposal."""

    def decide(self, contract: DecisionExecutionFlowContract) -> DecisionExecutionDecision:
        if contract.missing_stages:
            return DecisionExecutionDecision("DECISION_EXECUTION_WAIT", "WAIT", "required_financial_stage_missing")
        if not contract.sequence_is_valid:
            return DecisionExecutionDecision("DECISION_EXECUTION_BLOCKED", "WAIT", "market_regime_sequence_invalid")
        if contract.selected_action not in {"BUY", "SELL"}:
            return DecisionExecutionDecision("DECISION_EXECUTION_WAIT", "WAIT", "decision_action_not_ready")
        if not contract.all_requests_usable:
            return DecisionExecutionDecision("DECISION_EXECUTION_BLOCKED", "WAIT", "execution_request_not_usable")
        if contract.requested_position_size > contract.maximum_position_size:
            return DecisionExecutionDecision("DECISION_EXECUTION_BLOCKED", "WAIT", "position_size_exceeds_capacity")
        if contract.flow_score < 70.0:
            return DecisionExecutionDecision("DECISION_EXECUTION_WAIT", "WAIT", "decision_execution_score_insufficient")
        return DecisionExecutionDecision("DECISION_EXECUTION_READY", "PREPARE_EXECUTION", "decision_execution_flow_ready")
