"""Runtime wiring report for audit-friendly production readiness."""

from __future__ import annotations

from dataclasses import dataclass

from .flow_contract import RuntimeFlowContract
from .wiring_policy import RuntimeWiringDecision


@dataclass(frozen=True)
class RuntimeWiringReport:
    status: str
    action: str
    reason: str
    aggregate_readiness: float
    component_count: int
    missing_components: tuple[str, ...]
    failed_components: tuple[str, ...]
    sequence_is_valid: bool
    component_keys: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "aggregate_readiness": self.aggregate_readiness,
            "component_count": self.component_count,
            "missing_components": list(self.missing_components),
            "failed_components": list(self.failed_components),
            "sequence_is_valid": self.sequence_is_valid,
            "component_keys": list(self.component_keys),
        }


class RuntimeWiringReporter:
    def build(self, contract: RuntimeFlowContract, decision: RuntimeWiringDecision) -> RuntimeWiringReport:
        return RuntimeWiringReport(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            aggregate_readiness=decision.aggregate_readiness,
            component_count=len(contract.components),
            missing_components=contract.missing_components,
            failed_components=contract.failed_components,
            sequence_is_valid=contract.sequence_is_valid,
            component_keys=contract.component_keys,
        )
