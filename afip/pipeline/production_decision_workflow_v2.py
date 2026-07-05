"""Production decision workflow V2 for AFIP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afip.governance.quality_checkpoint import QualityCheckpoint
from afip.report.executive_decision_report import ExecutiveDecisionReport
from afip.runtime.production_orchestrator import ProductionOrchestrator


@dataclass(frozen=True)
class ProductionDecisionWorkflowV2Result:
    status: str
    action: str
    confidence: float
    reason: str
    report_lines: tuple[str, ...]
    details: dict[str, Any]


class ProductionDecisionWorkflowV2:
    """Run final production decision workflow from normalized component outputs."""

    def __init__(self) -> None:
        self._checkpoint = QualityCheckpoint()
        self._orchestrator = ProductionOrchestrator()
        self._report = ExecutiveDecisionReport()

    def run(
        self,
        decision: dict[str, Any],
        readiness: dict[str, Any],
        risk: dict[str, Any],
        completed_quality_checks: tuple[str, ...] | list[str] | None = None,
    ) -> ProductionDecisionWorkflowV2Result:
        checkpoint = self._checkpoint.from_completed_names(completed_quality_checks or ())
        orchestration = self._orchestrator.run(
            decision=decision,
            readiness=readiness,
            risk=risk,
            checkpoint={"status": checkpoint.status, "score": checkpoint.score},
        )
        report = self._report.build(
            decision={"action": orchestration.action, "confidence": orchestration.confidence},
            readiness={"score": orchestration.readiness_score},
            risk={"status": "PASS" if orchestration.risk_score >= 60 else "BLOCKED", "position_size": risk.get("position_size", 0.0)},
        )

        return ProductionDecisionWorkflowV2Result(
            status=orchestration.status,
            action=orchestration.action,
            confidence=orchestration.confidence,
            reason=orchestration.reason,
            report_lines=report.lines,
            details={
                "checkpoint": checkpoint,
                "orchestration": orchestration,
                "report": report,
            },
        )
