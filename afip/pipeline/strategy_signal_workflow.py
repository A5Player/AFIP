from afip.strategy.trend_following_strategy import TrendFollowingStrategy
from afip.strategy.breakout_strategy import BreakoutStrategy
from afip.strategy.mean_reversion_strategy import MeanReversionStrategy
from afip.strategy.strategy_aggregator import StrategyAggregator

class StrategySignalWorkflow:
    def __init__(self, strategies=None, aggregator=None):
        self.strategies = strategies or [
            TrendFollowingStrategy(),
            BreakoutStrategy(),
            MeanReversionStrategy(),
        ]
        self.aggregator = aggregator or StrategyAggregator()

    def run(self, snapshot: dict) -> dict:
        results = [strategy.evaluate(snapshot) for strategy in self.strategies]
        aggregate = self.aggregator.aggregate(results)
        return {
            "mode": "SIMULATION",
            "strategy_results": results,
            "strategy_signal": aggregate,
        }
