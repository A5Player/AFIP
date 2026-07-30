from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_RSA_SOURCE = [
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA1.md",
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA2.md",
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA2_1.md",
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA3.md",
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA4.md",
    "tests/test_runtime_state_architecture_rsa1.py",
    "tests/test_runtime_state_architecture_rsa2.py",
    "tests/test_runtime_state_architecture_rsa2_1.py",
    "tests/test_runtime_state_architecture_rsa3.py",
    "tests/test_runtime_state_architecture_rsa4.py",
    "tools/afip_runtime_classification.py",
    "tools/afip_runtime_guarded_git_transition.py",
    "tools/afip_runtime_manual_review_resolution.py",
    "tools/afip_runtime_persistence_policy.py",
    "tools/afip_runtime_safe_git_tracking_plan.py",
]

WORKING_TREE_PRESERVATION_SAMPLE = [
    "runtime/account_isolation_status.json",
    "runtime/control/final_integration/architecture_registry.json",
    "runtime/dashboard/afip_dashboard.html",
    "runtime/execution/runtime_cleanup_status.json",
    "runtime/profiles/p1/mt5_health.json",
    "runtime/research/runtime_observatory_timeline.jsonl",
]

MANUAL_REVIEW = [
    "capital_binding_verification.json",
    "runtime/certification/afip_v1_final_production_certification.json",
    "runtime/certification/runtime_truth.json",
    "runtime/control/execution_chain_certification.json",
]

MANAGED_MARKERS = (
    "# BEGIN AFIP RSA-4 MANAGED RUNTIME POLICY",
    "# END AFIP RSA-4 MANAGED RUNTIME POLICY",
)

AUTHORITY = {
    "changes_files": False,
    "stages_changes": False,
    "unstages_changes": False,
    "commits_changes": False,
    "pushes_changes": False,
    "writes_certification_reports_only": True,
}


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


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def staged_names(project_root: Path) -> list[str]:
    return [
        line.strip().replace("\\", "/")
        for line in run_git(project_root, "diff", "--cached", "--name-only").stdout.splitlines()
        if line.strip()
    ]


def tracked_names(project_root: Path) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in run_git(project_root, "ls-files").stdout.splitlines()
        if line.strip()
    }


def cached_name_status(project_root: Path) -> list[dict[str, str]]:
    rows = []
    raw = run_git(project_root, "diff", "--cached", "--name-status", "-z").stdout.split("\0")
    i = 0
    while i < len(raw):
        status = raw[i]
        i += 1
        if not status:
            continue
        if i >= len(raw):
            break
        path = raw[i].replace("\\", "/")
        i += 1
        if status.startswith(("R", "C")) and i < len(raw):
            path = raw[i].replace("\\", "/")
            i += 1
        rows.append({"status": status, "path": path})
    return rows


def is_generated_transition_path(path: str) -> bool:
    return (
        path.startswith("runtime/dashboard/")
        or path.startswith("runtime/research/")
        or path.startswith("runtime/profiles/") and (
            path.endswith("/mt5_health.json") or "/production_activation/" in path
        )
        or path in {
            "runtime/account_isolation_status.json",
            "runtime/final_integration_status.json",
            "runtime/execution/runtime_cleanup_status.json",
            "runtime/execution/sequential_router_status.json",
            "runtime/control/final_integration/architecture_registry.json",
        }
    )


