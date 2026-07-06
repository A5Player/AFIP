"""Runtime integration layer for Production Milestone C Pack 19."""

from __future__ import annotations

from typing import Any, Mapping

from .integration_contract import ProductionIntegrationContract
from .integration_policy import ProductionIntegrationPolicy
from .integration_report import ProductionIntegrationReport, ProductionIntegrationReporter


class ProductionIntegrationRuntime:
    def __init__(self) -> None:
        self.policy = ProductionIntegrationPolicy()
        self.reporter = ProductionIntegrationReporter()

    def run(
        self,
        regime_state: Mapping[str, Any],
        decision_state: Mapping[str, Any],
        execution_state: Mapping[str, Any],
    ) -> ProductionIntegrationReport:
        contract = ProductionIntegrationContract.from_states(regime_state, decision_state, execution_state)
        decision = self.policy.decide(contract)
        return self.reporter.build(contract, decision)
