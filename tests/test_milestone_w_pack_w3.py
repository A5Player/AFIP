from pathlib import Path
import json
from afip.strategy_intelligence import StrategyIntelligenceEngine, StrategyTemplate


def template(**changes):
    data = dict(strategy_id="BREAKOUT_RETEST_CONTINUATION", strategy_family="CONTINUATION", supported_pattern_families=("BREAKOUT_RETEST",), supported_market_regimes=("TREND",), minimum_similarity=80, minimum_sample_size=30)
    data.update(changes)
    return StrategyTemplate(**data)


def match(identifier, similarity=95, samples=100, win_rate=82, expectancy=2.5, quality="HIGH", pattern="BREAKOUT_RETEST", regime="TREND"):
    return {"historical_context_id": identifier, "similarity_score": similarity, "sample_size": samples, "evidence_quality": quality, "outcome": "WIN", "metadata": {"historical_win_rate": win_rate, "historical_expectancy": expectancy, "pattern_family": pattern, "market_regime": regime}}


def test_strong_evidence_is_eligible_for_plan_review_only():
    result = StrategyIntelligenceEngine().evaluate(template(), [match("A"), match("B", 93), match("C", 91)])
    assert result.status == "ELIGIBLE_FOR_PLAN_REVIEW"
    assert result.authority == "ADVISORY_ONLY"
    assert result.execution_authority is False and result.order_send_allowed is False


def test_insufficient_evidence_fails_closed():
    result = StrategyIntelligenceEngine().evaluate(template(), [match("A")])
    assert result.status == "WAIT"
    assert "insufficient_evidence_count" in result.reasons


def test_unsupported_context_is_excluded():
    evidence = [match("A", pattern="REVERSAL"), match("B", regime="RANGE"), match("C", similarity=70)]
    result = StrategyIntelligenceEngine().evaluate(template(), evidence)
    assert result.status == "WAIT" and result.evidence_count == 0


def test_rank_prefers_stronger_supported_strategy():
    engine = StrategyIntelligenceEngine()
    strong = template()
    weak = template(strategy_id="REVERSAL", strategy_family="REVERSAL", supported_pattern_families=("REVERSAL",), supported_market_regimes=("RANGE",))
    ranked = engine.rank([weak, strong], [match("A"), match("B"), match("C")])
    assert ranked[0].strategy_id == strong.strategy_id
    assert ranked[1].status == "WAIT"


def test_contract_forbids_trading_authority():
    path = Path(__file__).resolve().parents[1] / "config/strategy_intelligence_contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    assert contract["final_decision_authority"] is False
    assert contract["execution_authority"] is False
    assert contract["order_send_allowed"] is False
    assert contract["lot_authority"] is False
    assert contract["sl_tp_authority"] is False
