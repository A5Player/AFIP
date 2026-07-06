"""Production Milestone D Pack 5 end-to-end dry run runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .dry_run_contract import EndToEndDryRunContract
from .dry_run_policy import EndToEndDryRunPolicy
from .dry_run_report import EndToEndDryRunReport


class EndToEndDryRunRuntime:
    """Execute a deterministic dry run over the integrated financial runtime path."""

    def __init__(self, policy: EndToEndDryRunPolicy | None = None) -> None:
        self.policy = policy or EndToEndDryRunPolicy()

    def run(self, evidence: Iterable[Mapping[str, Any]]) -> EndToEndDryRunReport:
        contract = EndToEndDryRunContract.from_evidence(evidence)
        decision = self.policy.decide(contract)
        return EndToEndDryRunReport.from_contract(contract, decision)
