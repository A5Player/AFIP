from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def load_module():
    path = Path(__file__).parents[1] / "tools" / "afip_runtime_persistence_policy.py"
    spec = importlib.util.spec_from_file_location("afip_rsa2_policy", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_policy_covers_all_rsa1_categories():
    mod = load_module()
    expected = {
        "CERTIFICATION_EVIDENCE", "DASHBOARD_CACHE", "PRODUCTION_EVIDENCE",
        "RESEARCH_DATA", "RUNTIME_STATE", "TEMPORARY_PROCESS_STATE",
        "PERSISTENT_KNOWLEDGE", "UNCLASSIFIED",
    }
    assert expected.issubset(mod.CATEGORY_POLICY)


def test_policy_is_strictly_non_destructive():
    mod = load_module()
    assert mod.AUTHORITY == {
        "moves_files": False,
        "deletes_files": False,
        "restores_files": False,
        "untracks_files": False,
        "changes_gitignore": False,
        "archives_files": False,
        "writes_policy_reports_only": True,
    }


def test_build_policy_preserves_manual_review_gate(tmp_path):
    mod = load_module()
    report = {
        "entries": [
            {"path": "runtime/dashboard/a.html", "git_state": "TRACKED_MODIFIED", "category": "DASHBOARD_CACHE"},
            {"path": "unknown.bin", "git_state": "UNTRACKED", "category": "UNCLASSIFIED"},
        ]
    }
    policy = mod.build_policy(report, tmp_path)
    assert policy["status"] == "REVIEW_REQUIRED"
    assert policy["counts"]["total_decisions"] == 2
    assert policy["manual_review"] == ["unknown.bin"]
    assert policy["rsa3_readiness"]["ready"] is False
    assert all(item["automatic_action_allowed"] is False for item in policy["decisions"])


def test_json_roundtrip(tmp_path):
    mod = load_module()
    policy = mod.build_policy({"entries": []}, tmp_path)
    encoded = json.dumps(policy)
    assert json.loads(encoded)["policy_version"] == "RSA-2.0"
