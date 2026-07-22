from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

from afip.standards.financial_naming_standard import find_obsolete_terms
from .io import atomic_write_json

CACHE_SCHEMA = "afip-financial-naming-fast.v2"
_TEXT_SUFFIXES = {".py", ".ps1", ".bat", ".json", ".toml", ".yaml", ".yml", ".ini", ".cfg"}
_EXCLUDED_PARTS = {
    ".git", ".venv", "runtime", "backup", "backups", "archive", "archives",
    "__pycache__", ".pytest_cache", "node_modules",
}


def _git_changed_files(root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    paths: list[Path] = []
    for raw in completed.stdout.splitlines():
        candidate = (root / raw.strip()).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.is_file():
            paths.append(candidate)
    return paths


def _iter_force_files(root: Path) -> Iterable[Path]:
    for base_name in ("afip", "tools", "config"):
        base = root / base_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in _TEXT_SUFFIXES:
                if not any(part.lower() in _EXCLUDED_PARTS for part in path.parts):
                    yield path
    for pattern in ("*.ps1", "*.bat", "*.py"):
        yield from (p for p in root.glob(pattern) if p.is_file())


def _eligible(root: Path, paths: Iterable[Path]) -> list[Path]:
    output: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        path = path.resolve()
        if path in seen or path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part.lower() in _EXCLUDED_PARTS for part in relative.parts):
            continue
        # Historical pack documentation is not executable source and must not block runtime.
        if path.suffix.lower() == ".md" or relative.parts[0].startswith("AFIP_PROJECT_DATABASE"):
            continue
        seen.add(path)
        output.append(path)
    return sorted(output)


def run_incremental_financial_naming(
    root: Path,
    *,
    force: bool = False,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    """Validate financial terminology without copying or recursively invoking validators.

    Default mode checks only working-tree source changes.  It is intentionally
    independent from AFIP start/status/trading runtime and never blocks trading.
    ``force=True`` scans the current executable source tree, still excluding
    runtime data, generated dashboards, backups and virtual environments.
    """
    root = root.resolve()
    validator = root / "tools" / "validate_financial_naming.py"
    if not validator.exists():
        result = {
            "schema_version": CACHE_SCHEMA, "status": "FAIL",
            "mode": "VALIDATOR_MISSING", "checked_file_count": 0,
            "duration_seconds": 0.0, "violations": [{"file": str(validator), "term": "VALIDATOR_MISSING", "replacement": ""}],
            "runtime_blocking": False, "audit_warning_count": 1,
            "policy": "FAIL_CLOSED_VALIDATOR_REQUIRED",
        }
        atomic_write_json(root / "runtime" / "certification" / "financial_naming_report.json", result)
        return result
    started = time.perf_counter()
    files = _eligible(root, _iter_force_files(root) if force else _git_changed_files(root))
    violations: list[dict[str, Any]] = []

    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as exc:
            violations.append({
                "file": str(path.relative_to(root)),
                "term": "READ_ERROR",
                "replacement": "",
                "message": str(exc),
            })
            continue
        for rule in find_obsolete_terms(text):
            violations.append({
                "file": str(path.relative_to(root)),
                "term": rule.obsolete,
                "replacement": rule.replacement,
            })

    result = {
        "schema_version": CACHE_SCHEMA,
        "status": "PASS" if (not violations or not force) else "FAIL",
        "mode": "FORCE_SOURCE_SCAN" if force else ("CHANGED_FILES" if files else "NO_SOURCE_CHANGES"),
        "checked_file_count": len(files),
        "duration_seconds": round(time.perf_counter() - started, 3),
        "violations": violations,
        "runtime_blocking": False,
        "audit_warning_count": len(violations),
        "policy": "AUDIT_ONLY_CHANGED_FILES" if not force else "STRICT_SOURCE_SCAN",
    }
    report_path = root / "runtime" / "certification" / "financial_naming_report.json"
    atomic_write_json(report_path, result)
    return result
