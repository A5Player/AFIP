import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "tools" / "afip_runtime_guarded_git_transition.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rsa4", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_authority_preserves_working_tree():
    mod = load_module()
    assert mod.AUTHORITY["deletes_working_tree_files"] is False
    assert mod.AUTHORITY["uses_git_rm_cached_only"] is True
    assert mod.AUTHORITY["commits_git_changes"] is False
    assert mod.AUTHORITY["pushes_git_changes"] is False
    assert mod.AUTHORITY["requires_explicit_apply"] is True


def test_gitignore_block_is_idempotent():
    mod = load_module()
    first = mod.update_gitignore_content("*.pyc\n")
    second = mod.update_gitignore_content(first)
    assert first == second
    assert first.count(mod.MANAGED_BLOCK_BEGIN) == 1
    assert first.count(mod.MANAGED_BLOCK_END) == 1


def test_existing_managed_block_is_replaced():
    mod = load_module()
    old = (
        "before\n\n"
        + mod.MANAGED_BLOCK_BEGIN
        + "\n/old/\n"
        + mod.MANAGED_BLOCK_END
        + "\n\nafter\n"
    )
    updated = mod.update_gitignore_content(old)
    assert "/old/" not in updated
    assert "/runtime/research/" in updated
    assert "before" in updated
    assert "after" in updated


def test_rsa_source_detection():
    mod = load_module()
    assert mod.is_rsa_source("tools/afip_runtime_classification.py")
    assert mod.is_rsa_source("tests/test_runtime_state_architecture_rsa4.py")
    assert mod.is_rsa_source("docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA4.md")
    assert not mod.is_rsa_source("runtime/dashboard/afip_dashboard.html")


def test_porcelain_parser():
    mod = load_module()
    raw = " M runtime/a.json\0?? tools/afip_runtime_new.py\0"
    parsed = mod.parse_porcelain_z(raw)
    assert parsed == [
        {"status": " M", "path": "runtime/a.json"},
        {"status": "??", "path": "tools/afip_runtime_new.py"},
    ]


def test_ignore_rules_cover_runtime_families():
    mod = load_module()
    block = "\n".join(mod.IGNORE_RULES)
    assert "/runtime/dashboard/" in block
    assert "/runtime/research/" in block
    assert "/runtime/profiles/*/production_activation/" in block
    assert "/runtime/control/runtime_state_architecture/" in block


def test_preview_uses_full_untracked_enumeration():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"--untracked-files=all"' in source


def test_approved_runtime_families_are_declared():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"runtime/control/runtime_state_architecture/"' in source
    assert '"runtime/control/repository_hygiene/"' in source
    assert '"runtime/profiles/p1/production_activation/"' in source
