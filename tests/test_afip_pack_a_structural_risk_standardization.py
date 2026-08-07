import json

from afip.adaptive_sl import AdaptiveSLInput, AdaptiveSLRuntime, NORMAL_SL_APPROVED
from afip.position.position_sizer import PositionSizer
from afip.research_standardization import (
    ATRBufferCandidate,
    ATRBufferPatternObservation,
    PatternResearchIdentity,
    PatternShapeSignature,
    ResearchStandardizationCoordinator,
)


def _sl(**changes):
    values = dict(
        plan_id="PACK-A-PLAN", oqs=98.0, oqs_status="HIGH_QUALITY",
        adaptive_sl_review_status="ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW",
        final_confidence=98.0, evidence_quality="HIGH", capital_pass=True,
        risk_pass=True, execution_pass=True, reward_risk_pass=True,
        data_integrity_pass=True, atr_points=700, structure_points=900,
        buffer_points=75,
    )
    values.update(changes)
    return AdaptiveSLInput(**values)


def _identity():
    return PatternResearchIdentity(
        symbol="GOLD#", timeframe="M15", pattern_family="TREND_PULLBACK",
        pattern_name="BULL_FLAG", pattern_variant="LONG_LOWER_WICK", direction="BUY",
        market_regime="TREND", trend_state="UP", momentum_state="RECOVERING",
        volatility_state="NORMAL", trading_session="LONDON", liquidity_state="NORMAL",
        multi_timeframe_context="H1_UP", entry_plan="PULLBACK", management_plan="TRAIL",
        exit_plan="STRUCTURE_TARGET",
    )


def _shape():
    return PatternShapeSignature(
        candle_count=5, duration_seconds=4500, average_body_ratio=0.55,
        upper_wick_ratio=0.15, lower_wick_ratio=0.45, pullback_depth_atr=0.8,
        total_range_atr=1.2, slope_strength=0.7,
    )


def _observation(sequence):
    return ATRBufferPatternObservation(
        pattern_id=f"PATTERN-{sequence:06d}", pattern_sequence=sequence,
        context_segment_id="GOLD-M15-BULL-FLAG",
        candidate=ATRBufferCandidate(1.0, 75, "PLUS", 1.0, 100, "PLUS"),
        result_points=125.0, outcome="WIN", research_identity=_identity(),
        shape_signature=_shape(), cross_market_context_id="CROSS-MARKET-NORMAL",
    )


def test_stop_distance_is_structure_atr_buffer_without_fixed_band():
    result = AdaptiveSLRuntime().assess(_sl(atr_points=1800, structure_points=2200, buffer_points=125))
    assert result.status == NORMAL_SL_APPROVED
    assert result.recommended_sl_points == 2325
    assert result.hard_ceiling_points is None
    assert result.execution_authority is False


def test_structural_stop_fails_closed_without_research_review():
    result = AdaptiveSLRuntime().assess(_sl(adaptive_sl_review_status="NOT_ELIGIBLE"))
    assert result.status == "NOT_ELIGIBLE"
    assert result.reason == "research_standard_review_not_approved"


def test_wider_stop_holds_or_reduces_lot_and_can_fail_closed_below_minimum():
    sizer = PositionSizer(min_lot=0.01, max_lot=0.03, lot_step=0.01)
    assert sizer.calculate(1000, risk_usd=30, stop_loss_points=1000)["lot"] == 0.03
    assert sizer.calculate(1000, risk_usd=30, stop_loss_points=1500)["lot"] == 0.02
    blocked = sizer.calculate(1000, risk_usd=8, stop_loss_points=1000)
    assert blocked["eligible"] is False
    assert blocked["lot"] == 0.0
    assert blocked["reason"] == "minimum_lot_exceeds_approved_risk_budget"


def test_exact_shape_standard_updates_only_at_new_1000_milestones(tmp_path):
    coordinator = ResearchStandardizationCoordinator(str(tmp_path / "research"))
    for sequence in range(1, 1000):
        coordinator.append_atr_observation(_observation(sequence))
    waiting = coordinator.run()
    assert waiting["status"] == "WAITING"
    assert waiting["atr_observation_count"] == 999
    assert coordinator.run()["reason"] == "no_new_pattern_observations_since_last_evaluation"

    coordinator.append_atr_observation(_observation(1000))
    updated = coordinator.run()
    assert updated["status"] == "UPDATED"
    assert updated["standards_updated"] == 1

    standards = coordinator.dataset.records("atr_buffer_research_standards")
    assert len(standards) == 1
    standard = standards[0]["record"]
    assert standard["pattern_count"] == 1000
    assert standard["pattern_identity"]["pattern_name"] == "BULL_FLAG"
    assert standard["shape_bucket_key"]
    assert standard["automatic_production_promotion_allowed"] is False

    state = json.loads(coordinator.state_path.read_text(encoding="utf-8"))
    assert state["atr_observation_count"] == 1000
