from afip.pipeline.strategy_signal_workflow import StrategySignalWorkflow

class BacktestRunner:
    """Runs strategy workflow over historical snapshots (simulation only)."""

    def __init__(self):
        self.workflow=StrategySignalWorkflow()

    def run(self,snapshots:list):
        trades=[]
        wins=0
        for snap in snapshots:
            r=self.workflow.run(snap)
            action=r["strategy_signal"]["action"]
            trades.append(r)
            if action in ("BUY","SELL"):
                wins+=1
        total=len(snapshots)
        return {
            "mode":"SIMULATION",
            "snapshots":total,
            "signals":wins,
            "signal_rate": round((wins/total*100),2) if total else 0,
            "results":trades
        }
