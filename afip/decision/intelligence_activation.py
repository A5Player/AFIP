"""Authoritative activation policy for the AFIP modular intelligence decision path.

This module does not create new market detectors.  It classifies the existing
modules by their real consumer role so context/gate/composite outputs are not
mistaken for independent directional votes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class IntelligenceActivation:
    name: str
    role: str
    decision_vote: bool
    weight: float
    source_status: str = "SOURCE_EXISTS"
    runtime_status: str = "CONNECTED_TO_RUNTIME"
    decision_status: str = "CONNECTED_TO_DECISION"
    entry_status: str = "CONNECTED_TO_ENTRY"
    position_care_status: str = "NOT_CONNECTED"
    exit_status: str = "NOT_CONNECTED"
    research_status: str = "TRACE_PARTIAL"
    reason: str = "existing_modular_pipeline"

    def as_dict(self) -> dict:
        return asdict(self)


# Independent directional detectors only.  Context, gate and composite modules
# remain visible in evidence but cannot manufacture extra directional consensus.
_POLICY = {
    "MarketIntelligenceV2": ("DETECTOR", True, 0.75, "broad_market_detector"),
    "MarketStructureIntelligence": ("DETECTOR", True, 1.25, "independent_structure_detector"),
    "TrendStrengthIntelligence": ("DETECTOR", True, 0.85, "independent_trend_detector"),
    "MomentumQualityIntelligence": ("DETECTOR", True, 0.75, "independent_momentum_detector"),
    "LiquidityIntelligence": ("DETECTOR", True, 1.00, "independent_liquidity_detector"),
    "VolumeIntelligence": ("DETECTOR", True, 0.70, "tick_volume_directional_context"),
    "OrderFlowIntelligence": ("PROXY_DETECTOR", True, 0.55, "candle_pressure_proxy_not_real_order_flow"),
    "FairValueGapIntelligence": ("DETECTOR", True, 1.10, "independent_fvg_detector"),
    "ImbalanceIntelligence": ("DETECTOR", True, 1.00, "independent_imbalance_detector"),
    "OrderBlockIntelligence": ("DETECTOR", True, 1.10, "independent_order_block_detector"),
    "LiquiditySweepIntelligence": ("DETECTOR", True, 1.15, "independent_liquidity_sweep_detector"),
    # Composite of FVG/imbalance/order-block/sweep: evidence only, no second vote.
    "SmartMoneyConceptIntelligence": ("COMPOSITE_CONTEXT", False, 0.00, "prevents_component_double_counting"),
    "VolatilityRiskIntelligence": ("RISK_CONTEXT", False, 0.00, "risk_context_not_direction_vote"),
    "CorrelationIntelligence": ("CONTEXT", False, 0.00, "placeholder_context_not_direction_vote"),
    "NewsRiskIntelligence": ("RISK_CONTEXT", False, 0.00, "placeholder_context_not_direction_vote"),
    "RiskIntelligence": ("GATE_CONTEXT", False, 0.00, "risk_gate_not_direction_vote"),
    "PortfolioIntelligence": ("CAPACITY_CONTEXT", False, 0.00, "capacity_context_not_direction_vote"),
    "ExecutionIntelligence": ("EXECUTION_CONTEXT", False, 0.00, "execution_quality_not_direction_vote"),
    "PerformanceIntelligence": ("RESEARCH_CONTEXT", False, 0.00, "performance_context_not_direction_vote"),
    "LearningIntelligence": ("RESEARCH_CONTEXT", False, 0.00, "learning_context_not_direction_vote"),
}


def activation_for(name: str) -> IntelligenceActivation:
    role, vote, weight, reason = _POLICY.get(
        str(name), ("UNCLASSIFIED_CONTEXT", False, 0.00, "unclassified_module_cannot_vote"),
    )
    return IntelligenceActivation(str(name), role, vote, float(weight), reason=reason)


def build_activation_matrix(module_names: list[str]) -> list[dict]:
    return [activation_for(name).as_dict() for name in module_names]
