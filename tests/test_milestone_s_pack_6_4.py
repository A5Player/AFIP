from hashlib import sha256
import json
from pathlib import Path

import pytest

from afip.knowledge_integrity import IntegrityStatus, KnowledgeIntegrityAuditor


def make_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    root.mkdir()
    (root / "dataset_info.json").write_text(json.dumps({
        "dataset_id": "d1",
        "schema_version": "1.0.0",
        "created_at": "2026-07-18T00:00:00Z",
        "producer": "test",
        "data_classification": "RESEARCH",
    }), encoding="utf-8")
    (root / "guide.md").write_text("guide", encoding="utf-8")
    (root / "payload.json").write_text('{"value":1}', encoding="utf-8")
    return root


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_policy_has_no_execution_authority():
    auditor = KnowledgeIntegrityAuditor({
        "execution_authority": "NONE",
        "automatic_data_repair": "PROHIBITED",
        "automatic_strategy_change": "PROHIBITED",
    })
    assert auditor.policy["execution_authority"] == "NONE"


def test_rejects_execution_authority():
    with pytest.raises(ValueError):
        KnowledgeIntegrityAuditor({"execution_authority": "LIVE"})


def test_healthy_dataset(tmp_path):
    root = make_dataset(tmp_path)
    manifest = {"files": [
        {"path": "dataset_info.json", "sha256": digest(root / "dataset_info.json")},
        {"path": "guide.md", "sha256": digest(root / "guide.md")},
        {"path": "payload.json", "sha256": digest(root / "payload.json")},
    ]}
    report = KnowledgeIntegrityAuditor().audit_dataset(root, manifest, ["guide.md"])
    assert report.status == IntegrityStatus.HEALTHY.value


def test_missing_file_is_corrupted(tmp_path):
    root = make_dataset(tmp_path)
    manifest = {"files": [{"path": "missing.json", "sha256": "0" * 64}]}
    report = KnowledgeIntegrityAuditor().audit_dataset(root, manifest)
    assert report.status == IntegrityStatus.CORRUPTED.value
    assert any(x.code == "FILE_MISSING" for x in report.findings)


def test_hash_mismatch_is_corrupted(tmp_path):
    root = make_dataset(tmp_path)
    manifest = {"files": [{"path": "payload.json", "sha256": "0" * 64}]}
    report = KnowledgeIntegrityAuditor().audit_dataset(root, manifest)
    assert any(x.code == "HASH_MISMATCH" for x in report.findings)


def test_missing_metadata_field_is_corrupted(tmp_path):
    root = make_dataset(tmp_path)
    (root / "dataset_info.json").write_text("{}", encoding="utf-8")
    report = KnowledgeIntegrityAuditor().audit_dataset(root)
    assert report.status == IntegrityStatus.CORRUPTED.value


def test_missing_guide_is_warning(tmp_path):
    root = make_dataset(tmp_path)
    report = KnowledgeIntegrityAuditor().audit_dataset(root, required_guides=["missing.md"])
    assert report.status == IntegrityStatus.WARNING.value


def test_duplicate_manifest_path_is_corrupted(tmp_path):
    root = make_dataset(tmp_path)
    manifest = {"files": [
        {"path": "payload.json", "sha256": digest(root / "payload.json")},
        {"path": "payload.json", "sha256": digest(root / "payload.json")},
    ]}
    report = KnowledgeIntegrityAuditor().audit_dataset(root, manifest)
    assert any(x.code == "MANIFEST_DUPLICATE_PATH" for x in report.findings)


def test_lineage_parent_missing(tmp_path):
    root = make_dataset(tmp_path)
    report = KnowledgeIntegrityAuditor().audit_dataset(
        root,
        lineage_records=[{"knowledge_id": "child", "parent_id": "absent"}],
    )
    assert any(x.code == "LINEAGE_PARENT_MISSING" for x in report.findings)


def test_report_id_is_deterministic(tmp_path):
    root = make_dataset(tmp_path)
    auditor = KnowledgeIntegrityAuditor()
    a = auditor.audit_dataset(root, required_guides=["missing.md"])
    b = auditor.audit_dataset(root, required_guides=["missing.md"])
    assert a.report_id == b.report_id


def test_append_only_ledger(tmp_path):
    root = make_dataset(tmp_path)
    report = KnowledgeIntegrityAuditor().audit_dataset(root)
    ledger = tmp_path / "audit.jsonl"
    KnowledgeIntegrityAuditor.append_audit_ledger(report, ledger)
    KnowledgeIntegrityAuditor.append_audit_ledger(report, ledger)
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 2


def test_quarantine_is_recommendation_only(tmp_path):
    root = make_dataset(tmp_path)
    report = KnowledgeIntegrityAuditor().audit_dataset(root, required_guides=["missing.md"])
    result = KnowledgeIntegrityAuditor.quarantine_recommendation(report)
    assert result["automatic_action_taken"] is False


def test_module_contains_no_broker_or_order_calls():
    source = Path("afip/knowledge_integrity/runtime.py").read_text(encoding="utf-8").lower()
    forbidden = ("metatrader5", "order_send(", "order_check(", "mt5.", "broker.login")
    assert not any(token in source for token in forbidden)
