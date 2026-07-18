from afip.protection.adaptive_rr_portfolio import AdaptiveRRProtectionPlanner
from afip.execution.protected_simulation_order_builder import ProtectedSimulationOrderBuilder


def test_rr_means_reward_divided_by_risk_and_three_plans_are_distinct():
    result = AdaptiveRRProtectionPlanner().plan_portfolio(
        action="BUY", entry_price=3000.0, unit_count=3, profile_id="P1",
        confidence=99.8, snapshot={"atr_points": 100}, regime="TREND", point_size=0.01,
    )
    assert result["status"] == "PLANNED"
    assert result["rr_definition"] == "reward_distance / initial_risk_distance"
    plans = result["unit_plans"]
    assert [p["role"] for p in plans] == ["RR_NEAR", "RR_CORE", "RR_RUNNER"]
    assert len({p["take_profit_points"] for p in plans}) == 3
    assert all(p["take_profit_points"] == p["stop_loss_points"] * p["rr_target"] for p in plans)


def test_validated_research_overrides_fallback_stop_and_rr_targets():
    result = AdaptiveRRProtectionPlanner().plan_portfolio(
        action="SELL", entry_price=3000.0, unit_count=3, profile_id="P2", confidence=100,
        snapshot={}, research={"validated": True, "sample_size": 100,
        "recommended_stop_points": 240, "validated_rr_targets": [0.9, 1.8, 3.6]},
        regime="RANGE", point_size=0.01,
    )
    assert result["research_evidence_sufficient"] is True
    assert [p["rr_target"] for p in result["unit_plans"]] == [0.9, 1.8, 3.6]
    assert all(p["stop_loss_points"] == 240 for p in result["unit_plans"])


def test_confidence_maps_to_maximum_units_not_mandatory_units():
    assert ProtectedSimulationOrderBuilder._confidence_units(97.99) == 0
    assert ProtectedSimulationOrderBuilder._confidence_units(98.0) == 1
    assert ProtectedSimulationOrderBuilder._confidence_units(98.5) == 2
    assert ProtectedSimulationOrderBuilder._confidence_units(99.5) == 3


def test_one_unit_uses_core_or_runner_not_forced_near():
    planner = AdaptiveRRProtectionPlanner()
    normal = planner.plan_portfolio(action="BUY", entry_price=3000, unit_count=1, profile_id="P1", confidence=98.2, snapshot={"atr_points": 100}, regime="RANGE")
    trend = planner.plan_portfolio(action="BUY", entry_price=3000, unit_count=1, profile_id="P1", confidence=98.2, snapshot={"atr_points": 100}, regime="TREND")
    assert normal["unit_plans"][0]["role"] == "RR_CORE"
    assert trend["unit_plans"][0]["role"] == "RR_RUNNER"


def test_profile_giveback_is_more_conservative_for_p1_than_p3():
    planner = AdaptiveRRProtectionPlanner()
    p1 = planner.plan_portfolio(action="BUY", entry_price=3000, unit_count=3, profile_id="P1", confidence=100, snapshot={"atr_points": 100})
    p3 = planner.plan_portfolio(action="BUY", entry_price=3000, unit_count=3, profile_id="P3", confidence=100, snapshot={"atr_points": 100})
    assert p1["unit_plans"][2]["maximum_giveback_r"] < p3["unit_plans"][2]["maximum_giveback_r"]
