"""AFIP local quality check.

Runs the checks that should be executed on the user's Windows/MT5 machine
before every commit and push.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str]


def run_check(check: Check) -> bool:
    print(f"\n=== {check.name} ===")
    print("$ " + " ".join(check.command))
    result = subprocess.run(check.command, text=True)
    if result.returncode == 0:
        print(f"PASS: {check.name}")
        return True
    print(f"FAIL: {check.name} (exit={result.returncode})")
    return False


def main() -> int:
    checks: Iterable[Check] = (
        Check("Financial Naming Validation", [sys.executable, "tools/validate_financial_naming.py"]),
        Check("AFIP Simulation", [sys.executable, "afip.py", "simulate"]),
        Check("MT5 Data Check", [sys.executable, "afip.py", "mt5-check"]),
        Check("Pytest", [sys.executable, "-m", "pytest", "-q"]),
    )

    failed: list[str] = []
    for check in checks:
        if not run_check(check):
            failed.append(check.name)

    print("\n=== AFIP Local Quality Summary ===")
    if not failed:
        print("Status: PASS")
        return 0

    print("Status: FAIL")
    for name in failed:
        print(f" - {name}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
