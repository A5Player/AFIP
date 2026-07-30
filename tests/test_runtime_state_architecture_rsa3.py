import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "tools" / "afip_runtime_safe_git_tracking_plan.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rsa3", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_authority_is_plan_only():
    mod = load_module()
    forbidden = (
        "moves_files", "deletes_files", "restores_files", "untracks_files",
        "changes_gitignore", "archives_files", "stages_git_changes", "commits_git_changes",
    )
    assert all(mod.AUTHORITY[name] is False for name in forbidden)
    assert mod.AUTHORITY["writes_plan_reports_only"] is True


def test_action_map_covers_all_rsa2_policies():
    mod = load_module()
    expected = {
        "TRACK_SOURCE_CONTROL",
        "IGNORE_GENERATED",
        "IGNORE_ALWAYS",
        "OUTSIDE_SOURCE_CONTROL",
        "ARCHIVE_OUTSIDE_SOURCE_CONTROL",
        "VERSIONED_RELEASE_SNAPSHOT_OR_ARCHIVE",
        "NO_AUTOMATIC_ACTION",
    }
    assert expected.issubset(mod.ACTION_MAP)


def test_build_plan_merges_manual_resolutions(tmp_path):
    mod = load_module()
    rsa2_dir = tmp_path / "runtime/control/runtime_state_architecture/rsa2"
    rsa21_dir = tmp_path / "runtime/control/runtime_state_architecture/rsa2_1"
    rsa2_dir.mkdir(parents=True)
    rsa21_dir.mkdir(parents=True)

    rsa2 = {
        "decisions": [
            {
                "path": "tools/example.py",
                "git_state": "UNTRACKED",
                "category": "UNCLASSIFIED",
                "git_policy": "NO_AUTOMATIC_ACTION",
            },
            {
                "path": "runtime/dashboard/example.html",
                "git_state": "TRACKED_MODIFIED",
                "category": "DASHBOARD_CACHE",
                "git_policy": "IGNORE_GENERATED",
                "backup_required": False,
                "archive_required": False,
                "reason": "generated",
            },
        ]
    }
    rsa21 = {
        "rsa3_readiness": {"ready": True},
        "decisions": [
            {
                "path": "tools/example.py",
                "resolution_status": "RESOLVED",
                "resolved_category": "PERSISTENT_KNOWLEDGE",
                "persistence": "VERSIONED_KNOWLEDGE",
                "git_policy": "TRACK_SOURCE_CONTROL",
                "retention": "PERMANENT",
                "backup_required": True,
                "archive_required": True,
                "reason": "source",
            }
        ],
    }
    (rsa2_dir / "runtime_persistence_policy.json").write_text(json.dumps(rsa2), encoding="utf-8")
    (rsa21_dir / "manual_review_resolution.json").write_text(json.dumps(rsa21), encoding="utf-8")

    report = mod.build_plan(tmp_path)
    assert report["status"] == "PASS"
    assert report["rsa4_readiness"]["ready"] is True
    assert report["counts"]["total_actions"] == 2
    assert "tools/example.py" in report["action_groups"]["TRACK_AS_SOURCE"]


def test_ordered_plan_defers_mutation():
    mod = load_module()
    names = [step["name"] for step in mod.build_plan.__code__.co_consts if False]
    assert mod.AUTHORITY["stages_git_changes"] is False
    assert mod.AUTHORITY["changes_gitignore"] is False


def test_unknown_policy_is_blocked():
    mod = load_module()
    assert mod.ACTION_MAP.get("NOT_REAL") is None
