from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESOLUTIONS: dict[str, dict[str, Any]] = {
    "AFIP_V1_FINAL_REVISION_3_REPLAY_THROUGHPUT.zip": {
        "resolved_category": "PRODUCTION_EVIDENCE",
        "persistence": "IMMUTABLE_EVIDENCE",
        "git_policy": "ARCHIVE_OUTSIDE_SOURCE_CONTROL",
        "retention": "POLICY_CONTROLLED_ARCHIVE",
        "backup_required": True,
        "archive_required": True,
        "recommended_action": "VERIFY_EXTERNAL_ARCHIVE_THEN_ACCEPT_TRACKED_DELETION",
        "automatic_action_allowed": False,
        "reason": "Legacy replay-throughput delivery ZIP is a release/operational artifact, not repository source.",
    },
    "capital_binding_verification.json": {
        "resolved_category": "CERTIFICATION_EVIDENCE",
        "persistence": "CONTROLLED_SNAPSHOT",
        "git_policy": "VERSIONED_RELEASE_SNAPSHOT_OR_ARCHIVE",
        "retention": "KEEP_CERTIFIED_SNAPSHOTS",
        "backup_required": True,
        "archive_required": True,
        "recommended_action": "REVIEW_FOR_CERTIFIED_SNAPSHOT_OR_EXTERNAL_ARCHIVE",
        "automatic_action_allowed": False,
        "reason": "Capital binding verification is generated certification evidence and must not become implicit source truth.",
    },
    "docs/AFIP_RUNTIME_STATE_ARCHITECTURE_RSA1.md": {
        "resolved_category": "PERSISTENT_KNOWLEDGE",
        "persistence": "VERSIONED_KNOWLEDGE",
        "git_policy": "TRACK_SOURCE_CONTROL",
        "retention": "PERMANENT",
        "backup_required": True,
        "archive_required": True,
        "recommended_action": "COMMIT_WITH_RSA_SOURCE_FILES",
        "automatic_action_allowed": False,
        "reason": "RSA-1 architecture documentation is curated repository knowledge.",
    },
    "tests/test_runtime_state_architecture_rsa1.py": {
        "resolved_category": "PERSISTENT_KNOWLEDGE",
        "persistence": "VERSIONED_KNOWLEDGE",
        "git_policy": "TRACK_SOURCE_CONTROL",
        "retention": "PERMANENT",
        "backup_required": True,
        "archive_required": True,
        "recommended_action": "COMMIT_WITH_RSA_SOURCE_FILES",
        "automatic_action_allowed": False,
        "reason": "RSA-1 regression tests are source-controlled verification assets.",
    },
    "tools/afip_runtime_classification.py": {
        "resolved_category": "PERSISTENT_KNOWLEDGE",
        "persistence": "VERSIONED_KNOWLEDGE",
        "git_policy": "TRACK_SOURCE_CONTROL",
        "retention": "PERMANENT",
        "backup_required": True,
        "archive_required": True,
        "recommended_action": "COMMIT_WITH_RSA_SOURCE_FILES",
        "automatic_action_allowed": False,
        "reason": "RSA-1 classification tool is executable repository source.",
    },
}

AUTHORITY = {
    "moves_files": False,
    "deletes_files": False,
    "restores_files": False,
    "untracks_files": False,
    "changes_gitignore": False,
    "archives_files": False,
    "stages_git_changes": False,
    "commits_git_changes": False,
    "writes_resolution_reports_only": True,
}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def build_resolution(project_root: Path) -> dict[str, Any]:
    source = project_root / "runtime/control/runtime_state_architecture/rsa2/runtime_persistence_policy.json"
    if not source.exists():
        raise FileNotFoundError(
            "RSA-2 policy report not found. Run RSA-2 before RSA-2.1: "
            f"{source}"
        )

    rsa2 = _read_json(source)
    blockers = list(rsa2.get("rsa3_readiness", {}).get("blockers", []))
    blocker_set = set(blockers)
    known_set = set(RESOLUTIONS)

    unresolved = sorted(blocker_set - known_set)
    stale_resolutions = sorted(known_set - blocker_set)

    decisions = []
    for path in blockers:
        resolution = RESOLUTIONS.get(path)
        if resolution is None:
            decisions.append({
                "path": path,
                "resolution_status": "UNRESOLVED",
                "automatic_action_allowed": False,
            })
            continue
        item = {"path": path, "resolution_status": "RESOLVED"}
        item.update(resolution)
        decisions.append(item)

    ready = not unresolved
    report = {
        "status": "PASS" if ready else "REVIEW_REQUIRED",
        "reason": (
            "manual_review_items_explicitly_classified_no_mutation_performed"
            if ready else
            "unknown_manual_review_items_remain"
        ),
        "resolution_version": "RSA-2.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "source_report": str(source),
        "authority": AUTHORITY,
        "counts": {
            "source_blockers": len(blockers),
            "resolved": len(blockers) - len(unresolved),
            "unresolved": len(unresolved),
            "stale_resolution_rules": len(stale_resolutions),
        },
        "decisions": decisions,
        "unresolved": unresolved,
        "stale_resolution_rules": stale_resolutions,
        "rsa3_readiness": {
            "ready": ready,
            "blockers": unresolved,
            "note": (
                "RSA-3 may design non-destructive tracking/refactoring actions."
                if ready else
                "RSA-3 remains blocked until all manual-review items are explicitly classified."
            ),
        },
        "next_action": (
            "Use this resolution contract with RSA-2 policy as input for RSA-3."
            if ready else
            "Add explicit reviewed resolutions for remaining blockers."
        ),
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AFIP Runtime State Architecture RSA-2.1",
        "",
        "## Manual Review Resolution",
        "",
        f"- Status: **{report['status']}**",
        f"- RSA-3 ready: **{report['rsa3_readiness']['ready']}**",
        f"- Source blockers: **{report['counts']['source_blockers']}**",
        f"- Resolved: **{report['counts']['resolved']}**",
        f"- Unresolved: **{report['counts']['unresolved']}**",
        "",
        "## Safety Authority",
        "",
    ]
    for key, value in report["authority"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines += ["", "## Resolutions", ""]
    for item in report["decisions"]:
        lines += [
            f"### `{item['path']}`",
            "",
            f"- Resolution: `{item['resolution_status']}`",
        ]
        if item["resolution_status"] == "RESOLVED":
            lines += [
                f"- Category: `{item['resolved_category']}`",
                f"- Git policy: `{item['git_policy']}`",
                f"- Recommended action: `{item['recommended_action']}`",
                f"- Automatic action allowed: `{str(item['automatic_action_allowed']).lower()}`",
                f"- Reason: {item['reason']}",
            ]
        lines.append("")
    return "\n".join(lines)


def write_reports(project_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    output_dir = project_root / "runtime/control/runtime_state_architecture/rsa2_1"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "manual_review_resolution.json"
    md_path = output_dir / "manual_review_resolution.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve RSA-2 manual-review classifications without mutation.")
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    report = build_resolution(project_root)
    outputs = write_reports(project_root, report)
    report["outputs"] = [str(path) for path in outputs]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["rsa3_readiness"]["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
