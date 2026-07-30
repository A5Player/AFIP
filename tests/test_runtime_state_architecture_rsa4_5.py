import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "tools" / "afip_runtime_repository_drift_reconciliation.py"

def load_module():
    spec = importlib.util.spec_from_file_location("rsa45", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_authority_is_guarded_and_non_destructive():
    mod = load_module()
    assert mod.AUTHORITY["deletes_working_tree_files"] is False
    assert mod.AUTHORITY["uses_git_rm_cached_only"] is True
    assert mod.AUTHORITY["commits_git_changes"] is False
    assert mod.AUTHORITY["pushes_git_changes"] is False
    assert mod.AUTHORITY["requires_explicit_apply"] is True

def test_dashboard_paths_are_generated_runtime():
    mod = load_module()
    assert mod.is_approved_generated_runtime(
        "runtime/dashboard/afip_cross_market_intelligence_dashboard.html"
    )

def test_research_paths_are_generated_runtime():
    mod = load_module()
    assert mod.is_approved_generated_runtime(
        "runtime/research/cross_market/observations.jsonl"
    )
    assert mod.is_approved_generated_runtime(
        "runtime/research/trade_cases/CASE-TEST.json"
    )

def test_profile_health_is_generated_runtime():
    mod = load_module()
    assert mod.is_approved_generated_runtime("runtime/profiles/p1/mt5_health.json")

def test_source_paths_are_not_runtime_candidates():
    mod = load_module()
    assert not mod.is_approved_generated_runtime("afip/core/runtime.py")
    assert not mod.is_approved_generated_runtime("tools/example.py")
    assert not mod.is_approved_generated_runtime("tests/test_example.py")

def test_apply_uses_git_rm_cached():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"rm", "--cached", "--", path' in source
    assert '"rm", "--", path' not in source

def test_apply_checks_working_tree_hashes():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "hash_mismatch_after" in source
    assert "WORKING_TREE_FILE_CHANGED" in source

def test_rsa45_source_count():
    mod = load_module()
    assert len(mod.RSA45_SOURCE) == 3
