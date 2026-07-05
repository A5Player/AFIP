"""Production Milestone B Pack 2 adaptive weight runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.fusion.adaptive_weight_engine import AdaptiveWeightEngine
from afip.fusion.intelligence_weight_matrix import IntelligenceWeightMatrix
from afip.fusion.performance_weight_adjustment import PerformanceWeightAdjustment
from afip.fusion.regime_weight_profile import RegimeWeightProfile


@dataclass(frozen=True)
class ProductionMilestoneBWeightRuntimeResult:
    """Runtime result for adaptive financial intelligence weighting."""

    status: str
    regime: str
    weights: dict[str, float]
    dominant_category: str
    matrix: dict[str, dict[str, float]]
    reason: str


class ProductionMilestoneBWeightRuntime:
    """Compose regime profile, adaptive inputs, performance, and matrix allocation."""

    def run(
        self,
        regime: str,
        intelligence_inputs: Iterable[Mapping[str, object]],
        performance_attribution: Mapping[str, float] | None = None,
    ) -> ProductionMilestoneBWeightRuntimeResult:
        regime_result = RegimeWeightProfile().resolve(regime)
        adaptive_result = AdaptiveWeightEngine().calculate(intelligence_inputs)
        base_weights = adaptive_result.weights or regime_result.weights
        adjusted = PerformanceWeightAdjustment().adjust(base_weights, performance_attribution or {})
        matrix = IntelligenceWeightMatrix().build(
            adjusted.weights,
            {
                "TREND": ["TrendStrengthIntelligence", "MarketIntelligenceV2"],
                "MOMENTUM": ["MomentumIntelligence"],
                "LIQUIDITY": ["LiquidityIntelligence", "OrderFlowIntelligence"],
                "EXECUTION": ["ExecutionQualityIndex"],
                "RISK": ["RiskIntelligence", "PortfolioExposureAllocator"],
                "STRUCTURE": ["MarketStructureIntelligence"],
                "VOLATILITY": ["VolatilityIntelligence"],
            },
        )
        dominant = max(adjusted.weights, key=adjusted.weights.get) if adjusted.weights else "NONE"
        status = "MILESTONE_B_WEIGHT_RUNTIME_READY" if adjusted.weights and matrix.matrix else "MILESTONE_B_WEIGHT_RUNTIME_REVIEW"
        return ProductionMilestoneBWeightRuntimeResult(
            status=status,
            regime=regime_result.regime,
            weights=adjusted.weights,
            dominant_category=dominant,
            matrix=matrix.matrix,
            reason="adaptive_financial_weight_runtime_ready" if status.endswith("READY") else "adaptive_financial_weight_runtime_review",
        )
