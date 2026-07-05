from afip.pipeline.multi_timeframe_signal_workflow import MultiTimeframeSignalWorkflow
from afip.risk.risk_assessor import RiskAssessor
from afip.decision.risk_aware_decision_service import RiskAwareDecisionService
from afip.execution.simulation_order_builder import SimulationOrderBuilder

class RiskAwareSignalWorkflow:
    def __init__(self):
        self.signal_workflow = MultiTimeframeSignalWorkflow()
        self.risk_assessor = RiskAssessor()
        self.decision_service = RiskAwareDecisionService()
        self.order_builder = SimulationOrderBuilder()

    def run(self, symbol: str, timeframe_candles: dict, spread: float = 18, portfolio_state: dict | None = None) -> dict:
        signal = self.signal_workflow.run(symbol, timeframe_candles, spread)
        first_snapshot = next(iter(signal["snapshots"].values()))
        risk = self.risk_assessor.assess(first_snapshot, signal["score"], portfolio_state)
        decision = self.decision_service.decide(signal["decision"], risk)
        order = self.order_builder.build(decision, symbol=symbol)

        return {
            "mode": "SIMULATION",
            "signal": signal,
            "risk": risk,
            "decision": decision,
            "order": order,
        }
