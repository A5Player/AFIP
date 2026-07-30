from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "RSA-4.5"

RSA45_SOURCE = [
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA4_5.md",
    "tests/test_runtime_state_architecture_rsa4_5.py",
    "tools/afip_runtime_repository_drift_reconciliation.py",
]

AUTHORITY = {
    "deletes_working_tree_files": False,
    "moves_runtime_files": False,
    "restores_files": False,
    "archives_files": False,
    "commits_git_changes": False,
    "pushes_git_changes": False,
    "uses_git_rm_cached_only": True,
    "stages_rsa45_source_only": True,
    "requires_explicit_apply": True,
    "backs_up_status_and_plan": True,
}

MANAGED_MARKERS = (
    "# BEGIN AFIP RSA-4 MANAGED RUNTIME POLICY",
    "# END AFIP RSA-4 MANAGED RUNTIME POLICY",
)

EXACT_GENERATED_PATHS = {
    "runtime/account_isolation_status.json",
    "runtime/final_integration_status.json",
    "runtime/execution/runtime_cleanup_status.json",
    "runtime/execution/sequential_router_status.json",
    "runtime/control/final_integration/architecture_registry.json",
    "runtime/control/final_integration/desired_runtime_state.json",
    "runtime/control/final_integration/runtime_watchdog_status.json",
    "runtime/control/final_integration/stop_research_runtime.flag",
    "runtime/control/repository_hygiene/runtime_hygiene_audit.json",
    "capital_binding_verification.json",
    "runtime/control/execution_chain_certification.json",
}

GENERATED_PREFIXES = (
    "runtime/dashboard/",
    "runtime/research/",
    "runtime/certification/",
    "runtime/control/runtime_state_architecture/",
)

def run_git(project_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result

def tracked_paths(project_root: Path) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in run_git(project_root, "ls-files").stdout.splitlines()
        if line.strip()
    }

def staged_deleted_paths(project_root: Path) -> set[str]:
    rows = run_git(project_root, "diff", "--cached", "--name-status").stdout.splitlines()
    deleted = set()
    for row in rows:
        parts = row.split("\t")
        if len(parts) >= 2 and parts[0] == "D":
            deleted.add(parts[-1].replace("\\", "/"))
    return deleted

def is_approved_generated_runtime(path: str) -> bool:
    if path in EXACT_GENERATED_PATHS:
        return True
    if path.startswith(GENERATED_PREFIXES):
        return True
    if path.startswith("runtime/profiles/") and (
        path.endswith("/mt5_health.json") or "/production_activation/" in path
    ):
        return True
    return False

def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def build_preview(project_root: Path) -> dict[str, Any]:
    gitignore = project_root / ".gitignore"
    gitignore_text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    managed_block_present = all(marker in gitignore_text for marker in MANAGED_MARKERS)

    tracked = tracked_paths(project_root)
    staged_deleted = staged_deleted_paths(project_root)

    approved_runtime_tracked = sorted(
        path for path in tracked
        if is_approved_generated_runtime(path)
    )
    already_staged_for_untrack = sorted(
        path for path in approved_runtime_tracked
        if path in staged_deleted
    )
    reconciliation_candidates = sorted(
        path for path in approved_runtime_tracked
        if path not in staged_deleted
    )

    candidate_evidence = []
    missing_working_tree = []
    for path in reconciliation_candidates:
        file_path = project_root / path
        exists = file_path.exists()
        if not exists:
            missing_working_tree.append(path)
        candidate_evidence.append({
            "path": path,
            "working_tree_exists": exists,
            "sha256": sha256_file(file_path),
            "action": "GIT_RM_CACHED_ONLY",
        })

    blockers = []
    if not managed_block_present:
        blockers.append("GITIGNORE_MANAGED_BLOCK_MISSING")
    if missing_working_tree:
        blockers.append("CANDIDATE_WORKING_TREE_FILE_MISSING")

    return {
        "status": "READY_FOR_APPLY" if not blockers else "BLOCKED",
        "reconciliation_version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "authority": AUTHORITY,
        "checks": {
            "repository_root_valid": (project_root / ".git").exists(),
            "gitignore_managed_block_present": managed_block_present,
            "candidate_working_tree_integrity_pass": not missing_working_tree,
        },
        "counts": {
            "approved_runtime_tracked": len(approved_runtime_tracked),
            "already_staged_for_untrack": len(already_staged_for_untrack),
            "reconciliation_candidates": len(reconciliation_candidates),
            "missing_working_tree": len(missing_working_tree),
            "blockers": len(blockers),
        },
        "already_staged_for_untrack": already_staged_for_untrack,
        "reconciliation_candidates": reconciliation_candidates,
        "candidate_evidence": candidate_evidence,
        "missing_working_tree": missing_working_tree,
        "blockers": blockers,
        "apply_allowed": not blockers,
        "next_action": (
            "Run with --apply to untrack only approved runtime drift paths."
            if not blockers else
            "Resolve blockers before apply."
        ),
    }

