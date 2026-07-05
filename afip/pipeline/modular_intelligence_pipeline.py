from afip.registry.intelligence_catalog import IntelligenceCatalog
from afip.decision.decision_intelligence import DecisionIntelligence


class ModularIntelligencePipeline:
    """
    Runs AFIP modular Intelligence set and produces transparent Decision Intelligence output.
    """

    def __init__(self, catalog=None, decision_intelligence=None):
        self.catalog = catalog or IntelligenceCatalog()
        self.decision_intelligence = decision_intelligence or DecisionIntelligence()

    def run(self, snapshot: dict) -> dict:
        modules = self.catalog.load_default()
        intelligence_results = [module.analyze(snapshot) for module in modules]
        decision = self.decision_intelligence.decide(intelligence_results)

        return {
            "mode": "SIMULATION",
            "module_count": len(modules),
            "intelligence": intelligence_results,
            "decision": decision,
        }
