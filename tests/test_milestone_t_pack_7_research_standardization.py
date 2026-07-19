from pathlib import Path
import json
import pytest

from afip.research_standardization import (
    HistoricalCoveragePlanner, InitialStandardPolicy, ResearchDerivedStandardRegistry,
    ResearchLineage, StandardContext, StandardizationPolicy,
)


def context(**overrides):
    values = dict(symbol_family="PRECIOUS_METAL", market_regime="TRENDING", market_structure="BULLISH",
                  liquidity_state="NORMAL", trend_state="UP", volatility_state="MEDIUM",
                  trading_session="LONDON", direction="BUY", pattern_family="BREAKOUT")
    values.update(overrides)
    return StandardContext(**values)


def lineage(**overrides):
    values = dict(policy_id="EXIT_A", policy_version="1.0", evidence_record_checksum="e"*64,
                  source_dataset_checksums=("a"*64, "b"*64), walk_forward_run_count=5,
                  robustness_scenario_count=8, total_forward_sample_size=500,
                  historical_start="2010-01-01", historical_end="2026-07-18",
                  source_instruments=("GOLD#", "DXY", "USOIL"))
    values.update(overrides)
    return ResearchLineage(**values)


def standard(**overrides):
    values = dict(standard_id="STD_EXIT_GOLD_BREAKOUT", standard_version="1.0.0", context=context(),
                  policy_id="EXIT_A", policy_parameters={"tp_r": 2.0, "sl_r": 1.0, "trailing": True},
                  lineage=lineage(), evidence_score=88.0, temporal_stability_score=82.0,
                  resilience_score=79.0, owner_approved=True, approval_reference="OWNER_DECISION_2026_07_19")
    values.update(overrides)
    return InitialStandardPolicy(**values)


def test_context_segment_is_deterministic():
    assert context().segment_id == context().segment_id


def test_exact_context_match_scores_100():
    assert context().match_score(context()) == 100.0


def test_context_mismatch_scores_zero():
    assert context().match_score(context(direction="SELL")) == 0.0


def test_any_fields_allow_general_standard():
    broad = context(trading_session="ANY")
    assert broad.match_score(context(trading_session="NEW_YORK")) == 100.0


def test_lineage_requires_checksums():
    with pytest.raises(ValueError):
        lineage(source_dataset_checksums=())


def test_lineage_requires_positive_evidence_counts():
    with pytest.raises(ValueError):
        lineage(total_forward_sample_size=0)


def test_active_standard_requires_owner_approval():
    with pytest.raises(ValueError):
        standard(owner_approved=False)


def test_registry_rejects_low_evidence():
    registry = ResearchDerivedStandardRegistry()
    with pytest.raises(ValueError):
        registry.register(standard(evidence_score=10.0))


def test_registry_rejects_low_stability():
    registry = ResearchDerivedStandardRegistry()
    with pytest.raises(ValueError):
        registry.register(standard(temporal_stability_score=10.0))


def test_registry_rejects_low_resilience():
    registry = ResearchDerivedStandardRegistry()
    with pytest.raises(ValueError):
        registry.register(standard(resilience_score=10.0))


def test_registry_registers_owner_approved_initial_standard():
    registry = ResearchDerivedStandardRegistry()
    item = registry.register(standard())
    assert item.production_usable is True
    assert item.standard_class == "RESEARCH_DERIVED_INITIAL_STANDARD"


def test_registry_never_authorizes_order_execution():
    with pytest.raises(ValueError):
        standard(automatic_order_execution_allowed=True)


def test_registry_rejects_duplicate_version():
    registry = ResearchDerivedStandardRegistry()
    registry.register(standard())
    with pytest.raises(ValueError):
        registry.register(standard())


def test_selection_uses_matching_initial_standard():
    registry = ResearchDerivedStandardRegistry()
    registry.register(standard())
    result = registry.select(context(), "SEL-1")
    assert result.selection_status == "SELECTED_INITIAL_STANDARD"
    assert result.selected_policy_id == "EXIT_A"
    assert result.selected_parameters["tp_r"] == 2.0


def test_selection_blocks_wrong_context():
    registry = ResearchDerivedStandardRegistry()
    registry.register(standard())
    result = registry.select(context(direction="SELL"), "SEL-2")
    assert result.selection_status == "NO_MATCH"


def test_selection_prefers_stronger_evidence():
    registry = ResearchDerivedStandardRegistry()
    registry.register(standard(standard_id="A", policy_id="P1", evidence_score=75.0))
    registry.register(standard(standard_id="B", policy_id="P2", evidence_score=95.0,
                               lineage=lineage(policy_id="P2")))
    assert registry.select(context(), "SEL-3").selected_policy_id == "P2"


def test_supersede_replaces_active_version():
    registry = ResearchDerivedStandardRegistry()
    registry.register(standard())
    replacement = standard(standard_version="1.1.0", policy_parameters={"tp_r": 2.2})
    registry.supersede("STD_EXIT_GOLD_BREAKOUT", "1.0.0", replacement)
    assert len(registry.active_standards()) == 1
    assert registry.active_standards()[0].standard_version == "1.1.0"


def test_dataset_persists_versions_and_selections(tmp_path: Path):
    registry = ResearchDerivedStandardRegistry(str(tmp_path))
    registry.register(standard())
    registry.select(context(), "SEL-4")
    assert (tmp_path / "research_standard_versions.jsonl").exists()
    assert (tmp_path / "research_standard_selections.jsonl").exists()


def test_historical_plan_requests_earliest_available():
    plan = HistoricalCoveragePlanner().build_default()
    assert all(item.earliest_available_required for item in plan.requests)
    assert all(item.end_at_latest_closed_bar for item in plan.requests)


def test_historical_plan_includes_gold_usd_oil_and_indices():
    instruments = {item.instrument for item in HistoricalCoveragePlanner().build_default().requests}
    assert {"GOLD#", "DXY", "EURUSD", "USOIL", "UKOIL", "US500", "US30"} <= instruments


def test_historical_plan_has_multi_timeframe_depth():
    plan = HistoricalCoveragePlanner().build_default()
    gold = next(item for item in plan.requests if item.instrument == "GOLD#")
    assert {"M1", "M5", "M15", "M30", "H1", "H4", "D1"} <= set(gold.timeframes)


def test_historical_plan_checksum_is_deterministic():
    planner = HistoricalCoveragePlanner()
    assert planner.build_default().plan_checksum == planner.build_default().plan_checksum


def test_historical_plan_persists_append_only(tmp_path: Path):
    planner = HistoricalCoveragePlanner()
    result = planner.persist(planner.build_default(), str(tmp_path))
    assert result["dataset_name"] == "historical_coverage_plans"
    assert (tmp_path / "historical_coverage_plans.jsonl").exists()


def test_custom_policy_can_require_higher_match():
    policy = StandardizationPolicy(minimum_context_match_score=100.0)
    registry = ResearchDerivedStandardRegistry(policy=policy)
    registry.register(standard(context=context(trading_session="ANY")))
    assert registry.select(context(trading_session="ASIA"), "SEL-5").selection_status == "SELECTED_INITIAL_STANDARD"
