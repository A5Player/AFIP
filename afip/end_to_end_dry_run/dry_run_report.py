"""Production Milestone D Pack 5 end-to-end dry run report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .dry_run_contract import EndToEndDryRunContract
from .dry_run_policy import EndToEndDryRunDecision


@dataclass(frozen=True)
class EndToEndDryRunReport:
    """Immutable report returned by the end-to-end dry run runtime."""

    status: str
    action: str
    reason: str
    capability_count: int
    evidence_count: int
    missing_capabilities: Tuple[str, ...]
    active_market_regime: str
    dry_run_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_contract(
        cls,
        contract: EndToEndDryRunContract,
        decision: EndToEndDryRunDecision,
    ) -> "EndToEndDryRunReport":
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            capability_count=len(contract.capability_keys),
            evidence_count=len(contract.evidence),
            missing_capabilities=contract.missing_capabilities,
            active_market_regime=contract.active_market_regime,
            dry_run_score=contract.dry_run_score,
            trace_ids=contract.trace_ids,
            is_ready=contract.is_ready and decision.status == "END_TO_END_DRY_RUN_READY",
        )
