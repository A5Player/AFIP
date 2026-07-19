from afip.research_evidence_consumer import EvidenceConsumer, EvidenceQuery

QUERY = EvidenceQuery("p1", "TREND", "LONDON", "NORMAL", "NORMAL")

def test_consumer_returns_no_order_permission():
    record = {"research_id": "r1", "pattern_id": "p1", "market_regime": "TREND",
              "session": "LONDON", "volatility_band": "NORMAL", "trading_cost_band": "NORMAL",
              "evidence_status": "CERTIFIED", "ranking_score": 90, "trade_count": 100}
    result = EvidenceConsumer([record]).query(QUERY)
    assert result["status"] == "CERTIFIED_EVIDENCE_AVAILABLE"
    assert result["execution_permission"] is False

def test_quarantined_record_is_excluded():
    record = {"research_id": "r1", "pattern_id": "p1", "market_regime": "TREND",
              "session": "LONDON", "volatility_band": "NORMAL", "trading_cost_band": "NORMAL",
              "evidence_status": "QUARANTINED", "ranking_score": 99}
    assert EvidenceConsumer([record]).query(QUERY)["status"] == "NO_CERTIFIED_EVIDENCE"

def test_best_certified_match_is_deterministic():
    base = {"pattern_id": "p1", "market_regime": "TREND", "session": "LONDON",
            "volatility_band": "NORMAL", "trading_cost_band": "NORMAL", "evidence_status": "CERTIFIED"}
    records = [{**base, "research_id": "b", "ranking_score": 80}, {**base, "research_id": "a", "ranking_score": 90}]
    assert EvidenceConsumer(records).query(QUERY)["evidence"]["research_id"] == "a"
