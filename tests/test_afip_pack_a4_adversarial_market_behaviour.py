from __future__ import annotations

from afip.market_regime_v2 import AdversarialMarketBehaviourAnalyzer
from afip.strategy_intelligence import ResearchPlanGate


def _bars(*, compressed: bool = False) -> list[dict[str, float]]:
    rows = []
    for index in range(20):
        centre = 2000.0 + (index % 3 - 1) * (0.08 if compressed else 2.0)
        width = 0.12 if compressed and index >= 12 else 2.0
        rows.append({"open": centre, "high": centre + width, "low": centre - width, "close": centre + width * 0.1})
    return rows


def _context(threat: dict[str, object]) -> dict[str, object]:
    return {
        "regime": "UP_TREND", "trend_state": "UP", "structure_state": "HIGHER_HIGHS_HIGHER_LOWS",
        "zone_position": "MID_ZONE", "pattern_family": "TREND_PULLBACK", "pattern_name": "UPTREND_PULLBACK",
        "direction": "BUY", "research_ready": True, "adversarial_market_behaviour": threat,
    }


def _evidence() -> dict[str, object]:
    return {
        "eligible": True, "pattern_name": "UPTREND_PULLBACK", "pattern_family": "TREND_PULLBACK",
        "market_regime": "UP_TREND", "structure_state": "HIGHER_HIGHS_HIGHER_LOWS",
        "zone_position": "MID_ZONE", "rank": 1, "sample_size": 100,
    }


def test_compression_is_explicit_no_trade_and_blocks_plan_gate() -> None:
    threat = AdversarialMarketBehaviourAnalyzer().analyze(_bars(compressed=True), timeframe="M15").as_dict()
    assert threat["threat_state"] == "SIDEWAY_COMPRESSION_NO_TRADE"
    result = ResearchPlanGate().evaluate(action="BUY", context=_context(threat), evidence=_evidence())
    assert result.allowed is False
    assert result.reason == "adversarial_market_behaviour_sideway_compression_no_trade"


def test_sweep_proxy_waits_for_reclaim_and_retest() -> None:
    bars = _bars()
    prior_low = min(row["low"] for row in bars[:-1])
    bars[-1] = {"open": prior_low + 0.3, "high": prior_low + 0.7, "low": prior_low - 1.0, "close": prior_low + 0.2}
    threat = AdversarialMarketBehaviourAnalyzer().analyze(bars, timeframe="M15").as_dict()
    assert threat["threat_state"] == "POST_SWEEP_WAITING_CONFIRMATION"
    assert threat["sweep_side"] == "LOWER"


def test_clear_context_does_not_replace_existing_exact_research_gate() -> None:
    threat = AdversarialMarketBehaviourAnalyzer().analyze(_bars(), timeframe="M15").as_dict()
    assert threat["threat_state"] == "CLEAR"
    result = ResearchPlanGate().evaluate(action="BUY", context=_context(threat), evidence=_evidence())
    assert result.allowed is True
