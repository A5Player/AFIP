"""Production Milestone B Pack 11 execution approval runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from afip.governance.execution_approval_policy import ExecutionApprovalPolicy
from afip.governance.order_submission_audit import OrderSubmissionAudit
from afip.governance.pre_trade_compliance import PreTradeCompliance


@dataclass(frozen=True)
class ProductionMilestoneBApprovalRuntimeResult:
    """Runtime output for pre-trade compliance and approval."""

    status: str
    approval: str
    approved: bool
    compliance_score: float
    audit_id: str
    failed_rules: tuple[str, ...]
    reason: str


class ProductionMilestoneBApprovalRuntime:
    """Run final financial approval controls before order submission."""

    def run(
        self,
        execution_plan: Mapping[str, object] | None = None,
        decision_profile: Mapping[str, object] | None = None,
        account_state: Mapping[str, object] | None = None,
        market_state: Mapping[str, object] | None = None,
        sequence: int = 1,
    ) -> ProductionMilestoneBApprovalRuntimeResult:
        compliance = PreTradeCompliance().evaluate(execution_plan, account_state, market_state)
        approval = ExecutionApprovalPolicy().approve(compliance, decision_profile)
        audit = OrderSubmissionAudit().create(execution_plan, compliance, sequence=sequence)

        status = "PRODUCTION_MILESTONE_B_APPROVAL_READY" if approval.approved else "PRODUCTION_MILESTONE_B_APPROVAL_REVIEW"
        return ProductionMilestoneBApprovalRuntimeResult(
            status=status,
            approval=approval.approval,
            approved=approval.approved,
            compliance_score=compliance.score,
            audit_id=audit.audit_id,
            failed_rules=compliance.failed_rules,
            reason=approval.reason,
        )

    def run_dict(
        self,
        execution_plan: Mapping[str, object] | None = None,
        decision_profile: Mapping[str, object] | None = None,
        account_state: Mapping[str, object] | None = None,
        market_state: Mapping[str, object] | None = None,
        sequence: int = 1,
    ) -> dict[str, object]:
        return asdict(self.run(execution_plan, decision_profile, account_state, market_state, sequence))
