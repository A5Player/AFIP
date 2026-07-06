from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.macro.macro_market_dashboard import MacroMarketDashboardBuilder
from afip.runtime.production_milestone_c_dashboard_runtime import ProductionMilestoneCMacroDashboardRuntime


NOW = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def _supportive_state() -> dict[str, object]:
    return {
        "consensus": {
            "macro_score": 78.25,
            "decision_confidence": 84.5,
            "gold_market_bias": "GOLD_SUPPORTIVE",
            "event_risk_state": "CLEAR",
            "conflict_level": "LOW",
            "component_scores": {"calendar": 66.0, "news": 82.0, "market_factors": 86.0},
        },
        "decision_profile": {
            "exposure_instruction": "ALLOW_LONG_EXPOSURE",
            "position_horizon": "INTRADAY_TREND",
            "reason": "macro_inputs_support_gold",
        },
        "calendar_state": {"status": "READY", "next_event": "No scheduled event", "event_risk_state": "CLEAR"},
        "news_state": {"status": "READY", "gold_bias": "GOLD_SUPPORTIVE", "reason": "fed_policy_supportive"},
        "market_factor_state": {
            "status": "READY",
            "gold_market_bias": {"bias": "SUPPORTIVE", "score": 86.0},
            "reason": "dxy_and_real_yield_support_gold",
        },
    }


def test_macro_dashboard_builder_creates_summary_line() -> None:
    dashboard = MacroMarketDashboardBuilder().build_dict(_supportive_state())

    assert dashboard["status"] == "MACRO_MARKET_DASHBOARD_READY"
    assert "Macro Score 78.25" in dashboard["summary_line"]
    assert dashboard["exposure_instruction"] == "ALLOW_LONG_EXPOSURE"
    assert dashboard["gold_market_bias"] == "GOLD_SUPPORTIVE"


def test_macro_dashboard_builder_creates_three_component_rows() -> None:
    dashboard = MacroMarketDashboardBuilder().build_dict(_supportive_state())

    rows = dashboard["component_rows"]
    assert len(rows) == 3
    assert rows[0]["name"] == "Economic Calendar"
    assert rows[1]["name"] == "Macro News"
    assert rows[2]["name"] == "Market Factors"


def test_macro_dashboard_builder_preserves_component_scores() -> None:
    dashboard = MacroMarketDashboardBuilder().build_dict(_supportive_state())

    scores = [row["score"] for row in dashboard["component_rows"]]
    assert scores == [66.0, 82.0, 86.0]


def test_macro_dashboard_builder_reports_standard_review_when_clear() -> None:
    dashboard = MacroMarketDashboardBuilder().build_dict(_supportive_state())

    assert dashboard["key_risks"] == ["standard_macro_review"]


def test_macro_dashboard_builder_flags_restricted_calendar_window() -> None:
    state = _supportive_state()
    state["consensus"] = dict(state["consensus"], event_risk_state="RESTRICTED", conflict_level="CALENDAR_RESTRICTED")
    state["decision_profile"] = dict(state["decision_profile"], exposure_instruction="NO_NEW_EXPOSURE")

    dashboard = MacroMarketDashboardBuilder().build_dict(state)

    assert dashboard["headline"] == "Macro dashboard recommends no new exposure"
    assert "high_impact_calendar_window" in dashboard["key_risks"]
    assert "macro_input_conflict" in dashboard["key_risks"]


def test_macro_dashboard_builder_flags_mixed_news() -> None:
    state = _supportive_state()
    state["news_state"] = dict(state["news_state"], gold_bias="MIXED")
    state["consensus"] = dict(state["consensus"], conflict_level="HIGH")

    dashboard = MacroMarketDashboardBuilder().build_dict(state)

    assert "mixed_macro_news" in dashboard["key_risks"]


def test_macro_dashboard_report_lines_are_dashboard_friendly() -> None:
    dashboard = MacroMarketDashboardBuilder().build_dict(_supportive_state())

    assert len(dashboard["report_lines"]) >= 6
    assert dashboard["report_lines"][0] == dashboard["headline"]
    assert dashboard["report_lines"][1] == dashboard["summary_line"]


def test_macro_dashboard_runtime_builds_ready_state() -> None:
    runtime = ProductionMilestoneCMacroDashboardRuntime()
    state = runtime.run_dict(
        economic_events=[],
        news_articles=[{"title": "Fed rate outlook supports gold", "published_at": NOW.isoformat(), "source": "sample"}],
        market_factors={"dxy_change_pct": -0.4, "us10y_change_bps": -5.0, "real_yield_change_bps": -6.0},
        now=NOW,
    )

    assert state["status"] == "MACRO_DASHBOARD_RUNTIME_READY"
    assert state["ready"] is True
    assert state["dashboard"]["status"] == "MACRO_MARKET_DASHBOARD_READY"


def test_macro_dashboard_runtime_blocks_near_high_impact_event() -> None:
    runtime = ProductionMilestoneCMacroDashboardRuntime()
    state = runtime.run_dict(
        economic_events=[{"name": "CPI", "importance": "HIGH", "scheduled_at": (NOW + timedelta(minutes=20)).isoformat()}],
        news_articles=[],
        market_factors={"dxy_change_pct": -0.4, "us10y_change_bps": -5.0, "real_yield_change_bps": -6.0},
        now=NOW,
    )

    assert state["exposure_instruction"] == "NO_NEW_EXPOSURE"
    assert "high_impact_calendar_window" in state["dashboard"]["key_risks"]


def test_macro_dashboard_runtime_includes_consensus_state() -> None:
    runtime = ProductionMilestoneCMacroDashboardRuntime()
    state = runtime.run_dict(now=NOW)

    assert state["consensus_state"]["status"] == "MACRO_MARKET_CONSENSUS_RUNTIME_READY"
    assert "consensus" in state["consensus_state"]
    assert "decision_profile" in state["consensus_state"]


def test_macro_dashboard_runtime_is_deterministic() -> None:
    runtime = ProductionMilestoneCMacroDashboardRuntime()
    first = runtime.run_dict(
        news_articles=[{"title": "Treasury yields ease and gold demand improves", "published_at": NOW.isoformat()}],
        market_factors={"dxy_change_pct": -0.2, "us10y_change_bps": -3.0, "real_yield_change_bps": -4.0},
        now=NOW,
    )
    second = runtime.run_dict(
        news_articles=[{"title": "Treasury yields ease and gold demand improves", "published_at": NOW.isoformat()}],
        market_factors={"dxy_change_pct": -0.2, "us10y_change_bps": -3.0, "real_yield_change_bps": -4.0},
        now=NOW,
    )

    assert first == second
