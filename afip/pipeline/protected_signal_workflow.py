from afip.pipeline.risk_aware_signal_workflow import RiskAwareSignalWorkflow
from afip.execution.protected_simulation_order_builder import ProtectedSimulationOrderBuilder

class ProtectedSignalWorkflow:
    def __init__(self):
        self.base_workflow = RiskAwareSignalWorkflow()
        self.order_builder = ProtectedSimulationOrderBuilder()

    def run(self, symbol: str, timeframe_candles: dict, spread: float = 18, balance: float = 1000.0) -> dict:
        base = self.base_workflow.run(symbol, timeframe_candles, spread)
        first_snapshot = next(iter(base["signal"]["snapshots"].values()))
        protected_order = self.order_builder.build(base["decision"], first_snapshot, balance=balance)

        return {
            "mode": "SIMULATION",
            "base": base,
            "protected_order": protected_order,
        }
