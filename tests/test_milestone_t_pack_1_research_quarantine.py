from datetime import datetime, timezone

from afip.research_governance import (
    KnowledgeState,
    PromotionPolicy,
    ResearchPromotionGate,
    ResearchZoneLayout,
)


def _eligible_record():
    return {
        "state": "APPROVED_CANDIDATE",
        "dataset_version": "GOLD-H1-2026.07",
        "research_run_id": "RUN-T1-001",
        "validation_report_id": "VAL-T1-001",
        "market_context_signature": "GOLD|H1|TREND|LONDON|NORMAL_VOLATILITY",
        "sample_size": 1000,
        "out_of_sample_size": 250,
        "walk_forward_windows": 5,
        "win_rate": 0.61,
        "net_profit": 1840.0,
        "profit_factor": 1.42,
        "expectancy": 0.18,
        "maximum_drawdown": 0.11,
        "out_of_sample_passed": True,
        "walk_forward_passed": True,
        "data_quality_certified": True,
        "future_leakage_detected": False,
        "chronological_replay_verified": True,
        "manual_approval_granted": True,
        "approved_by": "AFIP_RESEARCH_AUTHORITY",
    }


def test_research_and_production_directories_are_physically_separate(tmp_path):
    layout = ResearchZoneLayout(tmp_path)
    layout.ensure()
    assert layout.experimental.is_dir()
    assert layout.pending.is_dir()
    assert layout.approved.is_dir()
    assert layout.experimental != layout.approved
    assert "research" in layout.experimental.parts
    assert "knowledge" in layout.approved.parts


def test_experimental_record_is_never_readable_by_production():
    record = _eligible_record()
    record["state"] = KnowledgeState.EXPERIMENTAL.value
    record["production_usable"] = True
    record["promotion_checksum_verified"] = True
    assert ResearchPromotionGate.production_read_allowed(record) is False


def test_candidate_becomes_eligible_only_after_every_gate_passes():
    decision = ResearchPromotionGate().evaluate(
        _eligible_record(), now=datetime(2026, 7, 19, tzinfo=timezone.utc)
    )
    assert decision.status == "APPROVED"
    assert decision.target_state == "PRODUCTION_APPROVED"
    assert decision.production_usable is True
    assert decision.block_reasons == ()
    assert decision.objective_evidence["maximum_drawdown"] == 0.11
    assert decision.objective_evidence["net_profit"] == 1840.0
    assert decision.objective_evidence["win_rate"] == 0.61


def test_missing_walk_forward_fails_closed():
    record = _eligible_record()
    record["walk_forward_passed"] = False
    decision = ResearchPromotionGate().evaluate(record)
    assert decision.status == "BLOCK"
    assert "walk_forward_not_passed" in decision.block_reasons


def test_insufficient_out_of_sample_size_fails_closed():
    record = _eligible_record()
    record["out_of_sample_size"] = 99
    decision = ResearchPromotionGate().evaluate(record)
    assert "minimum_out_of_sample_size_not_met" in decision.block_reasons


def test_future_leakage_always_blocks_promotion():
    record = _eligible_record()
    record["future_leakage_detected"] = True
    decision = ResearchPromotionGate().evaluate(record)
    assert "future_leakage_detected" in decision.block_reasons


def test_high_profit_does_not_override_drawdown_limit():
    record = _eligible_record()
    record["net_profit"] = 1_000_000.0
    record["profit_factor"] = 9.0
    record["expectancy"] = 10.0
    record["maximum_drawdown"] = 0.50
    decision = ResearchPromotionGate().evaluate(record)
    assert decision.status == "BLOCK"
    assert "maximum_drawdown_exceeded" in decision.block_reasons


def test_high_win_rate_does_not_override_missing_validation():
    record = _eligible_record()
    record["win_rate"] = 0.99
    record["out_of_sample_passed"] = False
    decision = ResearchPromotionGate().evaluate(record)
    assert decision.status == "BLOCK"
    assert "out_of_sample_not_passed" in decision.block_reasons


def test_manual_approval_and_approver_identity_are_mandatory():
    record = _eligible_record()
    record["manual_approval_granted"] = False
    record["approved_by"] = ""
    decision = ResearchPromotionGate().evaluate(record)
    assert "manual_approval_required" in decision.block_reasons


def test_production_reader_requires_approved_state_checksum_and_not_revoked():
    record = {
        "state": "PRODUCTION_APPROVED",
        "production_usable": True,
        "promotion_checksum_verified": True,
        "revoked": False,
    }
    assert ResearchPromotionGate.production_read_allowed(record) is True
    record["revoked"] = True
    assert ResearchPromotionGate.production_read_allowed(record) is False


def test_dashboard_uses_objectives_not_top10_or_top100():
    snapshot = ResearchPromotionGate.dashboard_snapshot([{"state": "EXPERIMENTAL"}])
    assert snapshot["top_ranking_enabled"] is False
    assert snapshot["selection_method"] == "CONTEXT_OBJECTIVES"
    assert snapshot["selection_objectives"] == [
        "LOWER_DRAWDOWN",
        "HIGHER_NET_PROFIT",
        "HIGHER_WIN_PROBABILITY",
    ]
    assert snapshot["experimental_data_used_by_production"] is False


def test_unknown_state_is_treated_as_experimental_and_blocked():
    record = _eligible_record()
    record["state"] = "UNKNOWN_UNSAFE_STATE"
    decision = ResearchPromotionGate().evaluate(record)
    assert decision.source_state == "EXPERIMENTAL"


def test_policy_is_loaded_from_json(tmp_path):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        '{"minimum_sample_size": 500, "maximum_drawdown": 0.1}',
        encoding="utf-8",
    )
    policy = PromotionPolicy.from_json_file(policy_path)
    assert policy.minimum_sample_size == 500
    assert policy.maximum_drawdown == 0.1
    assert policy.minimum_profit_factor == 1.20
