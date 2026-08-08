from afip.market_regime_v2 import MarketStructureContextAnalyzer
from afip.strategy_intelligence import ResearchPlanGate


def _uptrend_bars():
    return [
        {"open": 2000 + index, "high": 2001 + index, "low": 1999 + index, "close": 2000.8 + index}
        for index in range(24)
    ]


def test_closed_bar_context_identifies_uptrend_pullback_or_extension():
    context = MarketStructureContextAnalyzer().analyze(_uptrend_bars(), timeframe="H1")
    assert context.research_ready is True
    assert context.regime == "UP_TREND"
    assert context.trend_state == "UP"
    assert context.structure_state == "HIGHER_HIGHS_HIGHER_LOWS"
    assert context.pattern_name.startswith("UPTREND_")
    assert context.execution_authority == "NONE"


def test_short_history_is_explicit_and_not_tradeable():
    context = MarketStructureContextAnalyzer().analyze(_uptrend_bars()[:5], timeframe="H1")
    assert context.research_ready is False
    assert context.regime == "INSUFFICIENT_DATA"
    assert context.direction == "WAIT"


def test_research_plan_gate_requires_exact_named_context_match():
    context = MarketStructureContextAnalyzer().analyze(_uptrend_bars(), timeframe="H1").as_dict()
    evidence = {
        "eligible": True,
        "pattern_name": context["pattern_name"],
        "pattern_family": context["pattern_family"],
        "market_regime": context["regime"],
        "structure_state": context["structure_state"],
        "zone_position": context["zone_position"],
        "rank": 1,
        "sample_size": 1000,
    }
    approved = ResearchPlanGate().evaluate(action="BUY", context=context, evidence=evidence)
    assert approved.allowed is True
    wrong_shape = ResearchPlanGate().evaluate(action="BUY", context=context, evidence={**evidence, "pattern_name": "OTHER"})
    assert wrong_shape.allowed is False
    assert wrong_shape.reason == "research_evidence_pattern_name_mismatch"


def test_transition_or_sideway_without_a_matching_plan_is_wait():
    context = {
        "regime": "TRANSITION", "trend_state": "MIXED", "structure_state": "STRUCTURE_UNCONFIRMED",
        "zone_position": "MID_ZONE", "pattern_family": "TRANSITION", "pattern_name": "TRANSITION_WAIT",
        "direction": "WAIT", "research_ready": True,
    }
    result = ResearchPlanGate().evaluate(action="BUY", context=context, evidence={"eligible": True})
    assert result.allowed is False
    assert result.reason == "market_regime_not_tradeable_for_research_plan"
