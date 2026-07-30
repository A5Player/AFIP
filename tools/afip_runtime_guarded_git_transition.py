from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANAGED_BLOCK_BEGIN = "# BEGIN AFIP RSA-4 MANAGED RUNTIME POLICY"
MANAGED_BLOCK_END = "# END AFIP RSA-4 MANAGED RUNTIME POLICY"

IGNORE_RULES = [
    "# Generated runtime state and dashboards",
    "/runtime/dashboard/",
    "/runtime/account_isolation_status.json",
    "/runtime/final_integration_status.json",
    "/runtime/execution/runtime_cleanup_status.json",
    "/runtime/execution/sequential_router_status.json",
    "/runtime/profiles/*/mt5_health.json",
    "/runtime/control/final_integration/architecture_registry.json",
    "/runtime/control/final_integration/desired_runtime_state.json",
    "/runtime/control/final_integration/runtime_watchdog_status.json",
    "/runtime/control/final_integration/stop_research_runtime.flag",
    "/runtime/control/repository_hygiene/runtime_hygiene_audit.json",
    "",
    "# Durable runtime data retained outside source control",
    "/runtime/research/",
    "/runtime/profiles/*/production_activation/",
    "",
    "# Generated certification evidence; release snapshots require explicit review",
    "/capital_binding_verification.json",
    "/runtime/certification/",
    "/runtime/control/execution_chain_certification.json",
    "",
    "# RSA-generated reports",
    "/runtime/control/runtime_state_architecture/",
]

RSA_SOURCE_PREFIXES = (
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA",
    "tests/test_runtime_state_architecture_rsa",
    "tools/afip_runtime_",
)

