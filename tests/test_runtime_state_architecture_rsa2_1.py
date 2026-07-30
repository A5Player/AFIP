import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "tools" / "afip_runtime_manual_review_resolution.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rsa2_1", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_all_expected_manual_review_items_are_resolved():
    mod = load_module()
    assert len(mod.RESOLUTIONS) == 5
    assert all(v["automatic_action_allowed"] is False for v in mod.RESOLUTIONS.values())


def test_rsa_source_files_are_versioned_knowledge():
    mod = load_module()
    for path in (
        "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA1.md",
        "tests/test_runtime_state_architecture_rsa1.py",
        "tools/afip_runtime_classification.py",
    ):
        assert mod.RESOLUTIONS[path]["resolved_category"] == "PERSISTENT_KNOWLEDGE"
        assert mod.RESOLUTIONS[path]["git_policy"] == "TRACK_SOURCE_CONTROL"


def test_evidence_is_not_implicitly_committed():
    mod = load_module()
    capital = mod.RESOLUTIONS["capital_binding_verification.json"]
    archive = mod.RESOLUTIONS["AFIP_V1_FINAL_REVISION_3_REPLAY_THROUGHPUT.zip"]
    assert capital["resolved_category"] == "CERTIFICATION_EVIDENCE"
    assert archive["git_policy"] == "ARCHIVE_OUTSIDE_SOURCE_CONTROL"


def test_authority_is_non_destructive():
    mod = load_module()
    forbidden = (
        "moves_files", "deletes_files", "restores_files", "untracks_files",
        "changes_gitignore", "archives_files", "stages_git_changes", "commits_git_changes",
    )
    assert all(mod.AUTHORITY[name] is False for name in forbidden)


def test_build_resolution_with_rsa2_contract(tmp_path):
    mod = load_module()
    source = tmp_path / "runtime/control/runtime_state_architecture/rsa2"
    source.mkdir(parents=True)
    blockers = list(mod.RESOLUTIONS)
    (source / "runtime_persistence_policy.json").write_text(
        json.dumps({"rsa3_readiness": {"blockers": blockers}}),
        encoding="utf-8",
    )
    report = mod.build_resolution(tmp_path)
    assert report["status"] == "PASS"
    assert report["rsa3_readiness"]["ready"] is True
    assert report["counts"]["resolved"] == 5
    assert report["counts"]["unresolved"] == 0
