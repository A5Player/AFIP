from pathlib import Path

from afip.production_certification.incremental_financial_naming import (
    run_incremental_financial_naming,
)


def test_missing_legacy_validator_fails_without_hanging(tmp_path: Path) -> None:
    (tmp_path / "afip").mkdir()
    (tmp_path / "afip" / "x.py").write_text("x=1\n", encoding="utf-8")
    result = run_incremental_financial_naming(tmp_path, timeout_seconds=1)
    assert result["status"] == "FAIL"
    assert result["mode"] == "VALIDATOR_MISSING"


def test_default_timeout_is_extended() -> None:
    assert run_incremental_financial_naming.__kwdefaults__["timeout_seconds"] == 900
