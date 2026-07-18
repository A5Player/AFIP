from datetime import datetime, timezone

import pytest

from afip.research_replay import (
    ChronologicalReplay,
    DecisionAlternativeRegistry,
    DynamicPyramidResearchGate,
    ExitAction,
    LegRole,
    PositionLegPlan,
    PositionPathAnalyzer,
    ReplayCandle,
    ResearchReplayBuilder,
)


def candles():
    return [
        ReplayCandle("2026-01-01T00:00:00Z", 100.0, 102.0, 99.0, 101.0),
        ReplayCandle("2026-01-01T01:00:00Z", 101.0, 105.0, 100.0, 104.0),
        ReplayCandle("2026-01-01T02:00:00Z", 104.0, 106.0, 98.0, 99.0),
        ReplayCandle("2026-01-02T00:00:00Z", 99.0, 110.0, 97.0, 108.0),
    ]


def test_replay_exposes_only_current_and_past_candles():
    replay = ChronologicalReplay(candles())
    context = replay.context_at(1)
    assert context.visible_candle_count == 2
    assert context.future_candle_count == 2
    assert context.future_data_exposed is False
    assert len(replay.visible_candles(1)) == 2


def test_replay_requires_strictly_increasing_timestamps():
    invalid = [candles()[1], candles()[0]]
    with pytest.raises(ValueError, match="strictly increasing"):
        ChronologicalReplay(invalid)


def test_replay_rejects_duplicate_timestamps():
    duplicate = [candles()[0], candles()[0]]
    with pytest.raises(ValueError, match="strictly increasing"):
        ChronologicalReplay(duplicate)


def test_position_path_metrics_for_buy():
    result = PositionPathAnalyzer.analyze(candles()[1:], direction="BUY", entry_price=101.0)
    assert result.maximum_favorable_excursion == 9.0
    assert result.maximum_adverse_excursion == 4.0
    assert result.final_return == 7.0


def test_position_path_metrics_for_sell():
    result = PositionPathAnalyzer.analyze(candles()[1:], direction="SELL", entry_price=104.0)
    assert result.maximum_favorable_excursion == 7.0
    assert result.maximum_adverse_excursion == 6.0
    assert result.final_return == -4.0


def test_one_to_three_legs_are_supported_without_forcing_three_roles():
    replay = ChronologicalReplay(candles())
    record = ResearchReplayBuilder.build(
        research_run_id="RUN-1",
        dataset_version="DATA-1",
        market_context_signature="TREND-H1",
        setup_id="SETUP-1",
        replay=replay,
        entry_index=0,
        direction="BUY",
        leg_plans=(PositionLegPlan("L1", LegRole.DYNAMIC, allow_overnight_hold=True),),
        now=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    assert len(record.leg_plans) == 1
    assert record.leg_plans[0]["role"] == "DYNAMIC"


def test_more_than_three_legs_is_rejected():
    replay = ChronologicalReplay(candles())
    legs = tuple(PositionLegPlan(f"L{i}", LegRole.DYNAMIC) for i in range(4))
    with pytest.raises(ValueError, match="one and three"):
        ResearchReplayBuilder.build(
            research_run_id="RUN-1",
            dataset_version="DATA-1",
            market_context_signature="TREND-H1",
            setup_id="SETUP-1",
            replay=replay,
            entry_index=0,
            direction="BUY",
            leg_plans=legs,
        )


def test_decision_alternatives_include_hold_close_trail_and_pyramid():
    alternatives = DecisionAlternativeRegistry.build(("L1", "L2"))
    actions = {value.action for value in alternatives}
    assert ExitAction.HOLD in actions
    assert ExitAction.CLOSE_ALL in actions
    assert ExitAction.TRAIL_STOP in actions
    assert ExitAction.PYRAMID_ADD in actions
    assert ExitAction.NO_PYRAMID in actions


def test_pyramid_requires_profit_risk_reduction_and_supportive_market():
    result = DynamicPyramidResearchGate.evaluate(
        {
            "position_profitable": True,
            "risk_reduced": True,
            "market_regime_supportive": True,
            "structure_intact": True,
            "trend_supportive": True,
            "current_total_risk": 0.5,
            "proposed_added_risk": 0.2,
            "maximum_total_risk": 1.0,
        }
    )
    assert result.allowed is True
    assert result.current_total_risk == 0.7


def test_overnight_status_alone_never_grants_pyramid():
    result = DynamicPyramidResearchGate.evaluate(
        {
            "held_overnight": True,
            "current_total_risk": 0.2,
            "proposed_added_risk": 0.2,
            "maximum_total_risk": 1.0,
        }
    )
    assert result.allowed is False
    assert "position_not_profitable" in result.block_reasons
    assert "existing_risk_not_reduced" in result.block_reasons


def test_pyramid_fails_when_total_risk_would_exceed_limit():
    result = DynamicPyramidResearchGate.evaluate(
        {
            "position_profitable": True,
            "risk_reduced": True,
            "market_regime_supportive": True,
            "structure_intact": True,
            "trend_supportive": True,
            "current_total_risk": 0.9,
            "proposed_added_risk": 0.2,
            "maximum_total_risk": 1.0,
        }
    )
    assert result.allowed is False
    assert "maximum_total_risk_exceeded" in result.block_reasons


def test_replay_record_is_experimental_and_auditable():
    replay = ChronologicalReplay(candles())
    record = ResearchReplayBuilder.build(
        research_run_id="RUN-2",
        dataset_version="DATA-2",
        market_context_signature="TREND-LONDON-H1",
        setup_id="SETUP-2",
        replay=replay,
        entry_index=1,
        direction="BUY",
        leg_plans=(
            PositionLegPlan("L1", LegRole.SHORT),
            PositionLegPlan("L2", LegRole.LONG, allow_overnight_hold=True),
        ),
        post_exit_observations={"M30": 1.5, "H1": 2.0, "H4": 4.0, "D1": 7.0},
        pyramid_inputs={
            "position_profitable": True,
            "risk_reduced": True,
            "market_regime_supportive": True,
            "structure_intact": True,
            "trend_supportive": True,
            "current_total_risk": 0.3,
            "proposed_added_risk": 0.2,
            "maximum_total_risk": 1.0,
        },
        now=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    assert record.research_state == "EXPERIMENTAL"
    assert record.replay_verified is True
    assert record.future_leakage_detected is False
    assert record.post_exit_observations["D1"] == 7.0
    assert record.pyramid_research["allowed"] is True
    assert len(record.record_checksum) == 64


def test_duplicate_leg_ids_are_rejected():
    replay = ChronologicalReplay(candles())
    with pytest.raises(ValueError, match="unique"):
        ResearchReplayBuilder.build(
            research_run_id="RUN-3",
            dataset_version="DATA-3",
            market_context_signature="RANGE-H1",
            setup_id="SETUP-3",
            replay=replay,
            entry_index=0,
            direction="SELL",
            leg_plans=(
                PositionLegPlan("L1", LegRole.SHORT),
                PositionLegPlan("L1", LegRole.LONG),
            ),
        )


def test_replay_builder_requires_research_identifiers():
    replay = ChronologicalReplay(candles())
    with pytest.raises(ValueError, match="required replay identifiers"):
        ResearchReplayBuilder.build(
            research_run_id="",
            dataset_version="DATA-4",
            market_context_signature="TREND-H1",
            setup_id="SETUP-4",
            replay=replay,
            entry_index=0,
            direction="BUY",
            leg_plans=(PositionLegPlan("L1", LegRole.DYNAMIC),),
        )
