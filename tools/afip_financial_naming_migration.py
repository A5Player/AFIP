"""AFIP official financial naming migration tool."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from afip.standards.financial_naming_standard import (
    find_obsolete_terms,
    iter_project_text_files,
    replace_obsolete_terms,
)


def project_root_from_tool() -> Path:
    return Path(__file__).resolve().parents[1]


def backup_project(project_root: Path) -> Path:
    backup_dir = project_root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_base = backup_dir / f"afip_financial_naming_backup_{stamp}"
    return Path(shutil.make_archive(str(backup_base), "zip", project_root))


def scan(project_root: Path):
    findings = []
    for path in iter_project_text_files(project_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found = find_obsolete_terms(text)
        if found:
            findings.append((path, found))
    return findings


def apply(project_root: Path) -> list[Path]:
    changed: list[Path] = []
    for path in iter_project_text_files(project_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated, applied = replace_obsolete_terms(text)
        if applied and updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP Financial Naming Migration")
    parser.add_argument("--apply", action="store_true", help="apply replacements after backup")
    args = parser.parse_args()

    project_root = project_root_from_tool()
    mode = "APPLY" if args.apply else "DRY-RUN"

    print("AFIP Financial Naming Migration")
    print(f"Project root: {project_root}")
    print(f"Mode: {mode}")
    print()

    findings = scan(project_root)
    if not findings:
        print("No obsolete military-style naming found.")
        return 0

    print("Obsolete terms found:")
    for path, rules in findings:
        rel = path.relative_to(project_root)
        terms = ", ".join(sorted({rule.obsolete for rule in rules}))
        print(f"  - {rel}: {terms}")

    if not args.apply:
        print()
        print("Dry-run complete. To apply official financial naming, run:")
        print("  python tools/afip_financial_naming_migration.py --apply")
        return 0

    backup_path = backup_project(project_root)
    changed = apply(project_root)
    print()
    print(f"Backup created: {backup_path.relative_to(project_root)}")
    print("Updated files:")
    for path in changed:
        print(f"  - {path.relative_to(project_root)}")
    print()
    print("Recommended validation:")
    print("  python afip.py simulate")
    print("  python afip.py mt5-check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
