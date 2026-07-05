"""AFIP Financial Naming validation tests.

This test intentionally validates the official financial naming rule through
AFIP's own validation tool instead of importing legacy AIF symbols.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_financial_naming_validation_passes() -> None:
    """Financial naming validation must pass for the whole AFIP project."""
    project_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "tools/validate_financial_naming.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
