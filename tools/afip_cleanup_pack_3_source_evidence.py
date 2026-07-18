from __future__ import annotations

import ast
import json
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "runtime" / "architecture_cleanup_pack_3"

TARGETS = [
    "afip/demo_execution_gateway/runtime.py",
    "afip/unit_allocation/runtime.py",
    "afip/unit_allocation/models.py",
    "afip/four_profile_operations/runtime.py",
    "afip/capital_growth_engine/runtime.py",
    "afip/adaptive_position_sizing/runtime.py",
    "afip/protection/sl_tp_planner.py",
    "afip/execution_safety/capital_aware_protection_guard.py",
    "afip/portfolio/portfolio_risk.py",
]

CONFIG_CANDIDATES = [
    "config/four_profile_demo.json",
    "config/afip.json",
    "config/runtime.json",
]

KEYWORDS = [
    "allocated_units",
    "maximum_units",
    "max_units",
    "capital_per_unit",
    "base_lot",
    "order_send",
    "order_check",
    "sl_points",
    "tp_points",
    "stop_loss",
    "take_profit",
    "atr",
    "buffer",
    "profile_unit_capacity_unavailable",
]


def module_name(path: str) -> str:
    return path[:-3].replace("/", ".") if path.endswith(".py") else path.replace("/", ".")


def source_segment(text: str, node: ast.AST) -> str:
    lines = text.splitlines()
    start = max(getattr(node, "lineno", 1) - 1, 0)
    end = getattr(node, "end_lineno", start + 1)
    return "\n".join(lines[start:end])


def inspect_python(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"syntax_error": str(exc), "path": str(path)}

    imports = []
    functions = []
    classes = []
    calls = []
    keyword_hits = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = source_segment(text, node)
            relevant = [kw for kw in KEYWORDS if kw.lower() in body.lower()]
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "relevant_keywords": relevant,
                "source": body if relevant else "",
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })
        elif isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                parts = []
                current = node.func
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                name = ".".join(reversed(parts))
            if name:
                calls.append({"name": name, "line": getattr(node, "lineno", None)})

    for index, line in enumerate(text.splitlines(), start=1):
        for keyword in KEYWORDS:
            if keyword.lower() in line.lower():
                keyword_hits.append({
                    "line": index,
                    "keyword": keyword,
                    "text": line.strip(),
                })

    return {
        "path": path.relative_to(ROOT).as_posix(),
        "module": module_name(path.relative_to(ROOT).as_posix()),
        "imports": sorted(set(imports)),
        "classes": classes,
        "functions": functions,
        "calls": calls,
        "keyword_hits": keyword_hits,
    }


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    copied_root = OUTPUT / "source_snapshot"
    copied_root.mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": "3.0",
        "status": "SOURCE_EVIDENCE_COLLECTED",
        "targets": [],
        "missing_targets": [],
        "configs": [],
        "cross_module_findings": [],
    }

    for rel in TARGETS:
        source = ROOT / rel
        if not source.exists():
            report["missing_targets"].append(rel)
            continue

        destination = copied_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        report["targets"].append(inspect_python(source))

    for rel in CONFIG_CANDIDATES:
        source = ROOT / rel
        if not source.exists():
            continue
        destination = copied_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        text = source.read_text(encoding="utf-8", errors="replace")
        report["configs"].append({
            "path": rel,
            "keyword_hits": [
                {"line": index, "text": line.strip()}
                for index, line in enumerate(text.splitlines(), start=1)
                if any(keyword.lower() in line.lower() for keyword in KEYWORDS)
            ],
        })

    gateway = next(
        (item for item in report["targets"]
         if item.get("path") == "afip/demo_execution_gateway/runtime.py"),
        None,
    )
    if gateway:
        imported = set(gateway.get("imports", []))
        report["cross_module_findings"].append({
            "rule": "GATEWAY_IMPORTS_UNIT_ALLOCATION_OWNER",
            "passed": any(
                name == "afip.unit_allocation"
                or name.startswith("afip.unit_allocation.")
                for name in imported
            ),
            "imports": sorted(imported),
        })

        call_names = [item["name"] for item in gateway.get("calls", [])]
        report["cross_module_findings"].append({
            "rule": "GATEWAY_CALLS_ORDER_SEND",
            "passed": any(name.endswith("order_send") for name in call_names),
            "calls": [name for name in call_names if "order_" in name.lower()],
        })

    output_json = OUTPUT / "source_evidence.json"
    output_json.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = [
        "# AFIP Cleanup Pack 3 — Source Evidence",
        "",
        f"- Source targets collected: **{len(report['targets'])}**",
        f"- Missing targets: **{len(report['missing_targets'])}**",
        f"- Config files collected: **{len(report['configs'])}**",
        "",
        "## Cross-module findings",
        "",
    ]
    for finding in report["cross_module_findings"]:
        md.append(
            f"- {finding['rule']}: **{'PASS' if finding['passed'] else 'FAIL'}**"
        )

    if report["missing_targets"]:
        md.extend(["", "## Missing targets", ""])
        md.extend(f"- `{path}`" for path in report["missing_targets"])

    md.extend([
        "",
        "## Important",
        "",
        "This pack only collects and analyzes the exact source involved in Unit "
        "Allocation, Position Sizing, Protection Planning, Risk Approval, and "
        "MT5 order submission. It does not alter runtime behavior.",
    ])
    (OUTPUT / "SOURCE_EVIDENCE.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    zip_path = OUTPUT / "AFIP_CLEANUP_PACK_3_SOURCE_EVIDENCE_RESULT.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(output_json, output_json.relative_to(OUTPUT))
        archive.write(OUTPUT / "SOURCE_EVIDENCE.md", "SOURCE_EVIDENCE.md")
        for path in copied_root.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(OUTPUT))

    print(json.dumps({
        "status": report["status"],
        "targets": len(report["targets"]),
        "missing_targets": len(report["missing_targets"]),
        "configs": len(report["configs"]),
        "result_zip": str(zip_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
