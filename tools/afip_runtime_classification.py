import argparse
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("TEMPORARY_PROCESS_STATE", (".pid", "/pytest_temp/", "/pytest_tmp/", "stop_research_runtime.flag")),
    ("DASHBOARD_CACHE", ("runtime/dashboard/",)),
    ("CERTIFICATION_EVIDENCE", ("runtime/certification/", "certification.json", "execution_chain_certification.json")),
    ("PRODUCTION_EVIDENCE", ("/production_activation/", "activation_ledger.jsonl", "/plans/plan-")),
    ("RESEARCH_DATA", ("runtime/research/", "research_", "replay_performance.json", "timeline.jsonl")),
    ("RUNTIME_STATE", ("runtime/control/", "runtime/execution/", "runtime/profiles/", "runtime_truth.json", "_status.json", "status.json", "mt5_health.json")),
    ("PERSISTENT_KNOWLEDGE", ("knowledge", "dictionary", "catalog", "registry", "dataset", "ledger")),
)

POLICY_HINTS = {
    "TEMPORARY_PROCESS_STATE": "IGNORE",
    "DASHBOARD_CACHE": "GENERATED",
    "CERTIFICATION_EVIDENCE": "REVIEW_FOR_SNAPSHOT",
    "PRODUCTION_EVIDENCE": "REVIEW_FOR_ARCHIVE",
    "RESEARCH_DATA": "PERSIST_OUTSIDE_SOURCE_CONTROL",
    "RUNTIME_STATE": "GENERATED_RUNTIME_STATE",
    "PERSISTENT_KNOWLEDGE": "VERSION_OR_ARCHIVE_BY_CONTRACT",
    "UNCLASSIFIED": "MANUAL_REVIEW",
}


class Entry:
    """Python 3.14-safe immutable-style report entry.

    A plain class is used deliberately because RSA-1 tests load this module
    through importlib without first registering it in sys.modules. Python 3.14
    dataclasses may inspect sys.modules while resolving string annotations,
    which caused the original RSA-1 import failure.
    """

    __slots__ = ("path", "git_state", "category", "policy_hint", "size_bytes", "exists")

    def __init__(
        self,
        path: str,
        git_state: str,
        category: str,
        policy_hint: str,
        size_bytes: int,
        exists: bool,
    ) -> None:
        self.path = path
        self.git_state = git_state
        self.category = category
        self.policy_hint = policy_hint
        self.size_bytes = size_bytes
        self.exists = exists

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "git_state": self.git_state,
            "category": self.category,
            "policy_hint": self.policy_hint,
            "size_bytes": self.size_bytes,
            "exists": self.exists,
        }


def run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout


def parse_status(root: Path) -> list[tuple[str, str]]:
    output = run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    parts = output.split("\0")
    results: list[tuple[str, str]] = []
    i = 0
    while i < len(parts):
        item = parts[i]
        if not item:
            i += 1
            continue
        code = item[:2]
        path = item[3:]
        if code[0] in {"R", "C"} and i + 1 < len(parts):
            path = parts[i + 1]
            i += 1
        results.append((code, path.replace("\\", "/")))
        i += 1
    return results


def classify(path: str) -> str:
    normalized = "/" + path.lower().replace("\\", "/")
    for category, needles in CATEGORY_RULES:
        if any(needle in normalized for needle in needles):
            return category
    return "UNCLASSIFIED"


def git_state(code: str) -> str:
    if code == "??":
        return "UNTRACKED"
    if "D" in code:
        return "TRACKED_DELETED"
    if "M" in code:
        return "TRACKED_MODIFIED"
    if "A" in code:
        return "TRACKED_ADDED"
    if "R" in code:
        return "TRACKED_RENAMED"
    return f"TRACKED_{code.strip() or 'UNKNOWN'}"


def build_report(root: Path) -> dict:
    entries: list[Entry] = []
    for code, relative in parse_status(root):
        target = root / relative
        category = classify(relative)
        entries.append(
            Entry(
                path=relative,
                git_state=git_state(code),
                category=category,
                policy_hint=POLICY_HINTS[category],
                size_bytes=target.stat().st_size if target.is_file() else 0,
                exists=target.exists(),
            )
        )

    by_category: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        by_category[entry.category].append(entry.path)

    category_counts = Counter(entry.category for entry in entries)
    state_counts = Counter(entry.git_state for entry in entries)
    review_categories = [
        category
        for category in ("CERTIFICATION_EVIDENCE", "PRODUCTION_EVIDENCE", "PERSISTENT_KNOWLEDGE", "UNCLASSIFIED")
        if category_counts.get(category)
    ]

    return {
        "status": "REVIEW_REQUIRED" if review_categories else "CLASSIFIED",
        "reason": "classification_complete_no_mutation_performed",
        "project_root": str(root),
        "authority": {
            "moves_files": False,
            "deletes_files": False,
            "restores_files": False,
            "untracks_files": False,
            "changes_gitignore": False,
        },
        "counts": {
            "total_changed_or_untracked": len(entries),
            "by_category": dict(sorted(category_counts.items())),
            "by_git_state": dict(sorted(state_counts.items())),
        },
        "review_categories": review_categories,
        "classification": {key: sorted(value) for key, value in sorted(by_category.items())},
        "entries": [entry.to_dict() for entry in sorted(entries, key=lambda e: e.path.lower())],
        "next_action": "Use this report as the input contract for RSA-2 Runtime Persistence Policy.",
    }


def write_markdown(report: dict, output: Path) -> None:
    lines = [
        "# AFIP Runtime Classification Report",
        "",
        f"Status: **{report['status']}**",
        "",
        "This report is advisory only. No file was moved, deleted, restored, untracked, or ignored.",
        "",
        "## Category Summary",
        "",
        "| Category | Count | Suggested RSA-2 policy |",
        "|---|---:|---|",
    ]
    for category, count in report["counts"]["by_category"].items():
        lines.append(f"| {category} | {count} | {POLICY_HINTS[category]} |")
    lines.extend(["", "## Files by Category", ""])
    for category, paths in report["classification"].items():
        lines.append(f"### {category}")
        lines.extend(f"- `{path}`" for path in paths)
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify AFIP runtime and repository state without mutation.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-dir", default="runtime/control/runtime_state_architecture/rsa1")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not (root / ".git").exists():
        raise SystemExit(f"Not a Git repository: {root}")

    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(root)
    json_path = output_dir / "runtime_classification.json"
    md_path = output_dir / "runtime_classification.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    report["outputs"] = [str(json_path), str(md_path)]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
