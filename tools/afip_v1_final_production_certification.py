from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROHIBITED_UNTRACKED = {
    "runtime/dashboard/dashboard_runtime.json",
    "runtime/profiles/p1/mt5_live_snapshot.json",
    "runtime/profiles/p2/mt5_live_snapshot.json",
    "runtime/profiles/p3/mt5_live_snapshot.json",
    "runtime/profiles/p4/mt5_live_snapshot.json",
    "AFIP_CAPITAL_AUTHORITY_AUDIT.txt",
}

PROHIBITED_PREFIXES = (
    "AFIP_MAXIMUM_LOT_AUTHORITY_FINAL_PATCH/",
)

GENERATED_TRACKED = {
    "runtime/certification/financial_naming_report.json",
    "runtime/dashboard/afip_control_center.html",
    "runtime/dashboard/afip_dashboard.html",
    "runtime/dashboard/afip_intelligence_engine_dashboard.html",
    "runtime/dashboard/afip_profiles_dashboard.html",
    "runtime/dashboard/afip_research_data_dashboard.html",
    "runtime/dashboard/afip_research_operations_dashboard.html",
    "runtime/dashboard/production_authority_snapshot.json",
    "runtime/profiles/p1/mt5_health.json",
    "runtime/profiles/p2/mt5_health.json",
    "runtime/profiles/p3/mt5_health.json",
    "runtime/profiles/p4/mt5_health.json",
}


def run_git(project_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def parse_porcelain_z(raw: str) -> list[tuple[str, str]]:
    if not raw:
        return []
    parts = raw.split("\0")
    rows: list[tuple[str, str]] = []
    index = 0
    while index < len(parts):
        record = parts[index]
        if not record:
            index += 1
            continue
        status = record[:2]
        path = record[3:].replace("\\", "/")
        rows.append((status, path))
        if status[0] in {"R", "C"}:
            index += 1
        index += 1
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    required = [
        root / "afip",
        root / "config" / "four_profile_demo.json",
        root / "tests",
        root / ".git",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(json.dumps({"status": "FAIL", "missing": missing}, indent=2))
        return 2

    rows = parse_porcelain_z(run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"))
    errors: list[str] = []
    warnings: list[str] = []

    for status, path in rows:
        if path in PROHIBITED_UNTRACKED and status == "??":
            errors.append(f"runtime/local-only output remains untracked: {path}")
        if status == "??" and any(path.startswith(prefix) for prefix in PROHIBITED_PREFIXES):
            errors.append(f"extracted patch workspace remains: {path}")
        if path in GENERATED_TRACKED and status.strip():
            errors.append(f"generated tracked snapshot is still modified: {path}")
        if path.endswith(".pyc") or "/__pycache__/" in f"/{path}":
            errors.append(f"Python cache is present in Git status: {path}")
        if path.startswith(".pytest_cache/"):
            errors.append(f"pytest cache is present in Git status: {path}")

    deleted_archive = [
        path for status, path in rows
        if path == "AFIP_V1_FINAL_REVISION_3_REPLAY_THROUGHPUT.zip" and "D" in status
    ]
    if deleted_archive:
        errors.append("tracked replay throughput archive remains deleted")

    if not rows:
        warnings.append("working tree has no changes; confirm the intended AFIP source patches were copied")

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "changed_path_count": len(rows),
        "errors": errors,
        "warnings": warnings,
        "policy": {
            "trading_logic_modified_by_this_pack": False,
            "runtime_started_by_this_pack": False,
            "mt5_started_by_this_pack": False,
            "git_staging_performed_by_this_pack": False,
        },
    }
    print(json.dumps(payload, indent=2))

    report_path = root / "AFIP_V1_FINAL_PRODUCTION_CERTIFICATION_REPORT.json"
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
