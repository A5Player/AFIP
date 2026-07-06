from datetime import datetime, timedelta, timezone

from afip.macro.economic_calendar_runtime import EconomicCalendarRuntime
from afip.macro.macro_consensus_engine import MacroConsensusEngine
from afip.macro.macro_event_engine import MacroEventEngine
from afip.macro.market_factor_runtime import MarketFactorRuntime
from afip.runtime.production_milestone_c_macro_runtime import ProductionMilestoneCMacroRuntime


def test_economic_calendar_runtime_restricts_high_impact_event_window():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    runtime = EconomicCalendarRuntime()
    state = runtime.runtime_state(
        [
            {
                "name": "CPI",
                "currency": "USD",
                "impact": "HIGH",
                "scheduled_at": (now + timedelta(minutes=20)).isoformat(),
                "forecast": "2.8",
                "previous": "2.6",
            }
        ],
        now,
    )
    assert state["event_risk_state"] == "RESTRICTED"
    assert state["trade_instruction"] == "NO_NEW_POSITION"


def test_economic_calendar_runtime_normalizes_and_sorts_events():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    runtime = EconomicCalendarRuntime()
    state = runtime.runtime_state(
        [
            {"name": "PCE", "currency": "USD", "impact": "HIGH", "scheduled_at": (now + timedelta(hours=5)).isoformat()},
            {"name": "Jobless Claims", "currency": "USD", "impact": "HIGH", "scheduled_at": (now + timedelta(hours=1)).isoformat()},
        ],
        now,
    )
    assert state["next_event"] == "Jobless Claims"
    assert state["next_event_currency"] == "USD"


def test_macro_event_engine_scores_cpi_as_high_confidence_near_event():
    assessment = MacroEventEngine().assess_dict({"next_event": "CPI", "minutes_to_event": 10})
    assert assessment["impact_score"] >= 95
    assert assessment["urgency_score"] == 100
    assert assessment["gold_bias"] == "VOLATILITY_RISK"


def test_market_factor_runtime_detects_supportive_gold_conditions():
    state = MarketFactorRuntime().evaluate(
        {"dxy_change_percent": -0.35, "real_yield_change_bps": -4.5, "us10y_change_bps": -6, "silver_change_percent": 0.5}
    )
    assert state["gold_bias"] == "SUPPORTIVE"
    assert state["gold_macro_score"] > 80


def test_market_factor_runtime_detects_pressure_conditions():
    state = MarketFactorRuntime().evaluate(
        {"dxy_change_percent": 0.35, "real_yield_change_bps": 4.5, "us10y_change_bps": 6, "silver_change_percent": -0.5}
    )
    assert state["gold_bias"] == "PRESSURE"
    assert state["gold_macro_score"] < 30


def test_macro_consensus_keeps_no_new_position_during_restricted_calendar():
    result = MacroConsensusEngine().combine_dict(
        {"event_risk_state": "RESTRICTED", "trade_instruction": "NO_NEW_POSITION"},
        {"confidence_score": 100},
        {"gold_macro_score": 90, "gold_bias": "SUPPORTIVE"},
    )
    assert result["trade_instruction"] == "NO_NEW_POSITION"
    assert result["gold_bias"] == "VOLATILITY_RISK"


def test_production_milestone_c_macro_runtime_builds_ready_state():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = ProductionMilestoneCMacroRuntime().run_dict(
        [{"name": "FOMC", "currency": "USD", "impact": "HIGH", "scheduled_at": (now + timedelta(minutes=25)).isoformat()}],
        {"dxy_change_percent": -0.25, "real_yield_change_bps": -3.5},
        now,
    )
    assert result["status"] == "PRODUCTION_MILESTONE_C_MACRO_READY"
    assert result["ready"] is True
    assert result["trade_instruction"] == "NO_NEW_POSITION"
    assert "Macro:" in result["dashboard_line"]


def test_production_milestone_c_macro_runtime_is_deterministic():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    runtime = ProductionMilestoneCMacroRuntime()
    first = runtime.run_dict([], {"dxy_change_percent": 0.0}, now)
    second = runtime.run_dict([], {"dxy_change_percent": 0.0}, now)
    assert first == second
