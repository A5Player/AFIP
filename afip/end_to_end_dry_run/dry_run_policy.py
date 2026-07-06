"""Production Milestone D Pack 5 end-to-end dry run policy."""

from __future__ import annotations

from dataclasses import dataclass

from .dry_run_contract import EndToEndDryRunContract


@dataclass(frozen=True)
class EndToEndDryRunDecision:
    """Deterministic policy decision for the production dry run."""

    status: str
    action: str
    reason: str


class EndToEndDryRunPolicy:
    """Decide whether the integrated production path is ready for dry run completion."""

    def decide(self, contract: EndToEndDryRunContract) -> EndToEndDryRunDecision:
        if contract.missing_capabilities:
            return EndToEndDryRunDecision(
                status="END_TO_END_DRY_RUN_WAIT",
                action="WAIT",
                reason="missing_required_capability",
            )
        if not contract.sequence_is_valid:
            return EndToEndDryRunDecision(
                status="END_TO_END_DRY_RUN_BLOCKED",
                action="BLOCK",
                reason="regime_sequence_not_valid",
            )
        if not contract.all_evidence_usable:
            return EndToEndDryRunDecision(
                status="END_TO_END_DRY_RUN_BLOCKED",
                action="BLOCK",
                reason="dry_run_evidence_not_usable",
            )
        if contract.dry_run_score < 70.0:
            return EndToEndDryRunDecision(
                status="END_TO_END_DRY_RUN_BLOCKED",
                action="BLOCK",
                reason="dry_run_score_below_required_quality",
            )
        return EndToEndDryRunDecision(
            status="END_TO_END_DRY_RUN_READY",
            action="CONFIRM_DRY_RUN",
            reason="integrated_runtime_path_ready",
        )
