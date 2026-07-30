from pathlib import Path
import importlib.util


def load_module():
    path = Path(__file__).parents[1] / "tools" / "afip_runtime_classification.py"
    spec = importlib.util.spec_from_file_location("rsa1", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_classification_rules_cover_known_runtime_families():
    mod = load_module()
    assert mod.classify("runtime/dashboard/afip_dashboard.html") == "DASHBOARD_CACHE"
    assert mod.classify("runtime/control/final_integration/runtime_watchdog.pid") == "TEMPORARY_PROCESS_STATE"
    assert mod.classify("runtime/certification/final.json") == "CERTIFICATION_EVIDENCE"
    assert mod.classify("runtime/profiles/p1/production_activation/status.json") == "PRODUCTION_EVIDENCE"
    assert mod.classify("runtime/research/replay_performance.json") == "RESEARCH_DATA"
    assert mod.classify("runtime/profiles/p1/mt5_health.json") == "RUNTIME_STATE"


def test_policy_is_non_destructive():
    mod = load_module()
    assert mod.POLICY_HINTS["TEMPORARY_PROCESS_STATE"] == "IGNORE"
    report_authority = {
        "moves_files": False,
        "deletes_files": False,
        "restores_files": False,
        "untracks_files": False,
        "changes_gitignore": False,
    }
    assert not any(report_authority.values())


def test_python_314_safe_dynamic_import_entry_serialization():
    mod = load_module()
    entry = mod.Entry(
        path="runtime/example.json",
        git_state="UNTRACKED",
        category="RUNTIME_STATE",
        policy_hint="GENERATED_RUNTIME_STATE",
        size_bytes=12,
        exists=True,
    )
    assert entry.to_dict() == {
        "path": "runtime/example.json",
        "git_state": "UNTRACKED",
        "category": "RUNTIME_STATE",
        "policy_hint": "GENERATED_RUNTIME_STATE",
        "size_bytes": 12,
        "exists": True,
    }
