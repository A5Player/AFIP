from __future__ import annotations

import ast
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AFIP_ROOT = ROOT / "afip"
INVENTORY_ROOT = ROOT / "runtime" / "architecture_inventory"
OUTPUT_ROOT = ROOT / "runtime" / "architecture_cleanup_pack_2"

TARGET_RESPONSIBILITIES = {
    "ORDER_SEND",
    "ORDER_CHECK",
    "UNIT_ALLOCATION",
    "POSITION_SIZING",
    "PROTECTION_PLAN",
    "RISK_APPROVAL",
}

PREFERRED_OWNER_PATHS = {
    "ORDER_SEND": "afip/demo_execution_gateway/runtime.py",
    "ORDER_CHECK": "afip/demo_execution_gateway/runtime.py",
    "UNIT_ALLOCATION": "afip/unit_allocation/runtime.py",
    "POSITION_SIZING": "afip/adaptive_position_sizing/runtime.py",
    "PROTECTION_PLAN": "afip/protection/sl_tp_planner.py",
    "RISK_APPROVAL": "afip/portfolio/portfolio_risk.py",
}


def _module_name(path: str) -> str:
    return path[:-3].replace("/", ".") if path.endswith(".py") else path.replace("/", ".")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_imports(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def _reverse_dependencies(all_paths: list[str]) -> dict[str, set[str]]:
    module_to_path = {_module_name(path): path for path in all_paths}
    reverse: dict[str, set[str]] = defaultdict(set)

    for source_path in all_paths:
        absolute = ROOT / source_path
        if not absolute.exists():
            continue
        for imported in _parse_imports(absolute):
            for module, target_path in module_to_path.items():
                if imported == module or imported.startswith(module + ".") or module.startswith(imported + "."):
                    if source_path != target_path:
                        reverse[target_path].add(source_path)
    return reverse


def _classify(
    authority: str,
    path: str,
    preferred_owner: str,
    reverse_dependencies: dict[str, set[str]],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    lower = path.lower()
    consumers = reverse_dependencies.get(path, set())

    if path == preferred_owner:
        reasons.append("preferred_by_explicit_cleanup_policy")
        reasons.append(f"consumer_count={len(consumers)}")
        return "PRIMARY_CANDIDATE", reasons

    if "/paper_" in lower or "/paper_trading/" in lower or "/shadow_" in lower:
        reasons.append("non_live_execution_namespace")
        return "RESEARCH_OR_SIMULATION", reasons

    if "/dashboard" in lower or lower.endswith("/models.py") or lower.endswith("/report.py"):
        reasons.append("presentation_or_data_model")
        return "OBSERVER_OR_MODEL", reasons

    if "/certification/" in lower or "_certification/" in lower or "/production_" in lower:
        reasons.append("certification_or_audit_namespace")
        return "CERTIFICATION_OBSERVER", reasons

    if "/execution_safety/" in lower:
        reasons.append("safety_boundary")
        return "SAFETY_GUARD", reasons

    if authority in {"ORDER_SEND", "ORDER_CHECK"}:
        reasons.append("non_owner_order_authority_requires_manual_review")
        return "BLOCKED_PENDING_REVIEW", reasons

    if consumers:
        reasons.append(f"consumer_count={len(consumers)}")
        return "SUPPORTING_CANDIDATE", reasons

    reasons.append("no_direct_consumers_detected")
    return "LEGACY_OR_UNUSED_CANDIDATE", reasons


def main() -> int:
    review_path = INVENTORY_ROOT / "architecture_review.json"
    components_path = INVENTORY_ROOT / "components.json"
    if not review_path.exists() or not components_path.exists():
        print("FAIL: Cleanup Pack 1 inventory outputs are missing.")
        return 1

    review = _read_json(review_path)
    components_doc = _read_json(components_path)
    components = components_doc.get("components", [])
    all_paths = [item["module_path"] for item in components if item.get("module_path")]
    reverse = _reverse_dependencies(all_paths)

    authority_index = review.get("authority_index", {})
    rows: list[dict[str, Any]] = []
    owner_registry: dict[str, Any] = {}
    blockers: list[dict[str, Any]] = []

    for authority in sorted(TARGET_RESPONSIBILITIES):
        paths = sorted(set(authority_index.get(authority, [])))
        preferred = PREFERRED_OWNER_PATHS[authority]
        preferred_exists = preferred in all_paths

        owner_registry[authority] = {
            "preferred_owner": preferred,
            "preferred_owner_exists": preferred_exists,
            "status": "CANDIDATE_NOT_CERTIFIED",
            "authority_paths": paths,
        }

        if not preferred_exists:
            blockers.append({
                "rule": f"{authority}_PREFERRED_OWNER_EXISTS",
                "preferred_owner": preferred,
            })

        for path in paths:
            classification, reasons = _classify(authority, path, preferred, reverse)
            rows.append({
                "authority": authority,
                "module_path": path,
                "classification": classification,
                "preferred_owner": path == preferred,
                "direct_consumer_count": len(reverse.get(path, set())),
                "direct_consumers": sorted(reverse.get(path, set())),
                "reasons": reasons,
            })

    gateway = "afip/demo_execution_gateway/runtime.py"
    for authority in ("ORDER_SEND", "ORDER_CHECK"):
        paths = sorted(set(authority_index.get(authority, [])))
        if paths != [gateway]:
            blockers.append({
                "rule": f"SINGLE_{authority}_AUTHORITY",
                "expected": [gateway],
                "actual": paths,
            })

    output = {
        "schema_version": "2.0",
        "status": "OWNER_SELECTION_PENDING_SOURCE_REVIEW",
        "owner_registry": owner_registry,
        "classifications": rows,
        "blockers": blockers,
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "responsibility_matrix.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with (OUTPUT_ROOT / "responsibility_matrix.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "authority", "module_path", "classification", "preferred_owner",
            "direct_consumer_count", "reasons",
        ])
        for row in rows:
            writer.writerow([
                row["authority"],
                row["module_path"],
                row["classification"],
                row["preferred_owner"],
                row["direct_consumer_count"],
                "|".join(row["reasons"]),
            ])

    md = [
        "# AFIP Responsibility Matrix",
        "",
        "This report selects candidates only. It does not redirect runtime calls yet.",
        "",
    ]
    for authority in sorted(owner_registry):
        entry = owner_registry[authority]
        md.extend([
            f"## {authority}",
            "",
            f"- Preferred owner: `{entry['preferred_owner']}`",
            f"- Exists: **{entry['preferred_owner_exists']}**",
            f"- Status: **{entry['status']}**",
            "",
        ])
        related = [row for row in rows if row["authority"] == authority]
        counts: dict[str, int] = defaultdict(int)
        for row in related:
            counts[row["classification"]] += 1
        for classification, count in sorted(counts.items()):
            md.append(f"- {classification}: **{count}**")
        md.append("")

    md.extend([
        "## Next Gate",
        "",
        "Cleanup Pack 3 may redirect Unit Allocation only after the preferred owner "
        "and its direct consumers are inspected. No module deletion is permitted.",
    ])
    (OUTPUT_ROOT / "RESPONSIBILITY_MATRIX.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "status": output["status"],
        "classified_records": len(rows),
        "blockers": len(blockers),
        "output": str(OUTPUT_ROOT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
