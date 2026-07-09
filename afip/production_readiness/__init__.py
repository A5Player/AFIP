"""Production readiness exports."""

from .readiness_observation import ProductionReadinessObservation
from .readiness_policy import ProductionReadinessDecision, ProductionReadinessPolicy
from .readiness_profile import ProductionReadinessProfile
from .readiness_report import ProductionReadinessReport as LegacyProductionReadinessReport
from .readiness_repository import ProductionReadinessRepository
from .readiness_runtime import ProductionReadinessRuntime as LegacyProductionReadinessRuntime
from .models import DeploymentStep, DemoTradingReadiness, ProductionReadinessReport as MilestoneHProductionReadinessReport
from .runtime import ProductionReadinessRuntime as MilestoneHProductionReadinessRuntime


class ProductionReadinessRuntime(LegacyProductionReadinessRuntime):
    """Backward-compatible production readiness runtime with Pack 10 evaluation."""

    def evaluate_one(self, record):
        return MilestoneHProductionReadinessRuntime().evaluate_one(record)

    def explain_one(self, record):
        return self.evaluate_one(record)


__all__ = [
    "ProductionReadinessObservation",
    "ProductionReadinessDecision",
    "ProductionReadinessPolicy",
    "ProductionReadinessProfile",
    "ProductionReadinessRepository",
    "LegacyProductionReadinessReport",
    "LegacyProductionReadinessRuntime",
    "DeploymentStep",
    "DemoTradingReadiness",
    "MilestoneHProductionReadinessReport",
    "MilestoneHProductionReadinessRuntime",
    "ProductionReadinessRuntime",
]
