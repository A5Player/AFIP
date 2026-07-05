from afip.intelligence.adaptive_intelligence_core import AdaptiveIntelligenceCore, AdaptiveSignal
from afip.intelligence.market_regime_intelligence_v2 import MarketRegimeIntelligenceV2
from afip.learning.adaptive_learning_optimizer import AdaptiveLearningOptimizer
from afip.runtime.production_milestone_a_runtime import ProductionMilestoneARuntime


def test_a1_adaptive_core_supports_dict_backward_compatibility():
    decision = AdaptiveIntelligenceCore(min_confidence=60, decision_margin=5).evaluate([
        {"name": "trend", "side": "BUY", "score": 82, "confidence": 90, "weight": 1.4, "status": "READY"},
        {"name": "liquidity", "side": "BUY", "score": 74, "confidence": 80, "weight": 1.0, "status": "READY"},
        {"name": "cost", "side": "HOLD", "score": 55, "confidence": 70, "weight": 0.5, "status": "READY"},
    ]).to_dict()

    assert decision["status"] == "READY"
    assert decision["action"] == "BUY"
    assert decision["buy_score"] >= 70
    assert decision["signal_count"] == 3


def test_a1_adaptive_core_observes_without_signals():
    decision = AdaptiveIntelligenceCore().evaluate([]).to_dict()

    assert decision["status"] == "OBSERVE"
    assert decision["action"] == "HOLD"
    assert decision["reasons"] == ["no_adaptive_signals"]


def test_a2_market_regime_classifies_trending_market():
    result = MarketRegimeIntelligenceV2().classify({
        "trend_strength": 78,
        "volatility_score": 55,
        "liquidity_score": 84,
        "spread_quality": 88,
        "structure_quality": 72,
    }).to_dict()

    assert result["status"] == "READY"
    assert result["regime"] == "TRENDING"
    assert result["action_bias"] == "FOLLOW_TREND"
    assert result["entry_threshold_adjustment"] < 0


def test_a2_market_regime_blocks_low_liquidity():
    result = MarketRegimeIntelligenceV2().classify({"liquidity_score": 20, "spread_quality": 80}).to_dict()

    assert result["regime"] == "LOW_LIQUIDITY"
    assert result["action_bias"] == "HOLD"
    assert result["risk_adjustment"] < 0


def test_a3_learning_optimizer_requires_minimum_samples():
    result = AdaptiveLearningOptimizer().optimize([
        {"outcome": "WIN", "entry_score": 72, "position_confidence": 66, "net_points": 120}
    ]).to_dict()

    assert result["status"] == "LEARNING"
    assert result["entry_threshold"] == 70


def test_a3_learning_optimizer_adjusts_conservatively_after_losses():
    samples = [
        {"outcome": "LOSS", "entry_score": 65, "position_confidence": 60, "net_points": -120},
        {"outcome": "LOSS", "entry_score": 66, "position_confidence": 59, "net_points": -80},
        {"outcome": "LOSS", "entry_score": 71, "position_confidence": 63, "net_points": -50},
        {"outcome": "WIN", "entry_score": 80, "position_confidence": 70, "net_points": 30},
        {"outcome": "LOSS", "entry_score": 62, "position_confidence": 58, "net_points": -40},
    ]
    result = AdaptiveLearningOptimizer().optimize(samples, {"entry_threshold": 70, "position_threshold": 62}).to_dict()

    assert result["status"] == "READY"
    assert result["entry_threshold"] > 70
    assert result["risk_adjustment"] < 0


def test_a4_runtime_allows_production_only_when_all_layers_align():
    samples = [{"outcome": "WIN", "entry_score": 75, "position_confidence": 68, "net_points": 100} for _ in range(6)]
    context = {
        "signals": [
            AdaptiveSignal("trend", side="BUY", score=82, confidence=88, weight=1.3),
            AdaptiveSignal("structure", side="BUY", score=78, confidence=84, weight=1.0),
            AdaptiveSignal("liquidity", side="BUY", score=76, confidence=80, weight=0.8),
        ],
        "regime_features": {"trend_strength": 76, "volatility_score": 55, "liquidity_score": 90, "spread_quality": 90, "structure_quality": 72},
        "learning_samples": samples,
        "base_thresholds": {"entry_threshold": 70, "position_threshold": 62},
    }

    result = ProductionMilestoneARuntime().evaluate(context).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["blockers"] == []


def test_a4_runtime_preserves_safe_hold_when_regime_disagrees():
    samples = [{"outcome": "WIN", "entry_score": 80, "position_confidence": 70, "net_points": 100} for _ in range(6)]
    context = {
        "signals": [{"name": "trend", "side": "BUY", "score": 90, "confidence": 90, "weight": 1}],
        "regime_features": {"liquidity_score": 15, "spread_quality": 80},
        "learning_samples": samples,
    }

    result = ProductionMilestoneARuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any("regime_requires_hold" in blocker for blocker in result["blockers"])
