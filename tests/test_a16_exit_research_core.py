from afip.exit_outcome_research import A16PolicySet


def test_a16_catalogue_has_eight_research_candidates():
    assert [p.policy_id for p in A16PolicySet(2).policies()] == [
        "FIXED_TP", "BREAK_EVEN_FIXED_TP", "R_STEP", "MFE_PERCENT",
        "ATR", "STRUCTURE", "HYBRID_R_STRUCTURE", "PARTIAL_RUNNER",
    ]


def test_a16_catalogue_rejects_invalid_risk():
    try:
        A16PolicySet(0)
    except ValueError as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("invalid risk must fail closed")
