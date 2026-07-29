from afip.research_ranking.runtime import ResearchRankingEngine


def _row(**overrides):
    row = {
        "research_id": "R-1",
        "trade_count": 40,
        "out_of_sample_windows": 2,
        "maximum_drawdown_percentage": 8.0,
        "expectancy": 2.0,
        "profit_factor": 1.8,
        "recovery_factor": 3.0,
        "stability_score": 80.0,
        "research_feedback_status": "ELIGIBLE",
        "ranking_readiness_status": "READY_FOR_RESEARCH_RANKING",
        "dataset_integrity_status": "READY",
    }
    row.update(overrides)
    return row


def test_certified_candidate_is_research_only_not_production_promoted():
    result = ResearchRankingEngine().rank([_row()])
    item = result["top_overall"][0]
    assert item["promotion_status"] == "RESEARCH_CANDIDATE"
    assert item["automatic_production_promotion_allowed"] is False
    assert item["affects_trading"] is False
    assert result["ranking_authority"]["execution_permission"] is False


def test_quarantined_feedback_never_enters_certified_ranking():
    result = ResearchRankingEngine().rank([_row(research_feedback_status="QUARANTINED")])
    assert result["top_overall"] == []
    assert result["bottom_and_quarantined"][0]["evidence_status"] == "QUARANTINED"
    assert result["bottom_and_quarantined"][0]["promotion_status"] == "QUARANTINED"


def test_dataset_not_ready_blocks_plan_promotion():
    result = ResearchRankingEngine().rank([_row(ranking_readiness_status="NOT_READY_FOR_AUTOMATIC_RANKING")])
    item = result["bottom_and_quarantined"][0]
    assert item["evidence_status"] == "INSUFFICIENT_EVIDENCE"
    assert item["promotion_status"] == "NOT_ELIGIBLE"
    assert result["ranking_authority"]["automatic_production_promotion_allowed"] is False
