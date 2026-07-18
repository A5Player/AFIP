from __future__ import annotations
from pathlib import Path
import json
import zipfile
import pytest
from afip.knowledge_portability import KnowledgePortabilityEngine


def sample(tmp_path: Path) -> Path:
    root = tmp_path / "knowledge"
    (root / "certified").mkdir(parents=True)
    (root / "certified" / "a.json").write_text('{"score": 91}\n', encoding="utf-8")
    (root / "lineage").mkdir()
    (root / "lineage" / "a.jsonl").write_text('{"parent": null}\n', encoding="utf-8")
    return root


def test_policy_has_no_execution_authority():
    with pytest.raises(ValueError): KnowledgePortabilityEngine(policy={"execution_authority": "LIVE"})


def test_manifest_inventory_and_hash(tmp_path):
    manifest = KnowledgePortabilityEngine().build_manifest(sample(tmp_path), dataset_name="knowledge")
    assert manifest.file_count == 2 and all(len(e.sha256) == 64 for e in manifest.entries)
    assert manifest.execution_authority == "NONE"


def test_manifest_identity_is_deterministic(tmp_path):
    root = sample(tmp_path); engine = KnowledgePortabilityEngine()
    one = engine.build_manifest(root, dataset_name="knowledge", created_at_utc="2026-01-01T00:00:00Z")
    two = engine.build_manifest(root, dataset_name="knowledge", created_at_utc="2027-01-01T00:00:00Z")
    assert one.bundle_id == two.bundle_id


def test_verify_clean_dataset(tmp_path):
    root = sample(tmp_path); engine = KnowledgePortabilityEngine(); manifest = engine.build_manifest(root, dataset_name="knowledge")
    assert engine.verify_dataset(root, manifest) == ()


def test_verify_detects_tamper(tmp_path):
    root = sample(tmp_path); engine = KnowledgePortabilityEngine(); manifest = engine.build_manifest(root, dataset_name="knowledge")
    (root / "certified" / "a.json").write_text("tampered", encoding="utf-8")
    assert engine.verify_dataset(root, manifest)[0].issue in {"size_mismatch", "checksum_mismatch"}


def test_export_and_inspect_bundle(tmp_path):
    engine = KnowledgePortabilityEngine(); archive, manifest = engine.export_bundle(sample(tmp_path), tmp_path / "out", dataset_name="knowledge")
    observed, issues = engine.inspect_bundle(archive)
    assert observed.bundle_id == manifest.bundle_id and issues == ()


def test_import_defaults_to_verify_only(tmp_path):
    engine = KnowledgePortabilityEngine(); archive, manifest = engine.export_bundle(sample(tmp_path), tmp_path / "out", dataset_name="knowledge")
    result = engine.import_bundle(archive, tmp_path / "imports")
    assert result.status == "VERIFIED_ONLY" and result.destination is None and not (tmp_path / "imports").exists()


def test_import_is_isolated(tmp_path):
    engine = KnowledgePortabilityEngine(); archive, manifest = engine.export_bundle(sample(tmp_path), tmp_path / "out", dataset_name="knowledge")
    result = engine.import_bundle(archive, tmp_path / "imports", verify_only=False)
    assert result.status == "IMPORTED_TO_ISOLATED_DESTINATION"
    assert (Path(result.destination) / "certified" / "a.json").is_file()


def test_import_rejects_existing_destination(tmp_path):
    engine = KnowledgePortabilityEngine(); archive, manifest = engine.export_bundle(sample(tmp_path), tmp_path / "out", dataset_name="knowledge")
    engine.import_bundle(archive, tmp_path / "imports", verify_only=False)
    with pytest.raises(FileExistsError): engine.import_bundle(archive, tmp_path / "imports", verify_only=False)


def test_empty_dataset_rejected(tmp_path):
    empty = tmp_path / "empty"; empty.mkdir()
    with pytest.raises(ValueError): KnowledgePortabilityEngine().build_manifest(empty, dataset_name="empty")


def test_unsafe_manifest_path_is_rejected(tmp_path):
    root = sample(tmp_path); engine = KnowledgePortabilityEngine(); manifest = engine.build_manifest(root, dataset_name="knowledge")
    bad = manifest.to_dict(); bad["entries"][0]["relative_path"] = "../escape.json"
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(bad), encoding="utf-8")
    loaded = engine.load_manifest(path)
    assert engine.verify_dataset(root, loaded)[0].issue == "unsafe_manifest_path"


def test_tampered_bundle_is_rejected(tmp_path):
    engine = KnowledgePortabilityEngine(); archive, manifest = engine.export_bundle(sample(tmp_path), tmp_path / "out", dataset_name="knowledge")
    corrupt = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(archive) as src, zipfile.ZipFile(corrupt, "w") as dst:
        for name in src.namelist(): dst.writestr(name, b"changed" if name.endswith("a.json") else src.read(name))
    result = engine.import_bundle(corrupt, tmp_path / "imports")
    assert result.status == "REJECTED" and result.issues


def test_module_contains_no_broker_or_order_calls():
    source = Path("afip/knowledge_portability/runtime.py").read_text(encoding="utf-8").lower()
    forbidden = ["metatrader5", "order_send(", "order_check(", "terminal64", "mt5.initialize"]
    assert not any(token in source for token in forbidden)
