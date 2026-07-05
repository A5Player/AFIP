from afip.intelligence.adaptive_intelligence_core import AdaptiveSignal
from afip.intelligence.adaptive_signal_calibrator import AdaptiveSignalCalibrator
from afip.intelligence.market_regime_transition_intelligence import MarketRegimeTransitionIntelligence
from afip.learning.adaptive_memory_store import AdaptiveMemoryStore
from afip.runtime.production_milestone_a_enhanced_runtime import ProductionMilestoneAEnhancedRuntime


def _winning_samples(count=6, group="trend"):
    return [
        {"group": group, "outcome": "WIN", "entry_score": 76, "position_confidence": 70, "net_points": 120}
        for _ in range(count)
    ]


def test_a1_pack_2_calibration_profile_positive_edge():
    profile = AdaptiveSignalCalibrator().build_profile("trend", _winning_samples())

    assert profile.status == "READY"
    assert profile.win_rate == 100.0
    assert profile.score_adjustment > 0


def test_a1_pack_2_calibration_keeps_backward_signal_contract():
    calibrator = AdaptiveSignalCalibrator()
    profile = calibrator.build_profile("trend", _winning_samples())
    signal = calibrator.calibrate_signal({"name": "trend_quality", "group": "trend", "side": "BUY", "score": 70, "confidence": 70}, profile)

    assert isinstance(signal, AdaptiveSignal)
    assert signal.score > 70
    assert "calibration_profile" in signal.metadata


def test_a1_pack_2_calibration_waits_for_samples():
    profile = AdaptiveSignalCalibrator(minimum_samples=5).build_profile("trend", _winning_samples(2))

    assert profile.status == "LEARNING"
    assert profile.score_adjustment == 0.0


def test_a2_pack_2_regime_transition_ready_when_stable():
    result = MarketRegimeTransitionIntelligence().evaluate([
        {"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "TRENDING"}
    ]).to_dict()

    assert result["status"] == "READY"
    assert result["risk_bias"] == "NORMAL_EXPOSURE"
    assert result["transition"] == "STABLE_TRENDING"


def test_a2_pack_2_regime_transition_reduces_exposure_on_change():
    result = MarketRegimeTransitionIntelligence().evaluate([
        {"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "RANGE_BOUND"}
    ]).to_dict()

    assert result["status"] == "CAUTION"
    assert result["risk_bias"] == "REDUCE_EXPOSURE"
    assert "TO_RANGE_BOUND" in result["transition"]


def test_a3_pack_2_memory_store_round_trip():
    store = AdaptiveMemoryStore(maximum_records=3)
    store.extend(_winning_samples(4))
    restored = AdaptiveMemoryStore.from_state(store.export_state())

    assert len(restored.records) == 3
    assert len(restored.by_group("trend")) == 3


def test_a4_pack_2_enhanced_runtime_allows_aligned_production():
    context = {
        "signals": [
            {"name": "trend_quality", "group": "trend", "side": "BUY", "score": 78, "confidence": 84, "weight": 1.2},
            {"name": "structure_quality", "group": "trend", "side": "BUY", "score": 76, "confidence": 82, "weight": 1.0},
        ],
        "learning_samples": _winning_samples(6),
        "regime_features": {"trend_strength": 78, "volatility_score": 55, "liquidity_score": 88, "spread_quality": 90, "structure_quality": 74},
        "regime_history": [{"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "TRENDING"}],
        "base_thresholds": {"entry_threshold": 70, "position_threshold": 62},
        "calibration_group": "trend",
    }

    result = ProductionMilestoneAEnhancedRuntime().evaluate(context).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["blockers"] == []


def test_a4_pack_2_enhanced_runtime_blocks_unstable_transition():
    context = {
        "signals": [{"name": "trend_quality", "group": "trend", "side": "BUY", "score": 85, "confidence": 88}],
        "learning_samples": _winning_samples(6),
        "regime_features": {"trend_strength": 78, "liquidity_score": 88, "spread_quality": 90, "structure_quality": 74},
        "regime_history": [{"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "RANGE_BOUND"}],
        "calibration_group": "trend",
    }

    result = ProductionMilestoneAEnhancedRuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any("regime_transition_requires_reduced_exposure" in item for item in result["blockers"])
