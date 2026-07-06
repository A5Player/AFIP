"""Production Milestone D Pack 1 runtime wiring orchestration."""

from __future__ import annotations

from typing import Any, Mapping

from .flow_contract import RuntimeFlowContract
from .wiring_policy import RuntimeWiringPolicy
from .wiring_report import RuntimeWiringReport, RuntimeWiringReporter


class RuntimeWiringRuntime:
    """Connect completed intelligence states into one deterministic runtime path."""

    def __init__(self) -> None:
        self.policy = RuntimeWiringPolicy()
        self.reporter = RuntimeWiringReporter()

    def run(self, states: Mapping[str, Mapping[str, Any]]) -> RuntimeWiringReport:
        contract = RuntimeFlowContract.from_runtime_states(states)
        decision = self.policy.decide(contract)
        return self.reporter.build(contract, decision)
