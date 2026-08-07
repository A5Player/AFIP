import json

from afip.dashboard_ui.dashboard_authority import DashboardAuthority
from afip.four_profile_operations import (
    FourProfileOperationalRuntime,
    ProfileTradingModeAuthority,
)
from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_standardization import (
    InitialCapitalObservation,
    InitialCapitalStandardizer,
    PatternResearchIdentity,
    PatternShapeSignature,
    SingleUnitProfitObservation,
    SingleUnitProfitStandardizer,
)


def identity():
    return PatternResearchIdentity(
        symbol="GOLD#", timeframe="H1", pattern_family="TREND_PULLBACK",
        pattern_name="UPTREND_PULLBACK", pattern_variant="SHORT_LOWER_WICK",
        direction="BUY", market_regime="TREND", trend_state="UP",
        momentum_state="RECOVERING", volatility_state="NORMAL", trading_session="LONDON",
        liquidity_state="NORMAL", multi_timeframe_context="H4_UP_H1_PULLBACK",
        entry_plan="STAGGERED_BETTER_PRICE", management_plan="SINGLE_UNIT_RESEARCH",
        exit_plan="RESEARCH_RANKED",
    )


def shape():
    return PatternShapeSignature(5, 18000, .5, .15, .45, .7, 1.2, .6)


def test_single_unit_profit_is_cumulative_each_complete_1000(tmp_path):
    dataset = AppendOnlyResearchDataset(tmp_path)
    rows = []
    for sequence in range(1, 1001):
        for policy, net in (("CORE", 10.0), ("TRAIL", 13.0)):
            rows.append(SingleUnitProfitObservation(
                pattern_id=f"P{sequence}", pattern_sequence=sequence,
                research_identity=identity(), shape_signature=shape(), exit_policy_id=policy,
                policy_parameters={"target_r": 2 if policy == "CORE" else 4},
                outcome="WIN", net_points=net, maximum_favorable_points=20,
                maximum_adverse_points=5, captured_profit_points=net,
                peak_giveback_points=20-net, holding_seconds=3600,
                break_even_exit=False, transaction_cost_points=1,
                cross_market_context_id="USD_SOFT_OIL_FLAT",
            ))
    result = SingleUnitProfitStandardizer(dataset).evaluate(rows)
    updated = [row for row in result if row["status"] == "RESEARCH_STANDARD_UPDATED"]
    assert len(updated) == 1
    assert updated[0]["standard"]["pattern_count"] == 1000
    assert updated[0]["standard"]["selected_exit_policy_id"] == "TRAIL"
    assert not [row for row in SingleUnitProfitStandardizer(dataset).evaluate(rows) if row["status"] == "RESEARCH_STANDARD_UPDATED"]


def test_initial_capital_starts_one_001_lot_and_ranks_levels(tmp_path):
    dataset = AppendOnlyResearchDataset(tmp_path)
    rows = []
    for sequence in range(1, 1001):
        for capital in (100.0, 300.0):
            rows.append(InitialCapitalObservation(
                pattern_id=f"P{sequence}", pattern_sequence=sequence,
                research_identity=identity(), shape_signature=shape(), starting_capital_usd=capital,
                required_margin_usd=20, approved_risk_usd=3,
                maximum_adverse_equity_usd=5, realized_pnl_usd=.1,
                transaction_cost_usd=.01, survived=True, margin_failure=False,
                risk_budget_failure=False, cross_market_context_id="USD_SOFT_OIL_FLAT", lot=.01,
            ))
    updated = [row for row in InitialCapitalStandardizer(dataset).evaluate(rows) if row["status"] == "RESEARCH_STANDARD_UPDATED"]
    assert len(updated) == 1
    assert updated[0]["standard"]["lot"] == .01
    assert updated[0]["standard"]["pattern_count"] == 1000
    assert updated[0]["standard"]["operational_capital_usd"] == 100.0


def test_every_profile_has_selectable_trading_mode(tmp_path):
    source = __import__("pathlib").Path("config/four_profile_demo.json")
    profiles = FourProfileOperationalRuntime(source).load()
    assert [profile.trading_mode for profile in profiles] == [
        "ALL_MODE", "ALL_MODE", "UP_TREND_AND_SIDEWAY_MODE", "UP_TREND_MODE"
    ]
    assert ProfileTradingModeAuthority.evaluate(
        mode="TREND_MODE", action="SELL", regime="DOWN_TREND", trend_state="DOWN", research_eligible=True
    ).allowed
    rejected = ProfileTradingModeAuthority.evaluate(
        mode="UP_TREND_MODE", action="SELL", regime="DOWN_TREND", trend_state="DOWN", research_eligible=True
    )
    assert not rejected.allowed
    assert rejected.reason == "current_market_rejected_by_profile_trading_mode"
    assert ProfileTradingModeAuthority.evaluate(
        mode="UP_TREND_AND_SIDEWAY_MODE", action="SELL", regime="SIDEWAY", trend_state="FLAT", research_eligible=True
    ).allowed
    no_research = ProfileTradingModeAuthority.evaluate(
        mode="ALL_MODE", action="BUY", regime="UP_TREND", trend_state="UP", research_eligible=False
    )
    assert not no_research.allowed
    assert no_research.reason == "current_pattern_not_research_eligible"


def test_dashboard_has_combined_and_four_full_detail_pages(tmp_path):
    result = DashboardAuthority().build_all(tmp_path / "runtime/dashboard", project_root=tmp_path)
    assert result.control_center.exists()
    assert {path.name for path in result.profile_details} == {
        "afip_p1_detail.html", "afip_p2_detail.html", "afip_p3_detail.html", "afip_p4_detail.html"
    }
    assert "P1 Full Decision Detail" in result.home.read_text(encoding="utf-8")
