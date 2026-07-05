from afip.protection.trailing_stop_planner import TrailingStopPlanner
from afip.position.position_lifecycle_manager import PositionLifecycleManager
from afip.journal.simulation_journal import SimulationJournal

class TradeManagementWorkflow:
    def __init__(self):
        self.trailing=TrailingStopPlanner()
        self.lifecycle=PositionLifecycleManager()
        self.journal=SimulationJournal()

    def run(self, profit_points=0, confidence=60):
        trail=self.trailing.update(profit_points,confidence)
        state=self.lifecycle.next_state("OPEN",profit_points)
        self.journal.record({"profit_points":profit_points,"state":state})
        return {"trailing":trail,"state":state,"journal_size":len(self.journal.records)}
