from pathlib import Path

import pytest

from afip.exit_outcome_research import (
    ExitOutcomeResearchEngine,
    ExitPolicyExperimentRunner,
    ExitResearchPolicy,
    PositionResearchCase,
)
from afip.historical_replay_research import AppendOnlyResearchDataset


def candles():
    return [
        {"timestamp_utc": "2026-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99.5, "close": 100.5, "volume": 10},
        {"timestamp_utc": "2026-01-01T01:00:00Z", "open": 100.5, "high": 103, "low": 100, "close": 102.5, "volume": 12},
        {"timestamp_utc": "2026-01-01T02:00:00Z", "open": 102.5, "high": 104, "low": 101.5, "close": 103.5, "volume": 13},
        {"timestamp_utc": "2026-01-01T03:00:00Z", "open": 103.5, "high": 103.8, "low": 101, "close": 101.5, "volume": 14},
    ]


def dataset(tmp_path):
    return AppendOnlyResearchDataset(tmp_path / "research" / "experimental" / "exit-pack-4")


def case(direction="BUY", entry_price=100, entry_index=0):
    return PositionResearchCase(
        position_case_id="CASE-1",
        replay_id="REPLAY-1",
        research_run_id="RUN-1",
        dataset_version="DATA-T4-1",
        scenario_id="GOLD-H1-EXIT-1",
        direction=direction,
        entry_index=entry_index,
        entry_price=entry_price,
    )


def test_dynamic_profit_target_closes_position(tmp_path):
    store = dataset(tmp_path)
    engine = ExitOutcomeResearchEngine(store)
    outcome = engine.evaluate(
        case=case(),
        policy=ExitResearchPolicy("TP-2R", initial_risk_distance=2, profit_target_distance=4),
        candles=candles(),
    )
    assert outcome.exit_reason == "PROFIT_TARGET"
    assert outcome.realized_r == 2.0
    assert outcome.outcome_classification == "STRONG_PROFIT"


def test_initial_stop_uses_conservative_same_bar_assumption(tmp_path):
    values = candles()
    values[0] = {**values[0], "low": 97.5, "high": 106}
    outcome = ExitOutcomeResearchEngine(dataset(tmp_path)).evaluate(
        case=case(),
        policy=ExitResearchPolicy("STOP-FIRST", initial_risk_distance=2, profit_target_distance=4),
        candles=values,
    )
    assert outcome.exit_reason == "STOP_OR_LOSS_CONTROL"
    assert outcome.realized_r == -1.0


def test_break_even_research_moves_stop_after_trigger(tmp_path):
    store = dataset(tmp_path)
    outcome = ExitOutcomeResearchEngine(store).evaluate(
        case=case(),
        policy=ExitResearchPolicy("BE", initial_risk_distance=2, break_even_trigger_r=1.0),
        candles=candles(),
    )
    records = store.records("exit_alternatives")
    assert any("break_even_trigger_reached" in item["record"]["reason_codes"] for item in records)
    assert any(item["record"]["active_stop_price"] == 100 for item in records)
    assert outcome.realized_r >= 0.0


def test_trailing_stop_research_records_dynamic_stop(tmp_path):
    store = dataset(tmp_path)
    ExitOutcomeResearchEngine(store).evaluate(
        case=case(),
        policy=ExitResearchPolicy(
            "TRAIL", initial_risk_distance=2, trailing_trigger_r=1.0, trailing_distance_r=0.5
        ),
        candles=candles(),
    )
    records = store.records("exit_alternatives")
    assert any("trailing_trigger_reached" in item["record"]["reason_codes"] for item in records)
    assert any(item["record"]["active_stop_price"] > 98 for item in records)
    assert all(item["record"]["production_usable"] is False for item in records)


def test_maximum_holding_period_closes_at_visible_close(tmp_path):
    outcome = ExitOutcomeResearchEngine(dataset(tmp_path)).evaluate(
        case=case(),
        policy=ExitResearchPolicy("TIME", initial_risk_distance=10, maximum_holding_bars=2),
        candles=candles(),
    )
    assert outcome.exit_reason == "MAXIMUM_HOLDING_PERIOD"
    assert outcome.exit_index == 1
    assert outcome.exit_price == 102.5


def test_end_of_replay_classifies_controlled_profit(tmp_path):
    outcome = ExitOutcomeResearchEngine(dataset(tmp_path)).evaluate(
        case=case(),
        policy=ExitResearchPolicy("HOLD", initial_risk_distance=10),
        candles=candles(),
    )
    assert outcome.exit_reason == "END_OF_REPLAY"
    assert outcome.outcome_classification == "CONTROLLED_PROFIT"


def test_sell_direction_supports_target_and_stop(tmp_path):
    values = [
        {"timestamp_utc": "2026-01-01T00:00:00Z", "open": 100, "high": 100.5, "low": 99, "close": 99.5, "volume": 1},
        {"timestamp_utc": "2026-01-01T01:00:00Z", "open": 99.5, "high": 100, "low": 95, "close": 96, "volume": 1},
    ]
    outcome = ExitOutcomeResearchEngine(dataset(tmp_path)).evaluate(
        case=case(direction="SELL"),
        policy=ExitResearchPolicy("SELL-TP", initial_risk_distance=2, profit_target_distance=4),
        candles=values,
    )
    assert outcome.exit_reason == "PROFIT_TARGET"
    assert outcome.realized_r == 2.0


def test_outcome_contains_mfe_mae_and_exit_quality(tmp_path):
    outcome = ExitOutcomeResearchEngine(dataset(tmp_path)).evaluate(
        case=case(), policy=ExitResearchPolicy("QUALITY", initial_risk_distance=2), candles=candles()
    )
    assert outcome.maximum_favorable_excursion_r == 2.0
    assert outcome.maximum_adverse_excursion_r == 0.25
    assert 0 <= outcome.exit_quality_score <= 100
    assert 0 <= outcome.capital_preservation_score <= 100


def test_position_lifecycle_and_outcome_datasets_are_append_only(tmp_path):
    store = dataset(tmp_path)
    ExitOutcomeResearchEngine(store).evaluate(
        case=case(), policy=ExitResearchPolicy("DATA", initial_risk_distance=2), candles=candles()
    )
    assert store.count("position_lifecycles") >= 1
    assert store.count("position_outcomes") == 1
    assert store.count("exit_quality") == 1
    assert all(store.verify(name) for name in store.DATASET_NAMES)


def test_dashboard_metadata_includes_research_expansion(tmp_path):
    store = dataset(tmp_path)
    ExitOutcomeResearchEngine(store).evaluate(
        case=case(), policy=ExitResearchPolicy("META", initial_risk_distance=2), candles=candles()
    )
    metadata = store.dashboard_metadata()
    assert metadata["dataset_counts"]["position_outcomes"] == 1
    assert metadata["dataset_counts"]["exit_alternatives"] >= 1
    assert metadata["production_usable"] is False


def test_experiment_runner_compares_policies_without_selecting_winner(tmp_path):
    store = dataset(tmp_path)
    outcomes = ExitPolicyExperimentRunner(store).run(
        case=case(),
        policies=(
            ExitResearchPolicy("HOLD", initial_risk_distance=2),
            ExitResearchPolicy("TP", initial_risk_distance=2, profit_target_distance=4),
        ),
        candles=candles(),
    )
    assert [item.policy_id for item in outcomes] == ["HOLD", "TP"]
    assert store.count("position_outcomes") == 2


def test_experiment_runner_rejects_duplicate_policy_ids(tmp_path):
    with pytest.raises(ValueError, match="unique"):
        ExitPolicyExperimentRunner(dataset(tmp_path)).run(
            case=case(),
            policies=(
                ExitResearchPolicy("DUP", initial_risk_distance=2),
                ExitResearchPolicy("DUP", initial_risk_distance=3),
            ),
            candles=candles(),
        )


def test_policy_validation_rejects_invalid_distances():
    with pytest.raises(ValueError, match="initial_risk_distance"):
        ExitResearchPolicy("BAD", initial_risk_distance=0)
    with pytest.raises(ValueError, match="trailing_distance_r"):
        ExitResearchPolicy("BAD", initial_risk_distance=1, trailing_distance_r=0)


def test_case_validation_rejects_invalid_direction():
    with pytest.raises(ValueError, match="BUY or SELL"):
        case(direction="WAIT")


def test_engine_rejects_non_chronological_candles(tmp_path):
    values = list(reversed(candles()))
    with pytest.raises(ValueError, match="chronological"):
        ExitOutcomeResearchEngine(dataset(tmp_path)).evaluate(
            case=case(), policy=ExitResearchPolicy("ORDER", initial_risk_distance=2), candles=values
        )


def test_engine_rejects_entry_outside_replay(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        ExitOutcomeResearchEngine(dataset(tmp_path)).evaluate(
            case=case(entry_index=9), policy=ExitResearchPolicy("ENTRY", initial_risk_distance=2), candles=candles()
        )


def test_all_records_remain_experimental_and_quarantined(tmp_path):
    store = dataset(tmp_path)
    ExitOutcomeResearchEngine(store).evaluate(
        case=case(), policy=ExitResearchPolicy("QUARANTINE", initial_risk_distance=2), candles=candles()
    )
    for name in ("position_lifecycles", "exit_alternatives", "position_outcomes", "exit_quality"):
        for envelope in store.records(name):
            assert envelope["record"]["research_state"] == "EXPERIMENTAL"
            assert envelope["record"]["production_usable"] is False


def test_module_contains_no_mt5_or_production_execution_calls():
    source = Path("afip/exit_outcome_research/runtime.py").read_text(encoding="utf-8")
    forbidden = ("order_send(", "order_check(", "positions_get(", "MetaTrader5", "production_runtime")
    assert not any(value in source for value in forbidden)
