from pathlib import Path

import pytest

from afip.adaptive_plan_ranking import (
    AdaptiveMultiObjectivePlanRanker,
    CapitalPreservationPolicy,
    ContextAwareWeightAdapter,
    DEFAULT_PROFILE_WEIGHTS,
    MarketRankingContext,
    PlanEvidence,
)
from afip.historical_replay_research import AppendOnlyResearchDataset


def plan(**overrides):
    values = dict(
        plan_id="PLAN-1", plan_name="Balanced Breakout", pattern_name="BREAKOUT",
        situation_name="TREND_HIGH_LIQUIDITY", sample_size=500,
        maximum_drawdown_percent=8.0, average_drawdown_percent=3.0,
        drawdown_duration_score=85.0, risk_of_ruin_percent=0.2,
        worst_losing_streak=5, tail_loss_r=2.0, capital_survival_rate=99.0,
        context_match_score=90.0, walk_forward_score=85.0, robustness_score=82.0,
        data_quality_score=95.0, temporal_stability_score=80.0,
        parameter_stability_score=78.0, return_to_drawdown_score=88.0,
        profit_factor_score=82.0, expectancy_score=80.0,
        conservative_win_rate=68.0, normalized_profit_score=75.0,
        raw_net_profit=1200.0, context_tags={"regime": "TREND"},
    )
    values.update(overrides)
    return PlanEvidence(**values)


def test_default_profiles_exist():
    assert set(DEFAULT_PROFILE_WEIGHTS) == {"P1", "P2", "P3", "P4"}


def test_profile_weights_normalize_to_one():
    for weights in DEFAULT_PROFILE_WEIGHTS.values():
        assert sum(weights.normalized().__dict__.values()) == pytest.approx(1.0)


def test_high_volatility_increases_capital_weight():
    adapter = ContextAwareWeightAdapter()
    base = DEFAULT_PROFILE_WEIGHTS["P2"].normalized()
    adapted = adapter.adapt(DEFAULT_PROFILE_WEIGHTS["P2"], MarketRankingContext(volatility="HIGH"))
    assert adapted.capital_preservation > base.capital_preservation
    assert adapted.normalized_profit < base.normalized_profit


def test_capital_gate_rejects_high_drawdown():
    ranker = AdaptiveMultiObjectivePlanRanker()
    result = ranker.rank([plan(maximum_drawdown_percent=25.0)], ranking_id="R1", profile_id="P1", context=MarketRankingContext())
    assert result.selected_plan_id is None
    assert "maximum_drawdown_above_policy" in result.ranked_plans[0].rejection_reasons


def test_capital_gate_rejects_risk_of_ruin():
    result = AdaptiveMultiObjectivePlanRanker().rank(
        [plan(risk_of_ruin_percent=4.0)], ranking_id="R2", profile_id="P2", context=MarketRankingContext())
    assert not result.ranked_plans[0].capital_preservation_passed


def test_evidence_gate_rejects_small_sample():
    result = AdaptiveMultiObjectivePlanRanker().rank(
        [plan(sample_size=20)], ranking_id="R3", profile_id="P2", context=MarketRankingContext())
    assert "sample_size_below_policy" in result.ranked_plans[0].rejection_reasons


def test_context_match_precedes_composite_score():
    best_context = plan(plan_id="CTX", plan_name="Context", context_match_score=95.0, normalized_profit_score=50.0)
    high_profit = plan(plan_id="PROFIT", plan_name="Profit", context_match_score=70.0, normalized_profit_score=100.0, raw_net_profit=9999)
    result = AdaptiveMultiObjectivePlanRanker().rank(
        [high_profit, best_context], ranking_id="R4", profile_id="P2", context=MarketRankingContext(regime="TREND"))
    assert result.selected_plan_id == "CTX"


def test_profit_does_not_override_capital_gate():
    unsafe = plan(plan_id="UNSAFE", raw_net_profit=100000, normalized_profit_score=100, maximum_drawdown_percent=40)
    safe = plan(plan_id="SAFE", raw_net_profit=1000, normalized_profit_score=60)
    result = AdaptiveMultiObjectivePlanRanker().rank([unsafe, safe], ranking_id="R5", profile_id="P3", context=MarketRankingContext())
    assert result.selected_plan_id == "SAFE"


def test_drawdown_breaks_equal_score_tie():
    low_dd = plan(plan_id="LOW", plan_name="A", maximum_drawdown_percent=5)
    high_dd = plan(plan_id="HIGH", plan_name="B", maximum_drawdown_percent=9)
    result = AdaptiveMultiObjectivePlanRanker().rank([high_dd, low_dd], ranking_id="R6", profile_id="P2", context=MarketRankingContext())
    assert result.ranked_plans[0].plan_id == "LOW"


def test_name_is_last_deterministic_tie_breaker():
    a = plan(plan_id="2", plan_name="Alpha")
    b = plan(plan_id="1", plan_name="Beta")
    result = AdaptiveMultiObjectivePlanRanker().rank([b, a], ranking_id="R7", profile_id="P2", context=MarketRankingContext())
    assert result.ranked_plans[0].plan_name == "Alpha"


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        AdaptiveMultiObjectivePlanRanker().rank([plan()], ranking_id="R8", profile_id="P5", context=MarketRankingContext())


def test_result_persists_append_only(tmp_path: Path):
    ranker = AdaptiveMultiObjectivePlanRanker(tmp_path)
    ranker.rank([plan()], ranking_id="R9", profile_id="P1", context=MarketRankingContext())
    dataset = AppendOnlyResearchDataset(tmp_path)
    assert dataset.count("adaptive_plan_rankings") == 1
    record = dataset.records("adaptive_plan_rankings")[0]
    assert record["previous_chain_checksum"] == "GENESIS"
    assert record["chain_checksum"]


def test_dashboard_top10_and_top100_are_written(tmp_path: Path):
    plans = [plan(plan_id=f"P-{i}", plan_name=f"Plan {i}", context_match_score=100-i/2) for i in range(120)]
    AdaptiveMultiObjectivePlanRanker(tmp_path).rank(plans, ranking_id="R10", profile_id="P2", context=MarketRankingContext())
    record = AppendOnlyResearchDataset(tmp_path).records("dashboard_research_rankings")[-1]["record"]
    assert len(record["top_10"]) == 10
    assert len(record["top_100"]) == 100
    assert record["hidden_record_count"] == 20


def test_ranking_contains_pattern_and_situation_names():
    result = AdaptiveMultiObjectivePlanRanker().rank([plan()], ranking_id="R11", profile_id="P1", context=MarketRankingContext())
    item = result.ranked_plans[0]
    assert item.pattern_name == "BREAKOUT"
    assert item.situation_name == "TREND_HIGH_LIQUIDITY"


def test_no_execution_permission_field_is_created():
    result = AdaptiveMultiObjectivePlanRanker().rank([plan()], ranking_id="R12", profile_id="P1", context=MarketRankingContext())
    payload = result.as_dict()
    assert "execution_allowed" not in payload
    assert "order_send" not in str(payload).lower()


def test_custom_capital_policy_is_enforced():
    ranker = AdaptiveMultiObjectivePlanRanker(capital_policy=CapitalPreservationPolicy(maximum_drawdown_percent=5))
    result = ranker.rank([plan(maximum_drawdown_percent=6)], ranking_id="R13", profile_id="P1", context=MarketRankingContext())
    assert result.selected_plan_id is None
