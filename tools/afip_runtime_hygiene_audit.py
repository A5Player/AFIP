from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

SAFE_UNTRACKED_PATTERNS = (
    "patch_backups/",
    "runtime/**/*.pid",
    "runtime/pytest_temp/",
    "runtime/pytest_tmp/",
    "status_after_start.txt",
)

RUNTIME_PREFIXES = (
    "runtime/",
    "patch_backups/",
)


def _git(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project_root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _is_runtime_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(RUNTIME_PREFIXES)


def build_report(project_root: Path) -> dict[str, object]:
    tracked_modified = _lines(_git(project_root, "diff", "--name-only"))
    tracked_deleted = _lines(_git(project_root, "diff", "--name-only", "--diff-filter=D"))
    untracked = _lines(_git(project_root, "ls-files", "--others", "--exclude-standard"))

    runtime_tracked_modified = [p for p in tracked_modified if _is_runtime_path(p)]
    runtime_untracked = [p for p in untracked if _is_runtime_path(p)]
    non_runtime_modified = [p for p in tracked_modified if not _is_runtime_path(p)]
    non_runtime_untracked = [p for p in untracked if not _is_runtime_path(p)]

    status = "PASS"
    reasons: list[str] = []
    if non_runtime_modified:
        status = "REVIEW_REQUIRED"
        reasons.append("non_runtime_tracked_changes_present")
    if non_runtime_untracked:
        status = "REVIEW_REQUIRED"
        reasons.append("non_runtime_untracked_files_present")
    if tracked_deleted:
        status = "REVIEW_REQUIRED"
        reasons.append("tracked_deletions_present")

    return {
        "status": status,
        "reasons": reasons,
        "project_root": str(project_root),
        "policy": {
            "destructive_cleanup": False,
            "automatic_untrack": False,
            "automatic_restore": False,
            "automatic_delete": False,
            "safe_ignore_patterns": list(SAFE_UNTRACKED_PATTERNS),
        },
        "counts": {
            "tracked_modified": len(tracked_modified),
            "tracked_deleted": len(tracked_deleted),
            "untracked": len(untracked),
            "runtime_tracked_modified": len(runtime_tracked_modified),
            "runtime_untracked": len(runtime_untracked),
            "non_runtime_modified": len(non_runtime_modified),
            "non_runtime_untracked": len(non_runtime_untracked),
        },
        "tracked_deleted": tracked_deleted,
        "runtime_tracked_modified": runtime_tracked_modified,
        "runtime_untracked": runtime_untracked,
        "non_runtime_modified": non_runtime_modified,
        "non_runtime_untracked": non_runtime_untracked,
        "next_action": (
            "Review tracked runtime outputs separately; .gitignore does not affect files already tracked."
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    project_root = Path(args[0] if args else ".").resolve()
    if not (project_root / ".git").exists():
        print(json.dumps({"status": "FAIL", "reason": "git_repository_not_found"}, indent=2))
        return 2

    report = build_report(project_root)
    output = project_root / "runtime" / "control" / "repository_hygiene" / "runtime_hygiene_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**report, "output": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
