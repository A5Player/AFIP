"""Production Milestone D Pack 3 decision-to-execution runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .flow_contract import DecisionExecutionFlowContract
from .flow_policy import DecisionExecutionFlowPolicy
from .flow_report import DecisionExecutionFlowReport, DecisionExecutionFlowReporter


class DecisionExecutionFlowRuntime:
    """Convert integrated decision data into a deterministic execution proposal report."""

    def __init__(self) -> None:
        self.policy = DecisionExecutionFlowPolicy()
        self.reporter = DecisionExecutionFlowReporter()

    def run(self, requests: Iterable[Mapping[str, Any]]) -> DecisionExecutionFlowReport:
        contract = DecisionExecutionFlowContract.from_requests(requests)
        decision = self.policy.decide(contract)
        return self.reporter.build(contract, decision)
