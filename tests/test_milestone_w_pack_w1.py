from pathlib import Path
import json
import pytest
from afip.research_knowledge.repository import KnowledgeRecord, ResearchKnowledgeRepository, RepositoryValidationError, assess_adaptive_sl, classify_oqs


def sample_record(**changes):
    data=dict(opportunity_id="OPP-W1-001",symbol="GOLD#",observed_at_utc="2026-07-30T00:00:00+00:00",pattern_family="BREAKOUT_RETEST",pattern_variant="V1",market_regime="TREND",volatility_class="NORMAL",session="LONDON",trend_state="BULLISH",sample_size=120,evidence_quality="HIGH",historical_win_rate=81.5,historical_expectancy=2.4,historical_mae_points=640,historical_mfe_points=2200,research_optimal_sl_points=780,research_optimal_tp_points=2300,opportunity_quality_score=98.4,source_ids=("CASE-001",))
    data.update(changes); return KnowledgeRecord(**data)


def test_oqs_thresholds_are_fail_closed():
    assert classify_oqs(96.999).classification == "WAIT_OR_SKIP"
    assert classify_oqs(97).classification == "GATE_ELIGIBLE"
    assert classify_oqs(98).classification == "HIGH_QUALITY"
    assert classify_oqs(99).classification == "ELITE"
    assert classify_oqs(100).extended_sl_review_eligible is True


def test_adaptive_sl_extended_requires_elite_and_every_gate():
    approved=assess_adaptive_sl(1280,oqs=99.4,final_confidence=99.7,evidence_quality="HIGH",all_gates_passed=True,reward_risk_approved=True)
    assert approved.allowed is True
    assert assess_adaptive_sl(1280,oqs=98.9,final_confidence=100,evidence_quality="HIGH",all_gates_passed=True,reward_risk_approved=True).allowed is False
    assert assess_adaptive_sl(1501,oqs=100,final_confidence=100,evidence_quality="HIGH",all_gates_passed=True,reward_risk_approved=True).allowed is False


def test_repository_is_append_only_and_deduplicated(tmp_path):
    repo=ResearchKnowledgeRepository(tmp_path/"knowledge")
    first=repo.append(sample_record())
    second=repo.append(sample_record())
    assert first["status"] == "WRITTEN"
    assert second["status"] == "DUPLICATE"
    assert len(repo.read_all()) == 1
    index=json.loads(repo.index_path.read_text(encoding="utf-8"))
    assert index["execution_authority"] is False
    assert index["order_send_called"] is False


def test_research_cannot_claim_execution_authority():
    with pytest.raises(RepositoryValidationError, match="research_execution_authority_forbidden"):
        sample_record(execution_authority=True).validate()
    with pytest.raises(RepositoryValidationError, match="research_order_send_forbidden"):
        sample_record(order_send_called=True).validate()


def test_contract_files_match_locked_policy():
    project=Path(__file__).resolve().parents[1]
    oqs=json.loads((project/"config/opportunity_quality_contract.json").read_text(encoding="utf-8"))
    sl=json.loads((project/"config/adaptive_sl_contract.json").read_text(encoding="utf-8"))
    assert oqs["thresholds"][1]["minimum"] == 97
    assert oqs["thresholds"][3]["minimum"] == 99
    assert sl["minimum_sl_points"] == 500
    assert sl["normal_max_sl_points"] == 1000
    assert sl["extended_max_sl_points"] == 1500
    assert sl["extended_requirements"]["oqs_minimum"] == 99
