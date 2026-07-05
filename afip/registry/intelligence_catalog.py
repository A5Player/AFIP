from afip.intelligence.market_intelligence_v2 import MarketIntelligenceV2
from afip.intelligence.market_structure_intelligence import MarketStructureIntelligence
from afip.intelligence.trend_strength_intelligence import TrendStrengthIntelligence
from afip.intelligence.momentum_quality_intelligence import MomentumQualityIntelligence
from afip.intelligence.liquidity_intelligence import LiquidityIntelligence
from afip.intelligence.volume_intelligence import VolumeIntelligence
from afip.intelligence.order_flow_intelligence import OrderFlowIntelligence
from afip.intelligence.volatility_risk_intelligence import VolatilityRiskIntelligence
from afip.intelligence.correlation_intelligence import CorrelationIntelligence
from afip.intelligence.news_risk_intelligence import NewsRiskIntelligence
from afip.intelligence.risk_intelligence import RiskIntelligence
from afip.intelligence.portfolio_intelligence import PortfolioIntelligence
from afip.intelligence.execution_intelligence import ExecutionIntelligence
from afip.intelligence.performance_intelligence import PerformanceIntelligence
from afip.intelligence.learning_intelligence import LearningIntelligence


class IntelligenceCatalog:
    def load_default(self):
        return [
            MarketIntelligenceV2(),
            MarketStructureIntelligence(),
            TrendStrengthIntelligence(),
            MomentumQualityIntelligence(),
            LiquidityIntelligence(),
            VolumeIntelligence(),
            OrderFlowIntelligence(),
            VolatilityRiskIntelligence(),
            CorrelationIntelligence(),
            NewsRiskIntelligence(),
            RiskIntelligence(),
            PortfolioIntelligence(),
            ExecutionIntelligence(),
            PerformanceIntelligence(),
            LearningIntelligence(),
        ]
