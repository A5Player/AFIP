from __future__ import annotations

import ast
import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
AFIP_ROOT = ROOT / "afip"
OUTPUT_ROOT = ROOT / "runtime" / "architecture_inventory"

EXCLUDED_PARTS = {
    ".git", ".venv", "__pycache__", ".pytest_cache",
    "runtime", "build", "dist",
}

AUTHORITY_PATTERNS = {
    "ORDER_SEND": re.compile(r"\b(?:mt5\.)?order_send\s*\(", re.I),
    "ORDER_CHECK": re.compile(r"\b(?:mt5\.)?order_check\s*\(", re.I),
    "UNIT_ALLOCATION": re.compile(
        r"\b(?:allocated_units|maximum_units|max_units|capital_per_unit|unit_capacity)\b", re.I
    ),
    "POSITION_SIZING": re.compile(
        r"\b(?:position_siz|lot_size|base_lot|lot_per_unit|volume)\b", re.I
    ),
    "PROTECTION_PLAN": re.compile(
        r"\b(?:stop_loss|take_profit|sl_points|tp_points|atr|buffer|reward_risk)\b", re.I
    ),
    "RISK_APPROVAL": re.compile(
        r"\b(?:risk_approv|risk_gate|risk_budget|risk_limit)\b", re.I
    ),
    "MARKET_REGIME": re.compile(r"\b(?:market_regime|regime_class)\b", re.I),
    "SIGNAL": re.compile(r"\b(?:signal_engine|signal_decision|entry_signal)\b", re.I),
    "CONFIDENCE": re.compile(r"\b(?:confidence_score|confidence_gate|confidence)\b", re.I),
    "HOLDING": re.compile(r"\b(?:holding_plan|hold_reason|trailing_stop|breakeven)\b", re.I),
    "EXIT": re.compile(r"\b(?:exit_plan|exit_signal|close_position|position_close)\b", re.I),
    "RESEARCH": re.compile(r"\b(?:research|replay|simulation|backtest|learning)\b", re.I),
}

LEGACY_PATTERNS = {
    "LEGACY_TP_500": re.compile(
        r"\b(?:tp_points|take_profit_points|default_tp_points)\s*[:=]\s*500(?:\.0)?\b", re.I
    ),
    "LEGACY_SL_3000": re.compile(
        r"\b(?:sl_points|stop_loss_points|default_sl_points)\s*[:=]\s*3000(?:\.0)?\b", re.I
    ),
    "FORCED_THREE_UNITS": re.compile(
        r"\b(?:allocated_units|units_to_send|order_units)\s*[:=]\s*3\b", re.I
    ),
    "MAXIMUM_AS_ALLOCATION": re.compile(
        r"\ballocated_units\s*[:=]\s*(?:int\()?\s*maximum_units\b", re.I
    ),
}

RESPONSIBILITY_HINTS = {
    "market_regime": "MARKET_REGIME",
    "signal": "SIGNAL",
    "confidence": "CONFIDENCE",
    "risk": "RISK_APPROVAL",
    "capital_allocation": "UNIT_ALLOCATION",
    "unit_allocation": "UNIT_ALLOCATION",
    "position_siz": "POSITION_SIZING",
    "protection": "PROTECTION_PLAN",
    "sl_tp": "PROTECTION_PLAN",
    "execution": "EXECUTION",
    "gateway": "EXECUTION",
    "holding": "HOLDING",
    "exit": "EXIT",
    "research": "RESEARCH",
    "replay": "RESEARCH",
    "learning": "RESEARCH",
    "dashboard": "PRESENTATION",
    "collector": "DATA_COLLECTION",
    "repository": "DATA_STORAGE",
}


@dataclass
class ComponentRecord:
    component_id: str
    module_path: str
    package_name: str
    module_name: str
    responsibility: str
    classes: list[str]
    functions: list[str]
    imports: list[str]
    authorities: list[str]
    legacy_findings: list[str]
    executable_entry_points: list[str]
    status: str
    duplicate_group: str
    lines: int


def python_files() -> Iterable[Path]:
    for path in AFIP_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        yield path


def infer_responsibility(path: Path, text: str) -> str:
    haystack = f"{path.as_posix()} {text[:3000]}".lower()
    scores: dict[str, int] = defaultdict(int)
    for hint, responsibility in RESPONSIBILITY_HINTS.items():
        scores[responsibility] += haystack.count(hint)
    if not scores:
        return "UNKNOWN"
    responsibility, score = max(scores.items(), key=lambda item: item[1])
    return responsibility if score > 0 else "UNKNOWN"


def parse_ast(text: str):
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def ast_details(tree) -> tuple[list[str], list[str], list[str], list[str]]:
    classes: list[str] = []
    functions: list[str] = []
    imports: list[str] = []
    entries: list[str] = []
    if tree is None:
        return classes, functions, imports, entries

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            if node.name in {"main", "run", "start", "execute", "process"}:
                entries.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
    return sorted(set(classes)), sorted(set(functions)), sorted(set(imports)), sorted(set(entries))