def build_certification(project_root: Path) -> dict[str, Any]:
    rsa4_result_path = project_root / "runtime/control/runtime_state_architecture/rsa4/guarded_git_transition_result.json"
    if not rsa4_result_path.exists():
        raise FileNotFoundError(f"RSA-4 result not found: {rsa4_result_path}")
    rsa4 = json.loads(rsa4_result_path.read_text(encoding="utf-8"))
    if rsa4.get("status") != "APPLIED_NOT_COMMITTED":
        raise RuntimeError("RSA-4 result is not APPLIED_NOT_COMMITTED.")

    staged = staged_names(project_root)
    cached_changes = cached_name_status(project_root)
    tracked = tracked_names(project_root)

    rsa_source_present = [
        path for path in REQUIRED_RSA_SOURCE
        if path in staged or path in tracked
    ]
    missing_rsa_source = [
        path for path in REQUIRED_RSA_SOURCE
        if path not in staged and path not in tracked
    ]

    gitignore = project_root / ".gitignore"
    gitignore_text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    managed_markers_present = all(marker in gitignore_text for marker in MANAGED_MARKERS)

    staged_index_deletions = [
        item["path"] for item in cached_changes if item["status"] == "D"
    ]
    generated_index_deletions = [
        path for path in staged_index_deletions if is_generated_transition_path(path)
    ]

    intentionally_absent = {
        "AFIP_V1_FINAL_REVISION_3_REPLAY_THROUGHPUT.zip",
        "runtime/control/final_integration/stop_research_runtime.flag",
    }
    preserved_after_cached_delete = []
    missing_after_cached_delete = []
    accepted_absent = []

    for path in staged_index_deletions:
        if path in intentionally_absent:
            accepted_absent.append(path)
        elif (project_root / path).exists():
            preserved_after_cached_delete.append(path)
        else:
            missing_after_cached_delete.append(path)

    still_tracked_runtime = sorted(
        path for path in tracked if is_generated_transition_path(path)
    )

    manual_review_state = []
    for path in MANUAL_REVIEW:
        file_path = project_root / path
        manual_review_state.append({
            "path": path,
            "exists": file_path.exists(),
            "tracked": path in tracked,
            "staged": path in staged,
            "sha256": sha256_file(file_path),
            "decision": "EXPLICIT_RELEASE_SNAPSHOT_OR_ARCHIVE_REVIEW_REQUIRED",
            "certification_effect": "WARNING_NOT_BLOCKER",
        })

    blockers = []
    blocker_details = []
    if missing_rsa_source:
        blockers.append("RSA_SOURCE_MISSING")
        blocker_details.extend({"code": "RSA_SOURCE_MISSING", "path": p} for p in missing_rsa_source)
    if missing_after_cached_delete:
        blockers.append("WORKING_TREE_DATA_MISSING")
        blocker_details.extend({"code": "WORKING_TREE_DATA_MISSING", "path": p} for p in missing_after_cached_delete)
    if not managed_markers_present:
        blockers.append("GITIGNORE_MANAGED_BLOCK_MISSING")
        blocker_details.append({"code": "GITIGNORE_MANAGED_BLOCK_MISSING", "path": ".gitignore"})
    if still_tracked_runtime:
        blockers.append("RUNTIME_PATHS_STILL_TRACKED")
        blocker_details.extend({"code": "RUNTIME_PATHS_STILL_TRACKED", "path": p} for p in still_tracked_runtime)
    if not staged:
        blockers.append("NO_STAGED_TRANSITION")
        blocker_details.append({"code": "NO_STAGED_TRANSITION", "path": None})

    report = {
        "status": "PASS" if not blockers else "FAIL",
        "reason": (
            "post_transition_integrity_certified_manual_snapshot_review_remains"
            if not blockers else
            "post_transition_integrity_blocked"
        ),
        "certification_version": "RSA-5.3",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "authority": AUTHORITY,
        "rsa4_result": str(rsa4_result_path),
        "checks": {
            "rsa4_applied_not_committed": True,
            "managed_gitignore_block_present": managed_markers_present,
            "staged_transition_present": bool(staged),
            "cached_only_deletion_integrity_pass": not missing_after_cached_delete,
            "runtime_untracked_from_git_index": not still_tracked_runtime,
            "rsa_source_present": not missing_rsa_source,
            "manual_snapshot_review_is_warning_only": True,
        },
        "counts": {
            "staged_paths": len(staged),
            "staged_index_deletions": len(staged_index_deletions),
            "generated_index_deletions": len(generated_index_deletions),
            "working_tree_preserved_after_cached_delete": len(preserved_after_cached_delete),
            "accepted_intentionally_absent": len(accepted_absent),
            "working_tree_missing": len(missing_after_cached_delete),
            "rsa_source_present": len(rsa_source_present),
            "rsa_source_missing": len(missing_rsa_source),
            "runtime_paths_still_tracked": len(still_tracked_runtime),
            "manual_review_warnings": len(manual_review_state),
            "blockers": len(blockers),
        },
        "staged_paths": staged,
        "staged_index_deletions": staged_index_deletions,
        "working_tree_preserved_after_cached_delete": preserved_after_cached_delete,
        "accepted_intentionally_absent": accepted_absent,
        "working_tree_missing": missing_after_cached_delete,
        "rsa_source_present": rsa_source_present,
        "rsa_source_missing": missing_rsa_source,
        "runtime_paths_still_tracked": still_tracked_runtime,
        "manual_review_warnings": manual_review_state,
        "blockers": blockers,
        "blocker_details": blocker_details,
        "commit_readiness": {
            "ready": not blockers,
            "commit_message": "Complete AFIP Runtime State Architecture RSA-1 to RSA-5",
            "requires_manual_snapshot_decision": True,
            "manual_snapshot_decision_blocks_integrity_certification": False,
            "note": (
                "Integrity is certified. The four evidence items remain an explicit release-management decision."
                if not blockers else
                "Do not commit until listed blocker_details are resolved."
            ),
        },
        "next_action": (
            "Review staged diff and four evidence warnings, then use the final commit pack."
            if not blockers else
            "Resolve exact blocker_details and rerun RSA-5 Revision 2."
        ),
    }
    return report

def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AFIP Runtime State Architecture RSA-5",
        "",
        "## Post-Transition Certification",
        "",
        f"- Status: **{report['status']}**",
        f"- Commit ready: **{report['commit_readiness']['ready']}**",
        f"- Blockers: **{report['counts']['blockers']}**",
        f"- Staged paths: **{report['counts']['staged_paths']}**",
        f"- Runtime paths still tracked: **{report['counts']['runtime_paths_still_tracked']}**",
        "",
        "## Checks",
        "",
    ]
    for key, value in report["checks"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines += ["", "## Manual Certification Evidence Review", ""]
    for item in report.get("manual_review_warnings", report.get("manual_review", [])):
        lines += [
            f"### `{item['path']}`",
            "",
            f"- Exists: `{str(item['exists']).lower()}`",
            f"- Tracked: `{str(item['tracked']).lower()}`",
            f"- Staged: `{str(item['staged']).lower()}`",
            f"- SHA256: `{item['sha256']}`",
            f"- Decision: `{item['decision']}`",
            "",
        ]
    return "\n".join(lines)


def write_reports(project_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    output = project_root / "runtime/control/runtime_state_architecture/rsa5"
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "post_transition_certification.json"
    md_path = output / "post_transition_certification.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Certify RSA-4 transition without mutation.")
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not (project_root / ".git").exists():
        raise RuntimeError(f"Not a Git repository: {project_root}")

    report = build_certification(project_root)
    outputs = write_reports(project_root, report)
    report["outputs"] = [str(path) for path in outputs]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
