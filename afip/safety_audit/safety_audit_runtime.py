"""Production Milestone D Pack 4 safety and audit runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .audit_contract import SafetyAuditContract
from .audit_policy import SafetyAuditPolicy
from .audit_report import SafetyAuditReport


class SafetyAuditRuntime:
    """Build final safety and audit state before a production execution path is allowed."""

    def __init__(self, policy: SafetyAuditPolicy | None = None) -> None:
        self.policy = policy or SafetyAuditPolicy()

    def run(self, evidence: Iterable[Mapping[str, Any]]) -> SafetyAuditReport:
        contract = SafetyAuditContract.from_evidence(evidence)
        decision = self.policy.decide(contract)
        return SafetyAuditReport.from_contract(contract, decision)
