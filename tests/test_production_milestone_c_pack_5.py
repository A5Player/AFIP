from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.macro.macro_market_consensus import MacroMarketConsensusEngine
from afip.macro.macro_market_decision_profile import MacroMarketDecisionProfileEngine
from afip.runtime.production_milestone_c_consensus_runtime import ProductionMilestoneCConsensusRuntime

NOW = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def _event(minutes: int = 180, name: str = "CPI", impact: str = "HIGH") -> dict[str, object]:
    return {
        "name": name,
        "currency": "USD",
        "impact": impact,
        "scheduled_at": (NOW + timedelta(minutes=minutes)).isoformat(),
        "forecast": 2.8,
        "previous": 2.6,
    }


def _supportive_news() -> list[dict[str, object]]:
    return [
        {
            "title": "Fed signals softer rate path as gold demand improves",
            "source": "Static Financial News",
            "published_at": NOW.isoformat(),
            "summary": "Fed dovish tone and weaker dollar support gold.",
        }
    ]


def _pressure_news() -> list[dict[str, object]]:
    return [
        {
            "title": "Treasury yields rise as dollar strengthens and gold slips",
            "source": "Static Financial News",
            "published_at": NOW.isoformat(),
            "summary": "Higher yields pressure gold and reduce demand.",
        }
    ]


def _supportive_factors() -> dict[str, float]:
    return {
        "dxy_change_percent": -0.42,
        "us10y_change_bps": -8.0,
        "real_yield_change_bps": -11.0,
        "inflation_expectation_change_bps": 1.0,
    }


def _pressure_factors() -> dict[str, float]:
    return {
        "dxy_change_percent": 0.55,
        "us10y_change_bps": 9.0,
        "real_yield_change_bps": 13.0,
        "inflation_expectation_change_bps": -1.0,
    }


def test_macro_market_consensus_supportive_alignment():
    engine = MacroMarketConsensusEngine()
    result = engine.combine_dict(
        {"event_risk_state": "CLEAR"},
        {"confidence_score": 25.0},
        {"gold_bias": "SUPPORTIVE", "confidence_score": 82.0, "impact_score": 72.0},
        {"gold_market_bias": {"bias": "GOLD_SUPPORTIVE", "score": 74.0}},
    )
    assert result["status"] == "MACRO_MARKET_CONSENSUS_READY"
    assert result["gold_market_bias"] == "GOLD_SUPPORTIVE"
    assert result["macro_score"] >= 62.0
    assert result["conflict_level"] in {"LOW", "MEDIUM"}


def test_macro_market_consensus_pressure_alignment():
    engine = MacroMarketConsensusEngine()
    result = engine.combine_dict(
        {"event_risk_state": "CLEAR"},
        {"confidence_score": 30.0},
        {"gold_bias": "PRESSURE", "confidence_score": 82.0, "impact_score": 75.0},
        {"gold_market_bias": {"bias": "GOLD_PRESSURE", "score": 24.0}},
    )
    assert result["gold_market_bias"] == "GOLD_PRESSURE"
    assert result["macro_score"] <= 38.0
    assert result["reason"] == "macro_inputs_pressure_gold"


def test_macro_market_consensus_routes_conflict_to_mixed():
    engine = MacroMarketConsensusEngine()
    result = engine.combine_dict(
        {"event_risk_state": "CLEAR"},
        {"confidence_score": 25.0},
        {"gold_bias": "SUPPORTIVE", "confidence_score": 80.0, "impact_score": 80.0},
        {"gold_market_bias": {"bias": "GOLD_PRESSURE", "score": 25.0}},
    )
    assert result["gold_market_bias"] == "MIXED"
    assert result["conflict_level"] == "HIGH"
    assert result["decision_confidence"] < 80.0


def test_macro_market_consensus_respects_restricted_calendar_window():
    engine = MacroMarketConsensusEngine()
    result = engine.combine_dict(
        {"event_risk_state": "RESTRICTED"},
        {"confidence_score": 100.0},
        {"gold_bias": "SUPPORTIVE", "confidence_score": 90.0, "impact_score": 95.0},
        {"gold_market_bias": {"bias": "GOLD_SUPPORTIVE", "score": 86.0}},
    )
    assert result["gold_market_bias"] == "VOLATILITY_RISK"
    assert result["conflict_level"] == "CALENDAR_RESTRICTED"
    assert result["decision_confidence"] <= 65.0


