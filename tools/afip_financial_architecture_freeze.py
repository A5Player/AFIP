"""AFIP Financial Architecture Freeze tool.

Self-contained. It does not import the AFIP package, so it can be run safely:

    python tools/afip_financial_architecture_freeze.py
    python tools/afip_financial_architecture_freeze.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "backup", "venv", ".venv"}
SKIP_WRITE_DIRS = {"backup"}

REPLACEMENTS = {
    "TradingCostProfile": "TradingCostProfile",
    "TradingCostIntelligence": "TradingCostIntelligence",
    "trading_cost_intelligence": "trading_cost_intelligence",
    "trading_cost_intelligence": "trading_cost_intelligence",
    "Trading Cost Intelligence": "Trading Cost Intelligence",
    "Trading Cost Intelligence": "Trading Cost Intelligence",
    "trading_cost_intelligence_block": "trading_cost_block",
    "SafetyValidation": "SafetyValidation",
    "safety_validation": "safety_validation",
    "DecisionIntelligence": "DecisionIntelligence",
    "decision_intelligence": "decision_intelligence",
    "TrendIntelligence": "TrendIntelligence",
    "trend_intelligence": "trend_intelligence",
    "PrecisionEntryIntelligence": "PrecisionEntryIntelligence",
    "precision_entry_intelligence": "precision_entry_intelligence",
    "MarketScannerIntelligence": "MarketScannerIntelligence",
    "market_scanner_intelligence": "market_scanner_intelligence",
    "ValidationIntelligence": "ValidationIntelligence",
    "validation_intelligence": "validation_intelligence",
    "EmergencyRiskHalt": "EmergencyRiskHalt",
    "emergency risk halt": "emergency risk halt",
    "MarketParticipation": "MarketParticipation",
    "market participation": "market participation",
    "RiskControl": "RiskControl",
    "risk control": "risk control",
    "MarketSession": "MarketSession",
    "market session": "market session",
    "ExecutionTool": "ExecutionTool",
    "execution tool": "execution tool",
    "TradingObjective": "TradingObjective",
    "trading objective": "trading objective",
    "Execution": "Execution",
    "execution": "execution",
    "PriceObjective": "PriceObjective",
    "price objective": "price objective",
}

OBSOLETE_PATHS = [
    "aif.py",
    "aif",
    "afip/intelligence/trading_cost_intelligence.py",
    "afip/security/safety_validation.py",
    "docs/PRODUCTION_SPRINT10_TRADING_COST_GUARD_INTELLIGENCE.md",
]

@dataclass(frozen=True)
class Change:
    path: Path
    action: str


def project_root_from_tool() -> Path:
    return Path(__file__).resolve().parents[1]


def iter_text_files(project_root: Path):
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(project_root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def planned_text_changes(project_root: Path) -> list[Change]:
    changes: list[Change] = []
    for path in iter_text_files(project_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = text
        for old, new in REPLACEMENTS.items():
            updated = updated.replace(old, new)
        if updated != text:
            changes.append(Change(path, "update-text"))
    return changes


def planned_removals(project_root: Path) -> list[Change]:
    changes: list[Change] = []
    for relative in OBSOLETE_PATHS:
        path = project_root / relative
        if path.exists():
            changes.append(Change(path, "remove-obsolete"))
    return changes


def create_price objectiveed_backup(project_root: Path, changes: list[Change]) -> Path:
    backup_dir = project_root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"afip_financial_architecture_freeze_backup_{stamp}.zip"

    seen: set[Path] = set()
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for change in changes:
            path = change.path
            if not path.exists() or path in seen:
                continue
            seen.add(path)
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file() and not any(part in SKIP_DIRS for part in child.relative_to(project_root).parts):
                        if child not in seen:
                            seen.add(child)
                            archive.write(child, child.relative_to(project_root))
            else:
                archive.write(path, path.relative_to(project_root))
    return backup_path


def apply_text_changes(changes: list[Change]) -> None:
    for change in changes:
        path = change.path
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = text
        for old, new in REPLACEMENTS.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def apply_removals(changes: list[Change]) -> None:
    for change in changes:
        path = change.path
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP Financial Architecture Freeze")
    parser.add_argument("--apply", action="store_true", help="apply cleanup after backup")
    args = parser.parse_args()

    project_root = project_root_from_tool()
    text_changes = planned_text_changes(project_root)
    removal_changes = planned_removals(project_root)
    planned = text_changes + removal_changes

    print("AFIP Financial Architecture Freeze")
    print(f"Project root: {project_root}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()

    if not planned:
        print("No naming cleanup required.")
        print("Recommended validation:")
        print("  python tools/validate_financial_naming.py")
        print("  python afip.py simulate")
        print("  python afip.py mt5-check")
        return 0

    print("Planned changes:")
    for change in planned:
        print(f"  - {change.action}: {change.path.relative_to(project_root)}")

    if not args.apply:
        print()
        print("Dry-run complete. To apply:")
        print("  python tools/afip_financial_architecture_freeze.py --apply")
        return 0

    backup_path = create_price objectiveed_backup(project_root, planned)
    apply_text_changes(text_changes)
    apply_removals(removal_changes)

    print()
    print(f"Backup created: {backup_path.relative_to(project_root)}")
    print("Financial naming cleanup applied.")
    print("Recommended validation:")
    print("  python tools/validate_financial_naming.py")
    print("  python afip.py simulate")
    print("  python afip.py mt5-check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
