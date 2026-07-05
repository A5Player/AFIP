from afip.market.candle_batch_processor import CandleBatchProcessor
from afip.intelligence.trend_consensus_intelligence import TrendConsensusIntelligence
from afip.intelligence.market_regime_intelligence import MarketRegimeIntelligence
from afip.scoring.multi_timeframe_score_calculator import MultiTimeframeScoreCalculator
from afip.decision.decision_service import DecisionService

class MultiTimeframeSignalWorkflow:
    def __init__(self):
        self.batch_processor = CandleBatchProcessor()
        self.trend_consensus = TrendConsensusIntelligence()
        self.market_regime = MarketRegimeIntelligence()
        self.score_calculator = MultiTimeframeScoreCalculator()
        self.decision_service = DecisionService()

    def run(self, symbol: str, timeframe_candles: dict, spread: float = 18) -> dict:
        snapshots = self.batch_processor.build_timeframe_snapshots(symbol, timeframe_candles, spread)
        trend = self.trend_consensus.analyze(snapshots)
        regime = self.market_regime.analyze(snapshots)
        score = self.score_calculator.calculate(trend, regime)
        decision = self.decision_service.decide(score)

        return {
            "mode": "SIMULATION",
            "symbol": symbol,
            "snapshots": snapshots,
            "trend_consensus": trend,
            "market_regime": regime,
            "score": score,
            "decision": decision,
        }
