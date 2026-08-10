import pytest
from afip.exit_outcome_research.a16_contract import A16ResearchContext, candidate_policy_ids, validate_advisory_record

def test_a16_has_all_required_research_candidates():
    assert candidate_policy_ids() == ("FIXED_TP", "BREAK_EVEN_FIXED_TP", "R_STEP", "MFE_PERCENT", "ATR", "STRUCTURE", "HYBRID_R_STRUCTURE", "PARTIAL_RUNNER")

def test_a16_context_preserves_blind_forward_contract():
    context = A16ResearchContext("p", "family", "plan", "2026-01-01T00:00:00Z", "TREND", "LONDON", "OPEN", "NONE", "NORMAL_DAY", "VERIFIED")
    assert context.as_dict()["future_data_used"] is False

def test_a16_rejects_execution_authority():
    with pytest.raises(ValueError, match="cannot request execution"):
        validate_advisory_record({"direct_execution": True})
