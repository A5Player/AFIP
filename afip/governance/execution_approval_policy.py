"""Execution approval policy for production financial order flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ExecutionApprovalPolicyResult:
    """Final approval decision before order submission."""

    status: str
    approval: str
    approved: bool
    reason: str


class ExecutionApprovalPolicy:
    """Convert compliance and decision quality into final order approval."""

    def approve(
        self,
        compliance_result: Mapping[str, object] | object | None = None,
        decision_profile: Mapping[str, object] | None = None,
    ) -> ExecutionApprovalPolicyResult:
        compliance = self._mapping(compliance_result)
        decision = dict(decision_profile or {})
        compliance_approved = bool(compliance.get("approved", False))
        confidence = self._ratio(decision.get("confidence", 0.0))
        action = str(decision.get("action", "WAIT")).upper()

        if not compliance_approved:
            return ExecutionApprovalPolicyResult(
                "EXECUTION_APPROVAL_REVIEW",
                "REJECTED",
                False,
                "pre_trade_compliance_not_approved",
            )
        if action not in {"BUY", "SELL", "REDUCE"}:
            return ExecutionApprovalPolicyResult(
                "EXECUTION_APPROVAL_REVIEW",
                "REJECTED",
                False,
                "decision_action_not_executable",
            )
        if confidence < 0.60:
            return ExecutionApprovalPolicyResult(
                "EXECUTION_APPROVAL_SELECTIVE",
                "CONDITIONAL",
                False,
                "decision_confidence_below_approval_threshold",
            )
        return ExecutionApprovalPolicyResult(
            "EXECUTION_APPROVAL_READY",
            "APPROVED",
            True,
            "execution_approved_for_order_submission",
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "approved": getattr(value, "approved", False),
            "reason": getattr(value, "reason", "compliance_result"),
        }

    @staticmethod
    def _ratio(value: object) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))
