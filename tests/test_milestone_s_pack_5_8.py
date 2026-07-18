import json
from pathlib import Path

import pytest

from afip.blind_forward_research import (
    BlindForwardResearchEngine, BlindForwardResultStore, CandidateSet,
    ForwardBar, ResearchCase, load_candidate_set,
)


def case(**changes):
    values = dict(
        case_id="case-001", instrument="GOLD#", timeframe="M15", direction="BUY",
        entry_price=3300.0, point_size=0.01, entry_at_utc="2026-07-18T10:00:00+00:00",
        market_regime="TREND", pattern_family="BREAKOUT", features={"score": 99.5},
        provenance={"source": "historical_closed_bars", "future_data_used": False},
        data_quality={"status": "PASS"},
    )
    values.update(changes)
    return ResearchCase(**values)


def candidates(**changes):
    values = dict(candidate_set_id="test", version="1", take_profit_points=(100,),
                  stop_loss_points=(100,), time_exit_bars=())
    values.update(changes)
    return CandidateSet(**values)


def bars(*rows):
    return [ForwardBar(*row) for row in rows]


def test_candidate_configuration_is_external_and_execution_neutral():
    config = json.loads(Path("config/blind_forward_research/candidate_sets.json").read_text(encoding="utf-8"))
    assert config["execution_authority"] == "NONE"
    assert load_candidate_set("config/blind_forward_research/candidate_sets.json").same_bar_resolution == "SL_FIRST"


def test_forward_bar_must_be_strictly_after_entry():
    with pytest.raises(ValueError, match="strictly after entry"):
        BlindForwardResearchEngine().evaluate(case(), candidates(), bars(("2026-07-18T10:00:00+00:00",3300,3301,3299,3300)))


def test_forward_bars_must_be_chronological():
    with pytest.raises(ValueError, match="chronological"):
        BlindForwardResearchEngine().evaluate(case(), candidates(), bars(
            ("2026-07-18T10:30:00+00:00",3300,3300.5,3299.5,3300),
            ("2026-07-18T10:15:00+00:00",3300,3300.5,3299.5,3300)))


def test_same_bar_collision_resolves_stop_loss_first():
    result = BlindForwardResearchEngine().evaluate(case(), candidates(), bars(
        ("2026-07-18T10:15:00+00:00",3300,3301.5,3298.5,3300)))
    outcome = result.outcomes[0]
    assert outcome.exit_reason == "STOP_LOSS"
    assert outcome.same_bar_collision is True
    assert outcome.result_points == -100


def test_take_profit_and_excursions_are_recorded():
    result = BlindForwardResearchEngine().evaluate(case(), candidates(), bars(
        ("2026-07-18T10:15:00+00:00",3300,3300.5,3299.8,3300.4),
        ("2026-07-18T10:30:00+00:00",3300.4,3301.2,3300.2,3301.0)))
    outcome = result.outcomes[0]
    assert outcome.exit_reason == "TAKE_PROFIT"
    assert outcome.result_points == 100
    assert outcome.maximum_favorable_excursion_points >= 100
    assert outcome.maximum_adverse_excursion_points == 20


def test_sell_direction_is_supported():
    result = BlindForwardResearchEngine().evaluate(case(direction="SELL"), candidates(), bars(
        ("2026-07-18T10:15:00+00:00",3300,3300.2,3298.8,3299.0)))
    assert result.outcomes[0].exit_reason == "TAKE_PROFIT"
    assert result.outcomes[0].result_points == 100


def test_time_exit_is_evaluated_as_separate_candidate():
    result = BlindForwardResearchEngine().evaluate(case(), candidates(time_exit_bars=(2,)), bars(
        ("2026-07-18T10:15:00+00:00",3300,3300.2,3299.8,3300.1),
        ("2026-07-18T10:30:00+00:00",3300.1,3300.4,3300.0,3300.3),
        ("2026-07-18T10:45:00+00:00",3300.3,3301.2,3300.2,3301.0)))
    assert len(result.outcomes) == 2
    timed = [x for x in result.outcomes if x.time_exit_bars == 2][0]
    assert timed.exit_reason == "TIME_EXIT"
    assert timed.holding_bars == 2


def test_input_hash_and_result_id_are_deterministic():
    engine = BlindForwardResearchEngine()
    sample_bars = bars(("2026-07-18T10:15:00+00:00",3300,3301.2,3299.8,3301))
    first = engine.evaluate(case(), candidates(), sample_bars)
    second = engine.evaluate(case(), candidates(), sample_bars)
    assert first.input_hash == second.input_hash
    assert first.result_id == second.result_id


def test_ineligible_case_is_quarantined_without_outcomes():
    result = BlindForwardResearchEngine().evaluate(case(data_quality={"status":"FAIL"}), candidates(), bars(
        ("2026-07-18T10:15:00+00:00",3300,3301.2,3299.8,3301)))
    assert result.research_eligibility == "QUARANTINED"
    assert "DATA_QUALITY_NOT_PASS" in result.quarantine_reasons
    assert result.outcomes == ()


def test_append_only_store_skips_duplicate(tmp_path):
    result = BlindForwardResearchEngine().evaluate(case(), candidates(), bars(
        ("2026-07-18T10:15:00+00:00",3300,3301.2,3299.8,3301)))
    store = BlindForwardResultStore(tmp_path)
    first = store.append(result)
    second = store.append(result)
    assert first.status == "APPENDED"
    assert second.status == "DUPLICATE_SKIPPED"
    assert len((tmp_path / first.relative_path).read_text(encoding="utf-8").splitlines()) == 1


def test_policy_is_shared_and_has_no_execution_promotion():
    policy=json.loads(Path("config/blind_forward_research/research_policy.json").read_text(encoding="utf-8"))
    assert policy["profiles_share_research_dataset"] is True
    assert policy["promotion_to_execution"] == "PROHIBITED"
    assert policy["same_bar_resolution"] == "SL_FIRST"


def test_module_has_no_broker_or_execution_imports():
    source=Path("afip/blind_forward_research/runtime.py").read_text(encoding="utf-8")
    forbidden=("order_send", "MetaTrader5", "demo_execution_gateway", "live_execution", "mt5.initialize")
    assert not any(token in source for token in forbidden)
