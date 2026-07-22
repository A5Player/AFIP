from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .fingerprint import iter_relevant_files, repository_fingerprint
from .io import atomic_write_json

CACHE_SCHEMA = "afip-financial-naming-cache.v1"


def _load_cache(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def _copy_validation_tree(root: Path, temporary_root: Path) -> int:
    copied = 0
    for source in iter_relevant_files(root):
        relative = source.relative_to(root)
        target = temporary_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    return copied


def run_incremental_financial_naming(
    root: Path,
    *,
    force: bool = False,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    root = root.resolve()
    runtime_dir = root / "runtime" / "certification"
    cache_path = runtime_dir / "financial_naming_cache.json"
    report_path = runtime_dir / "financial_naming_report.json"
    fingerprint, relevant_files = repository_fingerprint(root)
    cache = _load_cache(cache_path)

    if (
        not force
        and cache.get("schema_version") == CACHE_SCHEMA
        and cache.get("fingerprint") == fingerprint
        and cache.get("status") == "PASS"
    ):
        result = {
            "schema_version": CACHE_SCHEMA,
            "status": "PASS",
            "mode": "CACHE_HIT",
            "fingerprint": fingerprint,
            "relevant_file_count": len(relevant_files),
            "duration_seconds": 0.0,
            "legacy_validator": "SKIPPED_UNCHANGED",
        }
        atomic_write_json(report_path, result)
        return result

    legacy = root / "tools" / "validate_financial_naming_legacy.py"
    if not legacy.exists():
        result = {
            "schema_version": CACHE_SCHEMA,
            "status": "FAIL",
            "mode": "VALIDATOR_MISSING",
            "fingerprint": fingerprint,
            "relevant_file_count": len(relevant_files),
            "message": str(legacy),
        }
        atomic_write_json(report_path, result)
        return result

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="afip_financial_naming_") as temp:
        temp_root = Path(temp)
        copied = _copy_validation_tree(root, temp_root)
        legacy_target = temp_root / "tools" / "validate_financial_naming.py"
        legacy_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, legacy_target)
        try:
            completed = subprocess.run(
                [sys.executable, str(legacy_target)],
                cwd=str(temp_root),
                capture_output=True,
                text=True,
                timeout=max(1, timeout_seconds),
                check=False,
            )
            status = "PASS" if completed.returncode == 0 else "FAIL"
            result = {
                "schema_version": CACHE_SCHEMA,
                "status": status,
                "mode": "INCREMENTAL_SANDBOX",
                "fingerprint": fingerprint,
                "relevant_file_count": len(relevant_files),
                "copied_file_count": copied,
                "duration_seconds": round(time.perf_counter() - started, 3),
                "return_code": completed.returncode,
                "stdout": completed.stdout[-12000:],
                "stderr": completed.stderr[-12000:],
            }
        except subprocess.TimeoutExpired as exc:
            result = {
                "schema_version": CACHE_SCHEMA,
                "status": "FAIL",
                "mode": "TIMEOUT",
                "fingerprint": fingerprint,
                "relevant_file_count": len(relevant_files),
                "copied_file_count": copied,
                "duration_seconds": round(time.perf_counter() - started, 3),
                "timeout_seconds": timeout_seconds,
                "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "")[-12000:] if isinstance(exc.stderr, str) else "",
            }

    atomic_write_json(report_path, result)
    if result["status"] == "PASS":
        atomic_write_json(
            cache_path,
            {
                "schema_version": CACHE_SCHEMA,
                "status": "PASS",
                "fingerprint": fingerprint,
                "relevant_file_count": len(relevant_files),
            },
        )
    return result
