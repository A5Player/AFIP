from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUTHORITY = {
    "moves_files": False,
    "deletes_files": False,
    "restores_files": False,
    "untracks_files": False,
    "changes_gitignore": False,
    "archives_files": False,
    "stages_git_changes": False,
    "commits_git_changes": False,
    "writes_plan_reports_only": True,
}

ACTION_MAP = {
    "TRACK_SOURCE_CONTROL": "TRACK_AS_SOURCE",
    "IGNORE_GENERATED": "PLAN_IGNORE_AND_UNTRACK_IF_ALREADY_TRACKED",
    "IGNORE_ALWAYS": "PLAN_IGNORE_AND_ACCEPT_TRANSIENT_DELETION",
    "OUTSIDE_SOURCE_CONTROL": "PLAN_EXTERNAL_PERSISTENCE_AND_UNTRACK",
    "ARCHIVE_OUTSIDE_SOURCE_CONTROL": "PLAN_ARCHIVE_VERIFY_AND_UNTRACK",
    "VERSIONED_RELEASE_SNAPSHOT_OR_ARCHIVE": "PLAN_RELEASE_SNAPSHOT_DECISION",
    "NO_AUTOMATIC_ACTION": "BLOCKED_MANUAL_REVIEW",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _resolution_lookup(resolution: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for item in resolution.get("decisions", []):
        path = item.get("path")
        if path and item.get("resolution_status") == "RESOLVED":
            result[path] = item
    return result


def build_plan(project_root: Path) -> dict[str, Any]:
    rsa2_path = project_root / "runtime/control/runtime_state_architecture/rsa2/runtime_persistence_policy.json"
    rsa2_1_path = project_root / "runtime/control/runtime_state_architecture/rsa2_1/manual_review_resolution.json"

    if not rsa2_path.exists():
        raise FileNotFoundError(f"RSA-2 report not found: {rsa2_path}")
    if not rsa2_1_path.exists():
        raise FileNotFoundError(f"RSA-2.1 report not found: {rsa2_1_path}")

    rsa2 = read_json(rsa2_path)
    rsa2_1 = read_json(rsa2_1_path)

    readiness = rsa2_1.get("rsa3_readiness", {})
    if readiness.get("ready") is not True:
        raise RuntimeError("RSA-2.1 has not cleared RSA-3 blockers.")

    resolutions = _resolution_lookup(rsa2_1)
    actions = []
    unresolved = []

    for decision in rsa2.get("decisions", []):
        path = decision["path"]
        effective = dict(decision)

        if decision.get("category") == "UNCLASSIFIED":
            resolved = resolutions.get(path)
            if not resolved:
                unresolved.append(path)
                continue
            effective.update({
                "category": resolved["resolved_category"],
                "persistence": resolved["persistence"],
                "git_policy": resolved["git_policy"],
                "retention": resolved["retention"],
                "backup_required": resolved["backup_required"],
                "archive_required": resolved["archive_required"],
                "reason": resolved["reason"],
            })

        git_policy = effective.get("git_policy", "NO_AUTOMATIC_ACTION")
        planned_action = ACTION_MAP.get(git_policy, "BLOCKED_UNKNOWN_POLICY")

        actions.append({
            "path": path,
            "git_state": effective.get("git_state"),
            "category": effective.get("category"),
            "git_policy": git_policy,
            "planned_action": planned_action,
            "backup_required": bool(effective.get("backup_required")),
            "archive_required": bool(effective.get("archive_required")),
            "automatic_action_allowed": False,
            "reason": effective.get("reason", ""),
        })

    groups: dict[str, list[str]] = {}
    for item in actions:
        groups.setdefault(item["planned_action"], []).append(item["path"])

    blockers = sorted(unresolved + [
        item["path"] for item in actions
        if item["planned_action"] in {"BLOCKED_MANUAL_REVIEW", "BLOCKED_UNKNOWN_POLICY"}
    ])

    ordered_steps = [
        {
            "step": 1,
            "name": "COMMIT_RSA_SOURCE",
            "description": "Track reviewed RSA documentation, tools and tests as repository source.",
            "requires_backup": False,
            "mutates_repository": True,
            "execution_mode": "MANUAL_AFTER_REVIEW",
        },
        {
            "step": 2,
            "name": "ESTABLISH_EXTERNAL_DATA_ROOT",
            "description": "Prepare an external persistence location for research data and production evidence.",
            "requires_backup": True,
            "mutates_repository": False,
            "execution_mode": "DESIGN_REQUIRED",
        },
        {
            "step": 3,
            "name": "VERIFY_ARCHIVES_AND_SNAPSHOTS",
            "description": "Verify production archives and certification snapshots before changing Git tracking.",
            "requires_backup": True,
            "mutates_repository": False,
            "execution_mode": "MANUAL_EVIDENCE_REVIEW",
        },
        {
            "step": 4,
            "name": "APPLY_IGNORE_POLICY",
            "description": "Add narrowly scoped generated-runtime ignore rules only after source/data separation is verified.",
            "requires_backup": True,
            "mutates_repository": True,
            "execution_mode": "FUTURE_RSA4",
        },
        {
            "step": 5,
            "name": "UNTRACK_GENERATED_FILES",
            "description": "Remove generated runtime files from Git index without deleting working-tree data.",
            "requires_backup": True,
            "mutates_repository": True,
            "execution_mode": "FUTURE_RSA4",
        },
        {
            "step": 6,
            "name": "CERTIFY_CLEAN_REPOSITORY",
            "description": "Run focused and full regression plus repository hygiene checks.",
            "requires_backup": False,
            "mutates_repository": False,
            "execution_mode": "FUTURE_RSA5",
        },
    ]

    report = {
        "status": "PASS" if not blockers else "REVIEW_REQUIRED",
        "reason": "safe_git_tracking_plan_complete_no_mutation_performed",
        "plan_version": "RSA-3.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "source_reports": [str(rsa2_path), str(rsa2_1_path)],
        "authority": AUTHORITY,
        "counts": {
            "total_actions": len(actions),
            "by_planned_action": {key: len(value) for key, value in sorted(groups.items())},
            "blockers": len(blockers),
        },
        "action_groups": {key: sorted(value) for key, value in sorted(groups.items())},
        "actions": actions,
        "ordered_execution_plan": ordered_steps,
        "blockers": blockers,
        "rsa4_readiness": {
            "ready": not blockers,
            "note": (
                "RSA-4 may implement a guarded, backup-first Git tracking transition."
                if not blockers else
                "RSA-4 remains blocked until every action has an approved policy."
            ),
        },
        "next_action": "Use this plan as the contract for RSA-4 guarded implementation.",
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AFIP Runtime State Architecture RSA-3",
        "",
        "## Safe Git Tracking & Runtime Separation Plan",
        "",
        f"- Status: **{report['status']}**",
        f"- RSA-4 ready: **{report['rsa4_readiness']['ready']}**",
        f"- Total actions: **{report['counts']['total_actions']}**",
        f"- Blockers: **{report['counts']['blockers']}**",
        "",
        "## Safety Authority",
        "",
    ]
    for key, value in report["authority"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")

    lines += ["", "## Action Groups", ""]
    for action, paths in report["action_groups"].items():
        lines.append(f"### {action} ({len(paths)})")
        lines.append("")
        for path in paths:
            lines.append(f"- `{path}`")
        lines.append("")

    lines += ["## Ordered Execution Plan", ""]
    for step in report["ordered_execution_plan"]:
        lines += [
            f"### Step {step['step']} — {step['name']}",
            "",
            step["description"],
            "",
            f"- Execution mode: `{step['execution_mode']}`",
            f"- Requires backup: `{str(step['requires_backup']).lower()}`",
            f"- Mutates repository: `{str(step['mutates_repository']).lower()}`",
            "",
        ]
    return "\n".join(lines)


def write_reports(project_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    output_dir = project_root / "runtime/control/runtime_state_architecture/rsa3"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "safe_git_tracking_plan.json"
    md_path = output_dir / "safe_git_tracking_plan.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build RSA-3 safe Git tracking plan without mutation.")
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    report = build_plan(project_root)
    outputs = write_reports(project_root, report)
    report["outputs"] = [str(path) for path in outputs]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
