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
from afip.intelligence.fair_value_gap_intelligence import FairValueGapIntelligence
from afip.intelligence.imbalance_intelligence import ImbalanceIntelligence
from afip.intelligence.order_block_intelligence import OrderBlockIntelligence
from afip.intelligence.liquidity_sweep_intelligence import LiquiditySweepIntelligence
from afip.intelligence.smart_money_concept_intelligence import SmartMoneyConceptIntelligence


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
            FairValueGapIntelligence(),
            ImbalanceIntelligence(),
            OrderBlockIntelligence(),
            LiquiditySweepIntelligence(),
            SmartMoneyConceptIntelligence(),
        ]