AUTHORITY = {
    "deletes_working_tree_files": False,
    "moves_runtime_files": False,
    "restores_files": False,
    "archives_files": False,
    "commits_git_changes": False,
    "pushes_git_changes": False,
    "uses_git_rm_cached_only": True,
    "backs_up_gitignore": True,
    "backs_up_status_and_plan": True,
    "requires_explicit_apply": True,
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


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def parse_porcelain_z(raw: str) -> list[dict[str, str]]:
    parts = raw.split("\0")
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(parts):
        item = parts[index]
        index += 1
        if not item:
            continue
        status = item[:2]
        path = item[3:]
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            if index < len(parts):
                new_path = parts[index]
                index += 1
                path = new_path
        entries.append({"status": status, "path": path.replace("\\", "/")})
    return entries


def is_rsa_source(path: str) -> bool:
    return path.startswith(RSA_SOURCE_PREFIXES) and path.endswith((".py", ".md"))


def managed_block() -> str:
    return "\n".join([MANAGED_BLOCK_BEGIN, *IGNORE_RULES, MANAGED_BLOCK_END])


def update_gitignore_content(existing: str) -> str:
    start = existing.find(MANAGED_BLOCK_BEGIN)
    end = existing.find(MANAGED_BLOCK_END)
    block = managed_block()
    if start >= 0 and end >= start:
        end += len(MANAGED_BLOCK_END)
        before = existing[:start].rstrip()
        after = existing[end:].lstrip("\r\n")
        pieces = [piece for piece in (before, block, after.rstrip()) if piece]
        return "\n\n".join(pieces) + "\n"
    prefix = existing.rstrip()
    return (prefix + "\n\n" if prefix else "") + block + "\n"


def load_rsa3_plan(project_root: Path) -> dict[str, Any]:
    path = project_root / "runtime/control/runtime_state_architecture/rsa3/safe_git_tracking_plan.json"
    if not path.exists():
        raise FileNotFoundError(f"RSA-3 plan not found: {path}")
    plan = read_json(path)
    if plan.get("rsa4_readiness", {}).get("ready") is not True:
        raise RuntimeError("RSA-3 has not marked RSA-4 ready.")
    return plan


def build_transition(project_root: Path) -> dict[str, Any]:
    plan = load_rsa3_plan(project_root)
    status_raw = run_git(project_root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    status_entries = parse_porcelain_z(status_raw)

    planned_paths = {item["path"] for item in plan.get("actions", [])}
    rsa_sources = sorted({
        item["path"] for item in status_entries if is_rsa_source(item["path"])
    })

    approved_generated_prefixes = (
        "runtime/control/runtime_state_architecture/",
        "runtime/control/repository_hygiene/",
        "runtime/profiles/p1/production_activation/",
        "runtime/profiles/p2/production_activation/",
        "runtime/profiles/p3/production_activation/",
        "runtime/profiles/p4/production_activation/",
    )

    def is_approved_path(path: str) -> bool:
        if path in planned_paths or is_rsa_source(path):
            return True
        return path.startswith(approved_generated_prefixes)

    unknown_drift = sorted({
        item["path"] for item in status_entries
        if not is_approved_path(item["path"])
    })

    untrack_actions = {
        "PLAN_IGNORE_AND_UNTRACK_IF_ALREADY_TRACKED",
        "PLAN_EXTERNAL_PERSISTENCE_AND_UNTRACK",
        "PLAN_ARCHIVE_VERIFY_AND_UNTRACK",
    }
    candidate_untrack = sorted({
        item["path"] for item in plan.get("actions", [])
        if item.get("planned_action") in untrack_actions
    })

    tracked = set(
        line.strip().replace("\\", "/")
        for line in run_git(project_root, "ls-files").stdout.splitlines()
        if line.strip()
    )
    tracked_untrack = [path for path in candidate_untrack if path in tracked]

    transient_accept = sorted({
        item["path"] for item in plan.get("actions", [])
        if item.get("planned_action") == "PLAN_IGNORE_AND_ACCEPT_TRANSIENT_DELETION"
    })

    release_review = sorted({
        item["path"] for item in plan.get("actions", [])
        if item.get("planned_action") == "PLAN_RELEASE_SNAPSHOT_DECISION"
    })

    report = {
        "status": "READY_FOR_APPLY" if not unknown_drift else "BLOCKED_BY_REPOSITORY_DRIFT",
        "transition_version": "RSA-4.2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "authority": AUTHORITY,
        "preflight": {
            "rsa3_ready": True,
            "repository_root_valid": (project_root / ".git").exists(),
            "unknown_drift_count": len(unknown_drift),
            "unknown_drift": unknown_drift,
            "rsa_source_count": len(rsa_sources),
            "rsa_sources_to_track": rsa_sources,
        },
        "planned_changes": {
            "gitignore_managed_block": IGNORE_RULES,
            "tracked_paths_to_untrack_cached_only": tracked_untrack,
            "transient_deletions_to_accept": transient_accept,
            "release_snapshot_manual_review": release_review,
        },
        "counts": {
            "tracked_paths_to_untrack_cached_only": len(tracked_untrack),
            "rsa_sources_to_track": len(rsa_sources),
            "release_snapshot_manual_review": len(release_review),
            "unknown_drift": len(unknown_drift),
        },
        "apply_allowed": not unknown_drift,
        "next_action": (
            "Run with --apply after reviewing this preview."
            if not unknown_drift else
            "Resolve or classify repository drift, regenerate RSA-1 through RSA-3, then retry."
        ),
    }
    return report


def write_preview(project_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    output = project_root / "runtime/control/runtime_state_architecture/rsa4"
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "guarded_git_transition_preview.json"
    md_path = output / "guarded_git_transition_preview.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# AFIP RSA-4 Guarded Git Transition",
        "",
        f"- Status: **{report['status']}**",
        f"- Apply allowed: **{report['apply_allowed']}**",
        f"- Unknown drift: **{report['counts']['unknown_drift']}**",
        f"- RSA source files to track: **{report['counts']['rsa_sources_to_track']}**",
        f"- Tracked runtime/data paths to untrack (cached only): **{report['counts']['tracked_paths_to_untrack_cached_only']}**",
        "",
        "## Unknown Drift",
        "",
    ]
    for path in report["preflight"]["unknown_drift"]:
        lines.append(f"- `{path}`")
    lines += ["", "## Working-tree Safety", "", "- No working-tree file deletion.", "- Git index transition uses `git rm --cached` only.", "- No commit and no push.", ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def make_backup(project_root: Path, report: dict[str, Any]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project_root / "patch_backups" / f"RUNTIME_STATE_ARCHITECTURE_RSA4_{timestamp}"
    backup.mkdir(parents=True, exist_ok=False)

    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        shutil_target = backup / ".gitignore.before"
        shutil_target.write_bytes(gitignore.read_bytes())

    (backup / "git_status_before.txt").write_text(
        run_git(project_root, "status", "--short").stdout,
        encoding="utf-8",
    )
    (backup / "rsa4_transition_plan.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return backup


def apply_transition(project_root: Path, report: dict[str, Any]) -> dict[str, Any]:
    if not report.get("apply_allowed"):
        raise RuntimeError("Apply blocked by repository drift.")

    backup = make_backup(project_root, report)
    gitignore = project_root / ".gitignore"
    before_hash = sha256_file(gitignore)
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    gitignore.write_text(update_gitignore_content(existing), encoding="utf-8", newline="\n")

    rsa_sources = report["preflight"]["rsa_sources_to_track"]
    if rsa_sources:
        run_git(project_root, "add", "--", *rsa_sources)

    untrack = report["planned_changes"]["tracked_paths_to_untrack_cached_only"]
    if untrack:
        run_git(project_root, "rm", "-r", "--cached", "--ignore-unmatch", "--", *untrack)

    transient = report["planned_changes"]["transient_deletions_to_accept"]
    for path in transient:
        if path in set(run_git(project_root, "ls-files").stdout.splitlines()):
            run_git(project_root, "rm", "--cached", "--ignore-unmatch", "--", path)

    run_git(project_root, "add", "--", ".gitignore")

    after = {
        "status": "APPLIED_NOT_COMMITTED",
        "transition_version": "RSA-4.2",
        "backup_root": str(backup),
        "gitignore_sha256_before": before_hash,
        "gitignore_sha256_after": sha256_file(gitignore),
        "working_tree_files_deleted": False,
        "commit_performed": False,
        "push_performed": False,
        "git_status_after": run_git(project_root, "status", "--short").stdout.splitlines(),
        "manual_review_still_required": report["planned_changes"]["release_snapshot_manual_review"],
        "next_action": "Inspect staged changes and run RSA-5 certification before commit.",
    }

    output = project_root / "runtime/control/runtime_state_architecture/rsa4"
    output.mkdir(parents=True, exist_ok=True)
    (output / "guarded_git_transition_result.json").write_text(
        json.dumps(after, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return after


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or apply RSA-4 guarded Git transition.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not (project_root / ".git").exists():
        raise RuntimeError(f"Not a Git repository: {project_root}")

    report = build_transition(project_root)
    outputs = write_preview(project_root, report)
    report["outputs"] = [str(path) for path in outputs]
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.apply:
        result = apply_transition(project_root, report)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    return 0 if report["apply_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
