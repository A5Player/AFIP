from __future__ import annotations

import argparse
import ast
import json
from functools import lru_cache
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Target:
    name: str
    source_glob: str
    symbols: tuple[str, ...]
    mt5_capable: bool = False


TARGETS = (
    Target("CompleteTradePlan", "afip/complete_trade_plan/*.py", ("CompleteTradePlan", "CompleteTradePlanCertifier")),
    Target("PositionCare", "afip/position_care_runtime/*.py", ("PositionCareSupervisor", "PositionCareDecision")),
    Target("TradeLifecycle", "afip/engine/trade_lifecycle_engine.py", ("TradeLifecycleEngine",)),
    Target("RuntimeAuthority", "afip/*runtime_authority*.py", ("RUNTIME_AUTHORITY_VERSION", "clean_stale_runtime", "reclaim_stale_lock")),
    Target("SequentialRouter", "afip/four_profile_operations/*.py", ("run_sequential", "sequential_router", "account_routing")),
    Target("LotAuthority", "afip/lot_authority/*.py", ("calculate_lot_authority",)),
    Target("DemoExecutionGateway", "afip/demo_execution_gateway/*.py", ("DemoExecutionGateway",), mt5_capable=True),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def py_files(root: Path) -> list[Path]:
    files = list((root / "afip").rglob("*.py")) + list((root / "tools").rglob("*.py"))
    return [p for p in files if "patch_backups" not in p.parts]


@lru_cache(maxsize=None)
def parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
    except SyntaxError:
        return None


def target_files(root: Path, target: Target) -> list[Path]:
    return sorted(root.glob(target.source_glob))


def symbol_definitions(files: Iterable[Path], symbols: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for path in files:
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in symbols or any(s.lower() in node.name.lower() for s in symbols):
                    found.append(f"{path.as_posix()}:{node.lineno}:{node.name}")
    return found


def references(files: Iterable[Path], symbols: tuple[str, ...], exclude: set[Path]) -> tuple[list[str], list[str]]:
    imports: list[str] = []
    calls: list[str] = []
    lowered = {s.lower() for s in symbols}
    for path in files:
        if path in exclude:
            continue
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name.lower() in lowered or any(s in alias.name.lower() for s in lowered):
                        imports.append(f"{path.as_posix()}:{node.lineno}:{alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if any(s in alias.name.lower() for s in lowered):
                        imports.append(f"{path.as_posix()}:{node.lineno}:{alias.name}")
            elif isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name.lower() in lowered or any(s in name.lower() for s in lowered):
                    calls.append(f"{path.as_posix()}:{node.lineno}:{name}")
    return sorted(set(imports)), sorted(set(calls))


def text_markers(files: Iterable[Path], markers: tuple[str, ...]) -> list[str]:
    results: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in markers:
            if marker in text:
                results.append(f"{path.as_posix()}:{marker}")
    return sorted(set(results))


def runtime_evidence(root: Path, target: Target) -> dict:
    evidence_files = list((root / "runtime").rglob("*.json")) + list((root / "runtime").rglob("*.jsonl"))
    evidence: list[str] = []
    needles = tuple({target.name.lower(), *(s.lower() for s in target.symbols)})
    for path in evidence_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if any(n in text for n in needles):
            evidence.append(path.relative_to(root).as_posix())
            if len(evidence) >= 20:
                break
    return {"present": bool(evidence), "files": evidence}


@lru_cache(maxsize=4)
def audit(root: Path) -> dict:
    all_files = py_files(root)
    rows = []
    for target in TARGETS:
        src = target_files(root, target)
        definitions = symbol_definitions(src, target.symbols)
        imports, calls = references(all_files, target.symbols, set(src))
        source_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in src)
        # A descriptive source comment saying that a component does not transmit
        # orders directly must not be interpreted as proof that the component has
        # no runtime effect. Runtime effect is established from real call sites.
        # Only an explicit executable assignment can mark a target as neutral.
        execution_neutral = "execution_permission = false" in source_text.lower()
        mt5_markers = text_markers(src, ("order_send", "order_check", "positions_get", "MetaTrader5"))
        dashboard_markers = text_markers(all_files, (target.name, *target.symbols))
        research_markers = [m for m in dashboard_markers if "research" in m.lower() or "dataset" in m.lower()]
        runtime = runtime_evidence(root, target)

        exists = bool(src and definitions)
        connected = bool(imports)
        called = bool(calls)
        affects_runtime = called
        mt5 = bool(mt5_markers) and target.mt5_capable
        dashboard = any("dashboard" in m.lower() for m in dashboard_markers)
        research = bool(research_markers)
        authority = target.name in {"RuntimeAuthority", "LotAuthority", "DemoExecutionGateway"} or "authority" in source_text.lower()

        if not exists:
            status = "MISSING"
        elif not connected:
            status = "ORPHAN"
        elif not called:
            status = "DEAD_CODE"
        elif not runtime["present"]:
            status = "PARTIAL"
        else:
            status = "ACTIVE"

        rows.append({
            "module": target.name,
            "exists": exists,
            "connected": connected,
            "called": called,
            "affects_runtime": affects_runtime,
            "mt5": mt5,
            "dashboard": dashboard,
            "research": research,
            "authority": authority,
            "execution_neutral": execution_neutral,
            "status": status,
            "evidence": {
                "source_files": [p.relative_to(root).as_posix() for p in src],
                "definitions": definitions,
                "imports": imports[:25],
                "calls": calls[:25],
                "runtime": runtime,
                "mt5_markers": mt5_markers[:20],
            },
        })

    duplicates: dict[str, list[str]] = {}
    symbol_locations: dict[str, list[str]] = {}
    for path in all_files:
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and not node.name.startswith("_"):
                symbol_locations.setdefault(node.name, []).append(f"{path.relative_to(root).as_posix()}:{node.lineno}")
    for name, locations in symbol_locations.items():
        if len(locations) > 1 and any(k in name.lower() for k in ("authority", "positioncare", "lifecycle", "tradeplan", "lot")):
            duplicates[name] = locations

    blockers = []
    for row in rows:
        if row["module"] in {"CompleteTradePlan", "PositionCare", "TradeLifecycle", "LotAuthority", "DemoExecutionGateway"} and row["status"] != "ACTIVE":
            blockers.append(f"{row['module']}:{row['status']}")
    return {
        "schema_version": "afip-production-activation-audit.v1",
        "generated_at_utc": utc_now(),
        "repository_root": str(root),
        "audit_levels": 10,
        "modules": rows,
        "duplicate_candidates": duplicates,
        "critical_blockers": blockers,
        "production_activation_certified": not blockers,
        "status": "PASS" if not blockers else "REVIEW_REQUIRED",
    }


def html(report: dict) -> str:
    rows = []
    for item in report["modules"]:
        cells = [item["module"], item["exists"], item["connected"], item["called"], item["affects_runtime"], item["mt5"], item["dashboard"], item["research"], item["authority"], item["status"]]
        rows.append("<tr>" + "".join(f"<td>{str(v)}</td>" for v in cells) + "</tr>")
    return f"""<!doctype html><meta charset='utf-8'><title>AFIP Production Activation Audit</title>
<style>body{{font-family:Segoe UI,Arial;margin:24px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:7px;text-align:left}}th{{background:#eee}}.bad{{font-weight:700}}</style>
<h1>AFIP V1 Production Activation Audit</h1><p>Status: <b>{report['status']}</b> | Certified: <b>{report['production_activation_certified']}</b></p>
<p>Critical blockers: {', '.join(report['critical_blockers']) or 'None'}</p>
<table><thead><tr><th>Module</th><th>Exists</th><th>Connected</th><th>Called</th><th>Runtime Effect</th><th>MT5</th><th>Dashboard</th><th>Research</th><th>Authority</th><th>Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    out = root / "runtime" / "activation_audit"
    out.mkdir(parents=True, exist_ok=True)
    report = audit(root)
    (out / "module_activation_matrix.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "production_activation_report.html").write_text(html(report), encoding="utf-8")
    summary = {
        "status": report["status"],
        "production_activation_certified": report["production_activation_certified"],
        "critical_blockers": report["critical_blockers"],
        "report": str(out / "module_activation_matrix.json"),
    }
    print(json.dumps(summary, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
