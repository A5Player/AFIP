import json
from pathlib import Path

import pytest

from afip.knowledge_certification.runtime import (
    CertificationPolicy,
    KnowledgeCertificationFramework,
    append_jsonl,
    load_policy,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/knowledge_certification/certification_policy.json"


def evidence(i, *, status="VALIDATED_FOR_RESEARCH_REVIEW", regime="TREND", period=None):
    return {
        "evidence_id": f"e{i}",
        "status": status,
        "period_id": period or f"p{i}",
        "market_regime": regime,
        "sample_size": 120,
        "validation_score": 0.84,
        "stability_score": 0.80,
        "drift_score": 0.10,
    }


def framework():
    return KnowledgeCertificationFramework(load_policy(POLICY))


def test_policy_has_no_execution_authority():
    policy = load_policy(POLICY)
    assert policy.execution_authority == "NONE"
    assert policy.promotion_to_execution == "PROHIBITED"
    assert policy.human_review_required is True


def test_strong_evidence_becomes_research_certified():
    rows = [evidence(1, regime="TREND"), evidence(2, regime="RANGE"), evidence(3, regime="TREND")]
    result = framework().certify(knowledge_id="k1", knowledge_version="1", evidence=rows, reviewer="research-board", evaluated_at="2026-07-18T00:00:00+00:00")
    assert result["decision"] == "RESEARCH_CERTIFIED"
    assert result["execution_authority"] == "NONE"


def test_insufficient_evidence_is_pending():
    result = framework().certify(knowledge_id="k1", knowledge_version="1", evidence=[evidence(1)], reviewer="r")
    assert result["decision"] == "CERTIFICATION_PENDING"


def test_rejected_evidence_rejects_certification():
    rows = [evidence(1), evidence(2, regime="RANGE"), evidence(3, status="REJECTED")]
    result = framework().certify(knowledge_id="k1", knowledge_version="1", evidence=rows, reviewer="r")
    assert result["decision"] == "REJECTED"


def test_duplicate_evidence_is_deduplicated():
    row = evidence(1)
    result = framework().certify(knowledge_id="k1", knowledge_version="1", evidence=[row, row], reviewer="r")
    assert result["evidence_count"] == 1


def test_deterministic_id():
    rows = [evidence(1), evidence(2, regime="RANGE"), evidence(3)]
    a = framework().certify(knowledge_id="k1", knowledge_version="1", evidence=rows, reviewer="r", evaluated_at="A")
    b = framework().certify(knowledge_id="k1", knowledge_version="1", evidence=reversed(rows), reviewer="r", evaluated_at="B")
    assert a["certification_id"] == b["certification_id"]


def test_lineage_record_preserves_parent():
    result = framework().certify(knowledge_id="k1", knowledge_version="2", evidence=[evidence(1)], reviewer="r", parent_certification_id="old")
    lineage = framework().lineage_record(result)
    assert lineage["parent_certification_id"] == "old"


def test_append_jsonl_is_append_only(tmp_path):
    path = tmp_path / "ledger.jsonl"
    append_jsonl(path, {"id": 1})
    append_jsonl(path, {"id": 2})
    assert [json.loads(x)["id"] for x in path.read_text().splitlines()] == [1, 2]


def test_invalid_execution_authority_rejected():
    payload = json.loads(POLICY.read_text())
    payload["execution_authority"] = "LIVE"
    with pytest.raises(ValueError):
        CertificationPolicy(**payload).validate()


def test_dataset_info_exists():
    info = json.loads((ROOT / "data/knowledge/certification/dataset_info.json").read_text())
    assert info["schema_version"] == "1.0.0"


def test_guides_exist():
    required = [
        "AFIP_KNOWLEDGE_CERTIFICATION_FRAMEWORK.md",
        "AFIP_KNOWLEDGE_CERTIFICATION_USER_GUIDE.md",
        "AFIP_KNOWLEDGE_CERTIFICATION_TECHNICAL_GUIDE.md",
        "AFIP_KNOWLEDGE_CERTIFICATION_RESEARCH_GUIDE.md",
        "AFIP_KNOWLEDGE_CERTIFICATION_MIGRATION_GUIDE.md",
    ]
    assert all((ROOT / "docs/research" / name).exists() for name in required)


def test_data_dictionary_exists():
    assert (ROOT / "docs/data_dictionary/AFIP_KNOWLEDGE_CERTIFICATION_DATA_DICTIONARY.md").exists()


def test_module_contains_no_execution_calls():
    text = (ROOT / "afip/knowledge_certification/runtime.py").read_text().lower()
    forbidden = ("order_send(", "order_check(", "mt5.initialize", "terminal64", "broker_login")
    assert not any(token in text for token in forbidden)
