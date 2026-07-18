import json
from dataclasses import replace
from pathlib import Path

import pytest

from afip.research_metrics import (ResearchLeaderboardEngine, ResearchMetricsEngine,
    ResearchObservation, observations_from_blind_forward_result, write_report)


def obs(points=100.0, **changes):
    values=dict(result_id="r1", case_id="c1", candidate_set_id="set", candidate_set_version="1",
        take_profit_points=100, stop_loss_points=50, time_exit_bars=None, result_points=points,
        outcome="WIN" if points>0 else "LOSS" if points<0 else "FLAT", exit_reason="TAKE_PROFIT" if points>0 else "STOP_LOSS",
        holding_bars=2, holding_seconds=1800, maximum_favorable_excursion_points=max(points,120),
        maximum_adverse_excursion_points=30, market_regime="TREND", pattern_family="BREAKOUT",
        confidence_bucket="98_100", direction="BUY", timeframe="M15")
    values.update(changes)
    return ResearchObservation(**values)


def test_policy_is_execution_neutral():
    policy=json.loads(Path("config/research_metrics/leaderboard_policy.json").read_text(encoding="utf-8"))
    assert policy["execution_authority"] == "NONE"
    assert policy["promotion_to_execution"] == "PROHIBITED"


def test_metrics_cover_expectancy_profit_factor_and_ci():
    m=ResearchMetricsEngine().summarize([obs(100,result_id="1"),obs(-50,result_id="2"),obs(50,result_id="3")])
    assert m.sample_count == 3 and m.win_rate == pytest.approx(66.66666667)
    assert m.expectancy_points == pytest.approx(33.33333333)
    assert m.profit_factor == 3.0
    assert m.confidence_interval_95_low < m.confidence_interval_95_high


def test_zero_loss_profit_factor_is_explicit_none():
    m=ResearchMetricsEngine().summarize([obs(10,result_id="1"),obs(20,result_id="2")])
    assert m.profit_factor is None


def test_empty_metrics_rejected():
    with pytest.raises(ValueError, match="at least one"):
        ResearchMetricsEngine().summarize([])


def test_leaderboard_groups_and_ranks_deterministically():
    rows=[]
    for i in range(30): rows.append(obs(100,result_id=f"a{i}",take_profit_points=100))
    for i in range(30): rows.append(obs(20,result_id=f"b{i}",case_id=f"b{i}",take_profit_points=200))
    report=ResearchLeaderboardEngine(30).build("tp",rows,["take_profit_points"])
    assert report.ranked_rows[0].group_values["take_profit_points"] == 100
    assert report.ranked_rows[0].eligible_for_ranking is True
    assert report.execution_authority == "NONE"


def test_low_sample_is_retained_but_not_eligible():
    report=ResearchLeaderboardEngine(30).build("pattern",[obs(100,result_id=str(i)) for i in range(3)],["pattern_family"])
    assert report.ranked_rows[0].eligible_for_ranking is False
    assert "MINIMUM_SAMPLE_NOT_MET" in report.ranked_rows[0].exclusion_reasons


def test_non_positive_confidence_interval_blocks_ranking():
    rows=[obs(100,result_id=f"w{i}") for i in range(15)] + [obs(-100,result_id=f"l{i}") for i in range(15)]
    report=ResearchLeaderboardEngine(30).build("mixed",rows,["pattern_family"])
    assert "CONFIDENCE_INTERVAL_NOT_POSITIVE" in report.ranked_rows[0].exclusion_reasons


def test_duplicate_observation_is_deduplicated():
    item=obs()
    report=ResearchLeaderboardEngine(1).build("x",[item,item],["pattern_family"])
    assert report.source_observation_count == 1


def test_unsupported_dimension_rejected():
    with pytest.raises(ValueError, match="unsupported"):
        ResearchLeaderboardEngine().build("x",[obs()],["profile_id"])


def test_blind_forward_conversion_rejects_execution_authority():
    result={"research_eligibility":"ELIGIBLE","execution_authority":"LIVE","result_id":"r","case_id":"c","outcomes":[]}
    with pytest.raises(ValueError, match="authority NONE"):
        observations_from_blind_forward_result(result)


def test_quarantined_result_produces_no_observations():
    assert observations_from_blind_forward_result({"research_eligibility":"QUARANTINED"}) == ()


def test_report_write_is_deterministic(tmp_path):
    rows=[obs(100,result_id=f"r{i}") for i in range(30)]
    report=ResearchLeaderboardEngine(30).build("pattern",rows,["pattern_family"])
    first=write_report(report,tmp_path/"a.json")
    second=write_report(report,tmp_path/"b.json")
    assert first == second
    assert (tmp_path/"a.json").read_bytes() == (tmp_path/"b.json").read_bytes()


def test_module_has_no_broker_or_order_authority():
    source=Path("afip/research_metrics/runtime.py").read_text(encoding="utf-8")
    forbidden=("MetaTrader5","order_send","demo_execution_gateway","live_execution","mt5.initialize")
    assert not any(x in source for x in forbidden)
