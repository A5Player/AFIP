# AFIP Phase 23 — Multi-Timeframe Analysis

Adds multi-timeframe candle processing and consensus analysis.

Flow:
Timeframe candle batches
→ CandleBatchProcessor
→ TrendConsensusIntelligence
→ MarketRegimeIntelligence
→ MultiTimeframeScoreCalculator
→ DecisionService

Safety:
- SIMULATION only
- No live order execution

Next:
- Add risk-aware decision thresholds
- Add portfolio exposure simulation
- Add execution order builder in SIMULATION mode
