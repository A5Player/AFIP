"""Aggregate certification for dataset, walk-forward, ranking, and consumer readiness."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class CertificationPolicy:
    maximum_drawdown_percentage: float = 20.0
    minimum_certified_candidates: int = 1
    minimum_eligible_windows: int = 1
    require_dataset_ready: bool = True

class ProductionResearchCertification:
    def __init__(self, policy: CertificationPolicy | None = None) -> None:
        self.policy = policy or CertificationPolicy()

    def certify(
        self,
        dataset_report: Mapping[str, Any],
        walk_forward_report: Mapping[str, Any],
        ranking_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        findings = []
        dataset_status = str(dataset_report.get("status", "UNKNOWN"))
        if self.policy.require_dataset_ready and dataset_status != "READY":
            findings.append("dataset_not_ready")

        eligible_windows = int(walk_forward_report.get("eligible_window_count", 0))
        if eligible_windows < self.policy.minimum_eligible_windows:
            findings.append("insufficient_eligible_walk_forward_windows")

        top = list(ranking_report.get("top_overall", []))
        if len(top) < self.policy.minimum_certified_candidates:
            findings.append("insufficient_certified_candidates")

        high_drawdown = [
            row.get("research_id")
            for row in top
            if float(row.get("maximum_drawdown_percentage", 999.0)) > self.policy.maximum_drawdown_percentage
        ]
        if high_drawdown:
            findings.append("certified_candidate_exceeds_drawdown_limit")

        status = "CERTIFIED" if not findings else "NOT_CERTIFIED"
        return {
            "schema_version": "1.0",
            "status": status,
            "execution_permission": False,
            "findings": findings,
            "dataset_status": dataset_status,
            "eligible_window_count": eligible_windows,
            "certified_candidate_count": len(top),
            "maximum_drawdown_percentage_limit": self.policy.maximum_drawdown_percentage,
        }
