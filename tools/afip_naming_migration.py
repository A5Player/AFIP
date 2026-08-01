"""
AFIP V1 naming migration utility.

Purpose:
    Remove obsolete pre-AFIP launcher paths after the official AFIP entry point
    has been installed and verified.

Safety:
    - Dry-run by default.
    - Creates a backup zip before destructive cleanup when --apply is used.
    - Keeps the official AFIP package and root afip.py launcher.
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class MigrationPriceObjective:
    path: Path
    reason: str


OBSOLETE_TARGETS = [
    MigrationPriceObjective(ROOT / "aif.py", "obsolete compatibility launcher replaced by root afip.py"),
    MigrationPriceObjective(ROOT / "aif", "obsolete compatibility package replaced by official afip package"),
]


def _existing_targets() -> list[MigrationPriceObjective]:
    return [target for target in OBSOLETE_TARGETS if target.path.exists()]


def _backup_targets(targets: Iterable[MigrationPriceObjective]) -> Path | None:
    targets = list(targets)
    if not targets:
        return None

    backup_dir = ROOT / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"afip_naming_migration_backup_{stamp}.zip"

    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for target in targets:
            if target.path.is_file():
                archive.write(target.path, target.path.relative_to(ROOT))
            elif target.path.is_dir():
                for child in target.path.rglob("*"):
                    if child.is_file():
                        archive.write(child, child.relative_to(ROOT))
    return backup_path


def _remove_target(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def run(apply: bool) -> int:
    targets = _existing_targets()

    print("AFIP Naming Migration")
    print(f"Project root: {ROOT}")
    print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
    print("")

    if not targets:
        print("No obsolete naming targets found. AFIP naming is already clean.")
        return 0

    print("Targets:")
    for target in targets:
        kind = "DIR " if target.path.is_dir() else "FILE"
        print(f"  - {kind}: {target.path.relative_to(ROOT)} | {target.reason}")

    if not apply:
        print("")
        print("Dry-run complete. To apply cleanup, run:")
        print("  python tools/afip_naming_migration.py --apply")
        return 0

    backup_path = _backup_targets(targets)
    if backup_path is not None:
        print("")
        print(f"Backup created: {backup_path.relative_to(ROOT)}")

    for target in targets:
        _remove_target(target.path)

    print("Cleanup complete. Official launcher remains: afip.py")
    print("Recommended validation:")
    print("  python afip.py simulate")
    print("  python afip.py mt5-check")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP V1 naming migration utility")
    parser.add_argument("--apply", action="store_true", help="remove obsolete naming targets after backup")
    args = parser.parse_args()
    return run(apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
