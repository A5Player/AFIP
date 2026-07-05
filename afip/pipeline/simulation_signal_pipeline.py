from afip.intelligence.trend_intelligence import TrendIntelligence
from afip.intelligence.momentum_intelligence import MomentumIntelligence
from afip.intelligence.volatility_intelligence import VolatilityIntelligence
from afip.intelligence.liquidity_intelligence import LiquidityIntelligence
from afip.scoring.signal_score_calculator import SignalScoreCalculator
from afip.decision.decision_service import DecisionService


class SimulationSignalPipeline:
    """
    Runs a complete SIMULATION-only signal workflow:
    Market Snapshot -> Intelligence -> Score -> Decision
    """

    def __init__(self):
        self.intelligence_modules = [
            TrendIntelligence(),
            MomentumIntelligence(),
            VolatilityIntelligence(),
            LiquidityIntelligence(),
        ]
        self.score_calculator = SignalScoreCalculator()
        self.decision_service = DecisionService()

    def run(self, snapshot: dict):
        intelligence_results = [
            module.analyze(snapshot) for module in self.intelligence_modules
        ]
        score = self.score_calculator.calculate(intelligence_results)
        decision = self.decision_service.decide(score)

        return {
            "mode": "SIMULATION",
            "intelligence": intelligence_results,
            "score": score,
            "decision": decision,
        }
