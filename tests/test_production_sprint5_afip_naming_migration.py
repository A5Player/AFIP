from pathlib import Path


def test_official_afip_launcher_exists():
    root = Path(__file__).resolve().parents[1]
    launcher = root / "afip.py"
    assert launcher.exists()
    text = launcher.read_text(encoding="utf-8")
    assert "AFIP — Automated Financial Intelligence Platform" in text
    assert "simulate" in text
    assert "mt5-check" in text


def test_migration_tool_is_dry_run_safe():
    root = Path(__file__).resolve().parents[1]
    tool = root / "tools" / "afip_naming_migration.py"
    assert tool.exists()
    text = tool.read_text(encoding="utf-8")
    assert "Dry-run by default" in text
    assert "--apply" in text
    assert "backup" in text
