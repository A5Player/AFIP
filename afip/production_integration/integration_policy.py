"""Production integration policy for Production Milestone C Pack 19."""

from __future__ import annotations

from dataclasses import dataclass

from .integration_contract import ProductionIntegrationContract


@dataclass(frozen=True)
class ProductionIntegrationDecision:
    status: str
    action: str
    readiness: str
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "readiness": self.readiness,
            "reasons": list(self.reasons),
        }


class ProductionIntegrationPolicy:
    def decide(self, contract: ProductionIntegrationContract) -> ProductionIntegrationDecision:
        if contract.regime_status != "MARKET_REGIME_INTELLIGENCE_READY":
            return ProductionIntegrationDecision("PRODUCTION_DATA_REQUIRED", "WAIT", "BLOCKED", ("market_regime_required_before_production",))
        if contract.decision_status != "DECISION_INTELLIGENCE_READY":
            return ProductionIntegrationDecision("PRODUCTION_DECISION_WAIT", "WAIT", "WAIT", ("decision_intelligence_not_ready",))
        if contract.execution_status != "EXECUTION_READY":
            return ProductionIntegrationDecision("PRODUCTION_EXECUTION_BLOCKED", "WAIT", "BLOCKED", ("execution_readiness_not_confirmed",))
        if not contract.is_ready:
            return ProductionIntegrationDecision("PRODUCTION_WAIT", "WAIT", "WAIT", ("production_contract_not_ready",))
        return ProductionIntegrationDecision("PRODUCTION_READY", contract.action, "READY", ("production_integration_confirmed",))
