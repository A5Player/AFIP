"""Production integration report model for Production Milestone C Pack 19."""

from __future__ import annotations

from dataclasses import dataclass

from .integration_contract import ProductionIntegrationContract
from .integration_policy import ProductionIntegrationDecision


@dataclass(frozen=True)
class ProductionIntegrationReport:
    status: str
    contract: dict[str, object]
    decision: dict[str, object]
    audit: dict[str, object]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "contract": dict(self.contract),
            "decision": dict(self.decision),
            "audit": dict(self.audit),
            "reason": self.reason,
        }


class ProductionIntegrationReporter:
    def build(self, contract: ProductionIntegrationContract, decision: ProductionIntegrationDecision) -> ProductionIntegrationReport:
        audit = {
            "market_regime_before_decision": contract.regime_status == "MARKET_REGIME_INTELLIGENCE_READY",
            "decision_before_execution": contract.decision_status in {"DECISION_INTELLIGENCE_READY", "DECISION_INTELLIGENCE_WAIT"},
            "execution_after_readiness_checks": contract.execution_status in {"EXECUTION_READY", "EXECUTION_BLOCKED", "EXECUTION_WAIT"},
            "deterministic_contract": True,
        }
        reason = decision.reasons[0] if decision.reasons else "production_integration_reported"
        return ProductionIntegrationReport(decision.status, contract.as_dict(), decision.as_dict(), audit, reason)
