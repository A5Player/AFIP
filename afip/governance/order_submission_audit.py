"""Order submission audit records for financial execution review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class OrderSubmissionAuditRecord:
    """Immutable audit record for a proposed order submission."""

    status: str
    audit_id: str
    action: str
    lot_size: float
    approved: bool
    reason: str


class OrderSubmissionAudit:
    """Create deterministic audit identifiers for approved or reviewed orders."""

    def create(
        self,
        execution_plan: Mapping[str, object] | None = None,
        compliance_result: Mapping[str, object] | object | None = None,
        sequence: int = 1,
    ) -> OrderSubmissionAuditRecord:
        plan = dict(execution_plan or {})
        compliance = self._mapping(compliance_result)
        action = str(plan.get("action", "WAIT")).upper()
        lot_size = round(self._float(plan.get("lot_size", plan.get("lot", 0.0))), 2)
        approved = bool(compliance.get("approved", False))
        reason = str(compliance.get("reason", "order_submission_audit_recorded"))
        audit_status = "APPROVED" if approved else "REVIEW"
        audit_id = f"AFIP-ORDER-{int(sequence):06d}-{audit_status}-{action}"
        return OrderSubmissionAuditRecord(
            status="ORDER_SUBMISSION_AUDIT_READY",
            audit_id=audit_id,
            action=action,
            lot_size=lot_size,
            approved=approved,
            reason=reason,
        )

    @staticmethod
    def _mapping(value: Mapping[str, object] | object | None) -> dict[str, object]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {
            "approved": getattr(value, "approved", False),
            "reason": getattr(value, "reason", "order_submission_audit_recorded"),
        }

    @staticmethod
    def _float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
