"""Policy for deciding whether runtime modules can be wired together."""

from __future__ import annotations

from dataclasses import dataclass

from .flow_contract import RuntimeFlowContract


@dataclass(frozen=True)
class RuntimeWiringDecision:
    status: str
    action: str
    reason: str
    aggregate_readiness: float

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "aggregate_readiness": self.aggregate_readiness,
        }


class RuntimeWiringPolicy:
    """Validate component readiness before enabling the integrated runtime path."""

    def decide(self, contract: RuntimeFlowContract) -> RuntimeWiringDecision:
        if contract.missing_components:
            return RuntimeWiringDecision(
                status="RUNTIME_WIRING_WAIT",
                action="WAIT",
                reason="missing_required_runtime_component",
                aggregate_readiness=contract.aggregate_readiness,
            )
        if not contract.sequence_is_valid:
            return RuntimeWiringDecision(
                status="RUNTIME_WIRING_BLOCKED",
                action="WAIT",
                reason="runtime_sequence_not_regime_first",
                aggregate_readiness=contract.aggregate_readiness,
            )
        if contract.failed_components:
            return RuntimeWiringDecision(
                status="RUNTIME_WIRING_BLOCKED",
                action="WAIT",
                reason="runtime_component_not_ready",
                aggregate_readiness=contract.aggregate_readiness,
            )
        return RuntimeWiringDecision(
            status="RUNTIME_WIRING_READY",
            action="WIRE_RUNTIME",
            reason="runtime_components_ready_in_financial_sequence",
            aggregate_readiness=contract.aggregate_readiness,
        )
