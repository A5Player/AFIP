from afip.intelligence.fair_value_gap_intelligence import FairValueGapIntelligence
from afip.intelligence.imbalance_intelligence import ImbalanceIntelligence
from afip.intelligence.liquidity_sweep_intelligence import LiquiditySweepIntelligence
from afip.intelligence.order_block_intelligence import OrderBlockIntelligence
from afip.intelligence.smart_money_concept_intelligence import SmartMoneyConceptIntelligence


def bullish_snapshot():
    return {
        "opens": [100.0, 100.2, 100.1, 100.0, 100.4, 101.0, 101.5, 102.0, 102.8, 103.4],
        "highs": [100.5, 100.6, 100.4, 100.8, 101.4, 101.9, 102.4, 103.1, 103.8, 104.5],
        "lows": [99.7, 99.9, 99.8, 99.6, 100.9, 101.2, 101.7, 102.2, 102.9, 103.5],
        "closes": [100.1, 100.0, 99.95, 100.6, 101.2, 101.7, 102.2, 102.9, 103.6, 104.2],
        "spread": 25.0,
    }


def bearish_snapshot():
    return {
        "opens": [104.0, 104.2, 104.1, 104.3, 103.8, 103.0, 102.4, 101.9, 101.2, 100.6],
        "highs": [104.6, 104.7, 104.5, 104.9, 104.0, 103.3, 102.6, 102.1, 101.4, 100.8],
        "lows": [103.8, 103.7, 103.9, 103.9, 102.7, 102.2, 101.6, 101.0, 100.4, 99.9],
        "closes": [104.2, 104.1, 104.25, 103.9, 102.9, 102.4, 101.8, 101.2, 100.6, 100.1],
        "spread": 25.0,
    }


def sweep_snapshot():
    return {
        "opens": [100.0, 100.2, 100.1, 100.3, 100.2, 100.4, 100.1, 100.2, 100.0, 99.9],
        "highs": [101.0, 101.1, 101.0, 101.2, 101.1, 101.2, 101.0, 101.1, 101.0, 100.8],
        "lows": [99.0, 99.1, 99.0, 99.1, 99.0, 99.1, 99.0, 99.1, 99.0, 98.5],
        "closes": [100.2, 100.1, 100.3, 100.2, 100.4, 100.2, 100.3, 100.1, 99.9, 99.4],
    }


def test_fair_value_gap_detects_bullish_gap():
    result = FairValueGapIntelligence(minimum_gap_points=10, point_size=0.01).analyze(bullish_snapshot())
    assert result["status"] == "READY"
    assert result["direction"] == "BUY"
    assert result["latest_gap"]["direction"] == "BULLISH"
    assert result["confidence"] > 50.0


def test_imbalance_detects_bearish_flow():
    result = ImbalanceIntelligence(lookback=10).analyze(bearish_snapshot())
    assert result["status"] == "READY"
    assert result["direction"] == "SELL"
    assert result["imbalance_score"] > 10.0
    assert result["efficiency_score"] > 20.0


def test_order_block_detects_active_bullish_zone():
    result = OrderBlockIntelligence(lookback=10).analyze(bullish_snapshot())
    assert result["status"] == "READY"
    assert result["direction"] == "BUY"
    assert result["latest_order_block"]["direction"] == "BULLISH"
    assert result["active_order_block_count"] >= 1


def test_liquidity_sweep_detects_sell_side_sweep():
    result = LiquiditySweepIntelligence(lookback=10, equality_tolerance_points=20, point_size=0.01).analyze(sweep_snapshot())
    assert result["status"] == "READY"
    assert result["direction"] == "BUY"
    assert result["sweep_type"] == "SELL_SIDE_SWEEP"
    assert result["confidence"] >= 55.0


def test_smart_money_integration_returns_directional_bias():
    result = SmartMoneyConceptIntelligence().analyze(bullish_snapshot())
    assert result["status"] == "READY"
    assert result["direction"] in {"BUY", "SELL", "FLAT"}
    assert result["institutional_bias"] in {
        "BULLISH_SMART_MONEY_BIAS",
        "BEARISH_SMART_MONEY_BIAS",
        "BALANCED",
    }
    assert len(result["components"]) == 4


def test_batch15_uses_financial_terminology_only():
    source_names = [
        FairValueGapIntelligence.name,
        ImbalanceIntelligence.name,
        OrderBlockIntelligence.name,
        LiquiditySweepIntelligence.name,
        SmartMoneyConceptIntelligence.name,
    ]
    banned_terms = ("military", "commander", "sniper", "scout", "ranger")
    assert not any(term in name.lower() for name in source_names for term in banned_terms)
