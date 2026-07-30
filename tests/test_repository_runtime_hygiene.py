from pathlib import Path

from tools.afip_runtime_hygiene_audit import _is_runtime_path


def test_runtime_path_classification() -> None:
    assert _is_runtime_path("runtime/dashboard/example.html")
    assert _is_runtime_path("patch_backups/example/file.txt")
    assert not _is_runtime_path("afip/example.py")
    assert not _is_runtime_path("docs/example.md")


def test_audit_module_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "tools" / "afip_runtime_hygiene_audit.py").exists()
