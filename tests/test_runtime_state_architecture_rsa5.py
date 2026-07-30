import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "tools" / "afip_runtime_post_transition_certification.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rsa5", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_authority_is_certification_only():
    mod = load_module()
    assert mod.AUTHORITY["changes_files"] is False
    assert mod.AUTHORITY["stages_changes"] is False
    assert mod.AUTHORITY["commits_changes"] is False
    assert mod.AUTHORITY["pushes_changes"] is False
    assert mod.AUTHORITY["writes_certification_reports_only"] is True


def test_required_rsa_source_count():
    mod = load_module()
    assert len(mod.REQUIRED_RSA_SOURCE) == 15
    assert "tools/afip_runtime_guarded_git_transition.py" in mod.REQUIRED_RSA_SOURCE


def test_preservation_sample_covers_core_runtime_families():
    mod = load_module()
    joined = "\n".join(mod.WORKING_TREE_PRESERVATION_SAMPLE)
    assert "runtime/dashboard/" in joined
    assert "runtime/research/" in joined
    assert "runtime/profiles/p1/mt5_health.json" in joined


def test_manual_review_count_and_scope():
    mod = load_module()
    assert len(mod.MANUAL_REVIEW) == 4
    assert "capital_binding_verification.json" in mod.MANUAL_REVIEW
    assert "runtime/certification/runtime_truth.json" in mod.MANUAL_REVIEW


def test_managed_markers_are_exact():
    mod = load_module()
    assert mod.MANAGED_MARKERS[0].startswith("# BEGIN AFIP RSA-4")
    assert mod.MANAGED_MARKERS[1].startswith("# END AFIP RSA-4")


def test_commit_message_is_not_executed():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"commit", "-m"' not in source
    assert '"push"' not in source


def test_revision2_distinguishes_cached_and_working_tree_deletion():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "cached_name_status" in source
    assert "working_tree_preserved_after_cached_delete" in source
    assert "accepted_intentionally_absent" in source


def test_manual_review_is_warning_not_integrity_blocker():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"certification_effect": "WARNING_NOT_BLOCKER"' in source
    assert '"manual_snapshot_decision_blocks_integrity_certification": False' in source


def test_blocker_details_are_explicit():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"blocker_details": blocker_details' in source


def test_render_markdown_accepts_revision2_warning_key():
    mod = load_module()
    report = {
        "status": "PASS",
        "commit_readiness": {"ready": True},
        "counts": {
            "blockers": 0,
            "staged_paths": 1,
            "runtime_paths_still_tracked": 0,
        },
        "checks": {"example": True},
        "manual_review_warnings": [
            {
                "path": "runtime/certification/runtime_truth.json",
                "exists": True,
                "tracked": True,
                "staged": False,
                "sha256": "abc",
                "decision": "EXPLICIT_RELEASE_SNAPSHOT_OR_ARCHIVE_REVIEW_REQUIRED",
            }
        ],
    }
    rendered = mod.render_markdown(report)
    assert "runtime/certification/runtime_truth.json" in rendered


def test_render_markdown_backward_compatible_with_old_key():
    mod = load_module()
    report = {
        "status": "PASS",
        "commit_readiness": {"ready": True},
        "counts": {
            "blockers": 0,
            "staged_paths": 1,
            "runtime_paths_still_tracked": 0,
        },
        "checks": {"example": True},
        "manual_review": [],
    }
    rendered = mod.render_markdown(report)
    assert "Post-Transition Certification" in rendered
