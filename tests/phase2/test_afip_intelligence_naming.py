from aif.core import (
    DecisionIntelligence,
    ExecutionIntelligence,
    MarketIntelligence,
    PortfolioIntelligence,
    RiskIntelligence,
)
from aif.core.financial_models import StrategySignal, TradeSide


def test_new_core_exports_intelligence_names():
    assert DecisionIntelligence
    assert ExecutionIntelligence
    assert MarketIntelligence
    assert PortfolioIntelligence
    assert RiskIntelligence


def test_strategy_signal_uses_source_intelligence():
    signal = StrategySignal(side=TradeSide.HOLD, entry_score=50, position_confidence=50)
    assert signal.source_intelligence == "Market Intelligence"
    assert signal.source_engine == signal.source_intelligence  # compatibility property only