def main() -> int:
    if not AFIP_ROOT.exists():
        print(f"FAIL: AFIP package not found: {AFIP_ROOT}")
        return 1

    records: list[ComponentRecord] = []
    authority_index: dict[str, list[str]] = defaultdict(list)
    legacy_index: dict[str, list[dict]] = defaultdict(list)

    for path in sorted(python_files()):
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = parse_ast(text)
        classes, functions, imports, entries = ast_details(tree)

        authorities = [
            name for name, pattern in AUTHORITY_PATTERNS.items()
            if pattern.search(text)
        ]
        legacy_findings = []
        for name, pattern in LEGACY_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                legacy_findings.append(f"{name}@L{line}")
                legacy_index[name].append({
                    "module_path": relative.as_posix(),
                    "line": line,
                    "match": match.group(0),
                })

        responsibility = infer_responsibility(relative, text)
        status = "REVIEW_REQUIRED" if legacy_findings else "ACTIVE_UNVERIFIED"
        duplicate_group = responsibility if responsibility not in {"UNKNOWN", "PRESENTATION"} else ""

        component_id = relative.with_suffix("").as_posix().replace("/", ".")
        record = ComponentRecord(
            component_id=component_id,
            module_path=relative.as_posix(),
            package_name=relative.parts[1] if len(relative.parts) > 2 else "afip",
            module_name=path.stem,
            responsibility=responsibility,
            classes=classes,
            functions=functions,
            imports=imports,
            authorities=authorities,
            legacy_findings=legacy_findings,
            executable_entry_points=entries,
            status=status,
            duplicate_group=duplicate_group,
            lines=text.count("\n") + 1,
        )
        records.append(record)

        for authority in authorities:
            authority_index[authority].append(record.module_path)

    duplicate_groups = {
        group: sorted(record.module_path for record in records if record.duplicate_group == group)
        for group in sorted({r.duplicate_group for r in records if r.duplicate_group})
    }
    duplicate_candidates = {
        group: paths for group, paths in duplicate_groups.items() if len(paths) > 1
    }

    dangerous_authorities = {
        authority: paths
        for authority, paths in authority_index.items()
        if authority in {
            "ORDER_SEND", "ORDER_CHECK", "UNIT_ALLOCATION",
            "POSITION_SIZING", "PROTECTION_PLAN", "RISK_APPROVAL",
        }
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    inventory = {
        "schema_version": "1.0",
        "repository_root": str(ROOT),
        "component_count": len(records),
        "components": [asdict(record) for record in records],
    }
    (OUTPUT_ROOT / "components.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with (OUTPUT_ROOT / "components.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "component_id", "module_path", "responsibility", "status",
            "authorities", "legacy_findings", "classes", "functions", "lines",
        ])
        for record in records:
            writer.writerow([
                record.component_id,
                record.module_path,
                record.responsibility,
                record.status,
                "|".join(record.authorities),
                "|".join(record.legacy_findings),
                "|".join(record.classes),
                "|".join(record.functions),
                record.lines,
            ])

    report = {
        "status": "REVIEW_REQUIRED",
        "component_count": len(records),
        "duplicate_candidates": duplicate_candidates,
        "authority_index": dangerous_authorities,
        "legacy_findings": legacy_index,
        "certification_blockers": [],
    }

    order_send_paths = authority_index.get("ORDER_SEND", [])
    if len(order_send_paths) != 1:
        report["certification_blockers"].append({
            "rule": "SINGLE_ORDER_SEND_AUTHORITY",
            "expected": 1,
            "actual": len(order_send_paths),
            "paths": order_send_paths,
        })

    for authority in ("UNIT_ALLOCATION", "POSITION_SIZING", "PROTECTION_PLAN"):
        paths = authority_index.get(authority, [])
        if len(paths) > 1:
            report["certification_blockers"].append({
                "rule": f"SINGLE_{authority}_AUTHORITY",
                "expected": 1,
                "actual": len(paths),
                "paths": paths,
            })

    if legacy_index:
        report["certification_blockers"].append({
            "rule": "NO_LEGACY_EXECUTION_DEFAULTS",
            "findings": legacy_index,
        })

    (OUTPUT_ROOT / "architecture_review.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    markdown = [
        "# AFIP Architecture Inventory",
        "",
        f"- Components scanned: **{len(records)}**",
        f"- Duplicate responsibility groups: **{len(duplicate_candidates)}**",
        f"- Certification blockers: **{len(report['certification_blockers'])}**",
        "",
        "## Execution Authorities",
        "",
    ]
    for authority, paths in sorted(dangerous_authorities.items()):
        markdown.append(f"### {authority}")
        markdown.extend(f"- `{path}`" for path in sorted(paths))
        markdown.append("")

    markdown.extend(["## Duplicate Candidates", ""])
    for group, paths in sorted(duplicate_candidates.items()):
        markdown.append(f"### {group}")
        markdown.extend(f"- `{path}`" for path in paths)
        markdown.append("")

    markdown.extend(["## Legacy Findings", ""])
    if not legacy_index:
        markdown.append("- None detected by strict patterns.")
    else:
        for name, findings in sorted(legacy_index.items()):
            markdown.append(f"### {name}")
            for finding in findings:
                markdown.append(
                    f"- `{finding['module_path']}:{finding['line']}` — `{finding['match']}`"
                )
            markdown.append("")

    markdown.extend([
        "## Rule",
        "",
        "This tool does not delete or refactor source code. It creates the evidence "
        "required for Cleanup Pack 2, where each responsibility receives exactly "
        "one primary authority and all other modules are classified as adapter, "
        "observer, research-only, compatibility, or deprecated.",
    ])
    (OUTPUT_ROOT / "ARCHITECTURE_INVENTORY.md").write_text(
        "\n".join(markdown) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "status": report["status"],
        "component_count": len(records),
        "duplicate_groups": len(duplicate_candidates),
        "certification_blockers": len(report["certification_blockers"]),
        "output": str(OUTPUT_ROOT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
