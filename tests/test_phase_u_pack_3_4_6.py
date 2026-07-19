from afip.production_research_certification import CertificationPolicy, ProductionResearchCertification

def test_certification_passes_complete_safe_evidence():
    result = ProductionResearchCertification().certify(
        {"status": "READY"},
        {"eligible_window_count": 2},
        {"top_overall": [{"research_id": "r1", "maximum_drawdown_percentage": 5}]},
    )
    assert result["status"] == "CERTIFIED"
    assert result["execution_permission"] is False

def test_dataset_caution_blocks_certification():
    result = ProductionResearchCertification().certify(
        {"status": "CAUTION"}, {"eligible_window_count": 2},
        {"top_overall": [{"research_id": "r1", "maximum_drawdown_percentage": 5}]},
    )
    assert "dataset_not_ready" in result["findings"]

def test_drawdown_limit_is_non_compensating():
    result = ProductionResearchCertification(CertificationPolicy(maximum_drawdown_percentage=20)).certify(
        {"status": "READY"}, {"eligible_window_count": 2},
        {"top_overall": [{"research_id": "high_win", "win_rate_percentage": 99, "maximum_drawdown_percentage": 45}]},
    )
    assert result["status"] == "NOT_CERTIFIED"
    assert "certified_candidate_exceeds_drawdown_limit" in result["findings"]
