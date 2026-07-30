from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

POLICY_VERSION = "RSA-2.0"

CATEGORY_POLICY: dict[str, dict[str, Any]] = {
    "DASHBOARD_CACHE": {
        "persistence": "REBUILDABLE",
        "git_policy": "IGNORE_GENERATED",
        "retention": "LATEST_ONLY",
        "backup_required": False,
        "archive_required": False,
        "reason": "Rendered dashboard outputs are reproducible from source and runtime truth.",
    },
    "RUNTIME_STATE": {
        "persistence": "EPHEMERAL_RUNTIME",
        "git_policy": "IGNORE_GENERATED",
        "retention": "LATEST_ONLY",
        "backup_required": False,
        "archive_required": False,
        "reason": "Operational state changes continuously and must not define source truth.",
    },
    "TEMPORARY_PROCESS_STATE": {
        "persistence": "TEMPORARY",
        "git_policy": "IGNORE_ALWAYS",
        "retention": "DELETE_WHEN_STALE",
        "backup_required": False,
        "archive_required": False,
        "reason": "PID, flag and transient process files are lifecycle artifacts.",
    },
    "RESEARCH_DATA": {
        "persistence": "PERSISTENT_DATA",
        "git_policy": "OUTSIDE_SOURCE_CONTROL",
        "retention": "APPEND_OR_VERSIONED_DATASET",
        "backup_required": True,
        "archive_required": True,
        "reason": "Research data is a durable AFIP asset and must be retained independently from source control.",
    },
    "PRODUCTION_EVIDENCE": {
        "persistence": "IMMUTABLE_EVIDENCE",
        "git_policy": "ARCHIVE_OUTSIDE_SOURCE_CONTROL",
        "retention": "POLICY_CONTROLLED_ARCHIVE",
        "backup_required": True,
        "archive_required": True,
        "reason": "Production plans and ledgers are operational evidence, not source files.",
    },
    "CERTIFICATION_EVIDENCE": {
        "persistence": "CONTROLLED_SNAPSHOT",
        "git_policy": "VERSIONED_RELEASE_SNAPSHOT_OR_ARCHIVE",
        "retention": "KEEP_CERTIFIED_SNAPSHOTS",
        "backup_required": True,
        "archive_required": True,
        "reason": "Certification evidence may be versioned only as an explicit release snapshot.",
    },
    "PERSISTENT_KNOWLEDGE": {
        "persistence": "VERSIONED_KNOWLEDGE",
        "git_policy": "TRACK_SOURCE_CONTROL",
        "retention": "PERMANENT",
        "backup_required": True,
        "archive_required": True,
        "reason": "Curated knowledge and contracts belong to the repository source of truth.",
    },
    "UNCLASSIFIED": {
        "persistence": "MANUAL_REVIEW",
        "git_policy": "NO_AUTOMATIC_ACTION",
        "retention": "UNTIL_CLASSIFIED",
        "backup_required": True,
        "archive_required": False,
        "reason": "Unknown files require explicit classification before any mutation.",
    },
}

AUTHORITY = {
    "moves_files": False,
    "deletes_files": False,
    "restores_files": False,
    "untracks_files": False,
    "changes_gitignore": False,
    "archives_files": False,
    "writes_policy_reports_only": True,
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("RSA-1 report must be a JSON object")
    return data


def build_policy(report: dict[str, Any], project_root: Path) -> dict[str, Any]:
    entries = report.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("RSA-1 report entries must be a list")

    decisions: list[dict[str, Any]] = []
    by_policy: dict[str, int] = {}
    unresolved: list[str] = []

    for raw in entries:
        if not isinstance(raw, dict):
            continue
        category = str(raw.get("category", "UNCLASSIFIED"))
        category_policy = CATEGORY_POLICY.get(category, CATEGORY_POLICY["UNCLASSIFIED"])
        decision = {
            "path": str(raw.get("path", "")),
            "git_state": str(raw.get("git_state", "UNKNOWN")),
            "category": category,
            "persistence": category_policy["persistence"],
            "git_policy": category_policy["git_policy"],
            "retention": category_policy["retention"],
            "backup_required": category_policy["backup_required"],
            "archive_required": category_policy["archive_required"],
            "automatic_action_allowed": False,
            "reason": category_policy["reason"],
        }
        decisions.append(decision)
        key = str(category_policy["git_policy"])
        by_policy[key] = by_policy.get(key, 0) + 1
        if category == "UNCLASSIFIED":
            unresolved.append(decision["path"])

    status = "REVIEW_REQUIRED" if unresolved else "READY_FOR_RSA3_DESIGN"
    return {
        "status": status,
        "reason": "policy_matrix_complete_no_mutation_performed",
        "policy_version": POLICY_VERSION,
        "project_root": str(project_root),
        "source_report": str(project_root / "runtime/control/runtime_state_architecture/rsa1/runtime_classification.json"),
        "authority": AUTHORITY,
        "category_policy": CATEGORY_POLICY,
        "counts": {
            "total_decisions": len(decisions),
            "by_git_policy": dict(sorted(by_policy.items())),
            "manual_review_required": len(unresolved),
        },
        "manual_review": unresolved,
        "decisions": decisions,
        "rsa3_readiness": {
            "ready": not unresolved,
            "blockers": unresolved,
            "note": "RSA-3 may design directory/refactoring actions only after manual-review items are explicitly classified.",
        },
        "next_action": "Review manual-review items, then use this policy as the non-destructive design contract for RSA-3.",
    }


def render_markdown(policy: dict[str, Any]) -> str:
    lines = [
        "# AFIP Runtime State Architecture — RSA-2 Persistence Policy",
        "",
        f"Status: **{policy['status']}**",
        f"Policy version: `{policy['policy_version']}`",
        "",
        "## Authority",
        "",
        "RSA-2 writes reports only. It does not move, delete, restore, untrack, archive, or edit `.gitignore`.",
        "",
        "## Category Policy Matrix",
        "",
        "| Category | Persistence | Git Policy | Retention | Backup | Archive |",
        "|---|---|---|---|---:|---:|",
    ]
    for category, item in CATEGORY_POLICY.items():
        lines.append(
            f"| {category} | {item['persistence']} | {item['git_policy']} | {item['retention']} | "
            f"{'YES' if item['backup_required'] else 'NO'} | {'YES' if item['archive_required'] else 'NO'} |"
        )
    lines.extend(["", "## Summary", ""])
    for key, value in policy["counts"]["by_git_policy"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", f"Manual review required: **{policy['counts']['manual_review_required']}**", ""])
    if policy["manual_review"]:
        lines.extend(["## Manual Review", ""])
        lines.extend(f"- `{path}`" for path in policy["manual_review"])
        lines.append("")
    lines.extend([
        "## RSA-3 Gate",
        "",
        f"Ready: **{'YES' if policy['rsa3_readiness']['ready'] else 'NO'}**",
        "",
        policy["rsa3_readiness"]["note"],
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AFIP RSA-2 runtime persistence policy")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--input", default=None)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    input_path = Path(args.input).resolve() if args.input else project_root / "runtime/control/runtime_state_architecture/rsa1/runtime_classification.json"
    if not input_path.is_file():
        raise SystemExit(f"RSA-1 classification report not found: {input_path}")

    report = load_json(input_path)
    policy = build_policy(report, project_root)
    output_dir = project_root / "runtime/control/runtime_state_architecture/rsa2"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "runtime_persistence_policy.json"
    md_path = output_dir / "runtime_persistence_policy.md"
    json_path.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(policy), encoding="utf-8")
    print(json.dumps(policy, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