def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AFIP Runtime State Architecture RSA-4.5",
        "",
        "## Repository Drift Reconciliation",
        "",
        f"- Status: **{report['status']}**",
        f"- Apply allowed: **{report['apply_allowed']}**",
        f"- Candidates: **{report['counts']['reconciliation_candidates']}**",
        f"- Missing working-tree files: **{report['counts']['missing_working_tree']}**",
        "",
        "## Candidates",
        "",
    ]
    for item in report["candidate_evidence"]:
        lines.append(
            f"- `{item['path']}` — exists=`{str(item['working_tree_exists']).lower()}` "
            f"action=`{item['action']}`"
        )
    if report["blockers"]:
        lines += ["", "## Blockers", ""]
        for blocker in report["blockers"]:
            lines.append(f"- `{blocker}`")
    return "\n".join(lines)

def write_preview(project_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    output = project_root / "runtime/control/runtime_state_architecture/rsa4_5"
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "repository_drift_reconciliation_preview.json"
    md_path = output / "repository_drift_reconciliation_preview.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path

def apply_reconciliation(project_root: Path, preview: dict[str, Any]) -> dict[str, Any]:
    if not preview["apply_allowed"]:
        raise RuntimeError("RSA-4.5 apply is not allowed.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / "patch_backups" / f"RUNTIME_STATE_ARCHITECTURE_RSA4_5_{timestamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    (backup_root / "git_status_before.txt").write_text(
        run_git(project_root, "status", "--short", "--untracked-files=all").stdout,
        encoding="utf-8",
    )
    (backup_root / "preview.json").write_text(
        json.dumps(preview, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    before_hashes = {
        item["path"]: item["sha256"]
        for item in preview["candidate_evidence"]
    }

    candidates = preview["reconciliation_candidates"]
    for path in candidates:
        run_git(project_root, "rm", "--cached", "--", path)

    for source in RSA45_SOURCE:
        if (project_root / source).exists():
            run_git(project_root, "add", "--", source)

    after_missing = []
    hash_mismatch = []
    for path, before_hash in before_hashes.items():
        file_path = project_root / path
        if not file_path.exists():
            after_missing.append(path)
        elif sha256_file(file_path) != before_hash:
            hash_mismatch.append(path)

    remaining_tracked = sorted(
        path for path in tracked_paths(project_root)
        if is_approved_generated_runtime(path)
    )

    blockers = []
    if after_missing:
        blockers.append("WORKING_TREE_FILE_DELETED")
    if hash_mismatch:
        blockers.append("WORKING_TREE_FILE_CHANGED")
    if remaining_tracked:
        blockers.append("APPROVED_RUNTIME_STILL_TRACKED")

    result = {
        "status": "APPLIED_NOT_COMMITTED" if not blockers else "APPLIED_WITH_BLOCKERS",
        "reconciliation_version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "authority": AUTHORITY,
        "backup_root": str(backup_root),
        "counts": {
            "untracked_cached_only": len(candidates),
            "rsa45_source_staged": sum(
                1 for source in RSA45_SOURCE
                if source in {
                    line.strip().replace("\\", "/")
                    for line in run_git(project_root, "diff", "--cached", "--name-only").stdout.splitlines()
                }
            ),
            "working_tree_missing_after": len(after_missing),
            "hash_mismatch_after": len(hash_mismatch),
            "approved_runtime_still_tracked": len(remaining_tracked),
            "blockers": len(blockers),
        },
        "untracked_cached_only": candidates,
        "working_tree_missing_after": after_missing,
        "hash_mismatch_after": hash_mismatch,
        "approved_runtime_still_tracked": remaining_tracked,
        "blockers": blockers,
        "working_tree_files_deleted": False if not after_missing else True,
        "commit_performed": False,
        "push_performed": False,
        "next_action": (
            "Rerun RSA-5 Revision 3 certification."
            if not blockers else
            "Resolve RSA-4.5 blockers before RSA-5."
        ),
    }

    output = project_root / "runtime/control/runtime_state_architecture/rsa4_5"
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "repository_drift_reconciliation_result.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP RSA-4.5 repository drift reconciliation.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not (project_root / ".git").exists():
        raise RuntimeError(f"Not a Git repository: {project_root}")

    preview = build_preview(project_root)
    outputs = write_preview(project_root, preview)
    preview["outputs"] = [str(path) for path in outputs]
    print(json.dumps(preview, indent=2, ensure_ascii=False))

    if not args.apply:
        return 0 if preview["apply_allowed"] else 2

    result = apply_reconciliation(project_root, preview)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "APPLIED_NOT_COMMITTED" else 3

if __name__ == "__main__":
    raise SystemExit(main())