def test_macro_market_decision_profile_favors_long_exposure_when_aligned():
    profile = MacroMarketDecisionProfileEngine().build(
        {
            "gold_market_bias": "GOLD_SUPPORTIVE",
            "macro_score": 72.0,
            "decision_confidence": 84.0,
            "event_risk_state": "CLEAR",
            "conflict_level": "LOW",
            "news_impact_score": 70.0,
        }
    )
    assert profile.exposure_instruction == "FAVOR_LONG_EXPOSURE"
    assert profile.position_horizon == "DAY_TRADE_PREFERRED"
    assert profile.review_required is False


def test_macro_market_decision_profile_blocks_new_exposure_in_restricted_window():
    profile = MacroMarketDecisionProfileEngine().build(
        {
            "gold_market_bias": "VOLATILITY_RISK",
            "macro_score": 80.0,
            "decision_confidence": 60.0,
            "event_risk_state": "RESTRICTED",
            "conflict_level": "CALENDAR_RESTRICTED",
            "news_impact_score": 95.0,
        }
    )
    assert profile.exposure_instruction == "NO_NEW_EXPOSURE"
    assert profile.review_required is True


def test_macro_market_decision_profile_routes_conflict_to_review_only():
    profile = MacroMarketDecisionProfileEngine().build(
        {
            "gold_market_bias": "MIXED",
            "macro_score": 50.0,
            "decision_confidence": 55.0,
            "event_risk_state": "CLEAR",
            "conflict_level": "HIGH",
            "news_impact_score": 88.0,
        }
    )
    assert profile.exposure_instruction == "REVIEW_ONLY"
    assert profile.confidence_floor == 85.0


def test_production_milestone_c_consensus_runtime_builds_ready_state():
    runtime = ProductionMilestoneCConsensusRuntime()
    result = runtime.run_dict(
        economic_events=[_event(180)],
        news_articles=_supportive_news(),
        market_factors=_supportive_factors(),
        now=NOW,
    )
    assert result["status"] == "MACRO_MARKET_CONSENSUS_RUNTIME_READY"
    assert result["ready"] is True
    assert result["consensus"]["status"] == "MACRO_MARKET_CONSENSUS_READY"
    assert result["decision_profile"]["status"] == "MACRO_MARKET_DECISION_PROFILE_READY"
    assert result["exposure_instruction"] in {"FAVOR_LONG_EXPOSURE", "BALANCED_REVIEW"}


def test_production_milestone_c_consensus_runtime_blocks_near_high_impact_event():
    runtime = ProductionMilestoneCConsensusRuntime()
    result = runtime.run_dict(
        economic_events=[_event(20, "FOMC", "HIGH")],
        news_articles=_supportive_news(),
        market_factors=_supportive_factors(),
        now=NOW,
    )
    assert result["calendar_state"]["event_risk_state"] == "RESTRICTED"
    assert result["decision_profile"]["exposure_instruction"] == "NO_NEW_EXPOSURE"


def test_production_milestone_c_consensus_runtime_handles_conflicting_inputs():
    runtime = ProductionMilestoneCConsensusRuntime()
    result = runtime.run_dict(
        economic_events=[_event(240)],
        news_articles=_supportive_news(),
        market_factors=_pressure_factors(),
        now=NOW,
    )
    assert result["consensus"]["conflict_level"] == "HIGH"
    assert result["decision_profile"]["exposure_instruction"] == "REVIEW_ONLY"


def test_production_milestone_c_consensus_runtime_is_deterministic():
    runtime = ProductionMilestoneCConsensusRuntime()
    first = runtime.run_dict([_event(180)], _pressure_news(), _pressure_factors(), NOW)
    second = runtime.run_dict([_event(180)], _pressure_news(), _pressure_factors(), NOW)
    assert first["consensus"] == second["consensus"]
    assert first["decision_profile"] == second["decision_profile"]
