"""Runtime for Production Milestone C Pack 18 execution readiness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .readiness_checks import CapacityReadinessCheck, CostReadinessCheck, LiquidityReadinessCheck, ReadinessCheckResult, RiskReadinessCheck
from .readiness_input import ExecutionReadinessInput
from .readiness_policy import ExecutionReadinessDecision, ExecutionReadinessPolicy


@dataclass(frozen=True)
class ExecutionReadinessState:
    status: str
    input: dict[str, object]
    checks: list[dict[str, object]]
    decision: dict[str, object]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "input": dict(self.input),
            "checks": [dict(check) for check in self.checks],
            "decision": dict(self.decision),
            "reason": self.reason,
        }


class ExecutionReadinessRuntime:
    def __init__(self) -> None:
        self.checks = (CostReadinessCheck(), LiquidityReadinessCheck(), RiskReadinessCheck(), CapacityReadinessCheck())
        self.policy = ExecutionReadinessPolicy()

    def run(self, value: ExecutionReadinessInput | Mapping[str, Any]) -> ExecutionReadinessState:
        readiness_input = value if isinstance(value, ExecutionReadinessInput) else ExecutionReadinessInput.from_mapping(value)
        results: list[ReadinessCheckResult] = [check.evaluate(readiness_input) for check in self.checks]
        decision: ExecutionReadinessDecision = self.policy.decide(readiness_input, results)
        return ExecutionReadinessState(
            status=decision.status,
            input=readiness_input.as_dict(),
            checks=[result.as_dict() for result in results],
            decision=decision.as_dict(),
            reason=str(decision.reasons[0]),
        )
