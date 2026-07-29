from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "node_modules", "dist", "build",
}
TERMS = (
    "intelligence", "signal", "decision", "regime", "pattern", "risk",
    "execution", "research", "historical", "collector", "loader",
    "gateway", "supervisor", "launcher", "runner", "engine",
)
PROCESS_LEAVES = {"popen", "run", "call", "check_call", "check_output", "system"}
WRITER_LEAVES = {
    "write_text", "write_bytes", "open", "dump", "dumps", "replace",
    "rename", "touch", "to_json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def relative_parts(path: Path, root: Path) -> tuple[str, ...]:
    try:
        return tuple(part.lower() for part in path.relative_to(root).parts)
    except ValueError:
        return tuple(part.lower() for part in path.parts)


def is_test_or_generated_path(rel_parts: tuple[str, ...]) -> bool:
    directory_parts = rel_parts[:-1]
    for part in directory_parts:
        if part in EXCLUDED_DIRS:
            return True
        if part == "runtime":
            return True
        if part in {"tests", "test", "docs", "documentation", "examples"}:
            return True
        if part.startswith(("pytest_temp", "pytest-", "temp_", "tmp_")):
            return True
        if "certification_pack" in part or part.startswith(("pack_", "patch_", "backup_")):
            return True
    return False


def is_production_source(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = tuple(part.lower() for part in rel.parts)
    if is_test_or_generated_path(parts):
        return False

    # Canonical AFIP source/runtime tooling roots.
    if len(parts) > 1 and parts[0] in {
        "afip", "tools", "config", "scripts", "service", "services"
    }:
        return True

    # Root-level launchers and Python entry points are production candidates.
    if len(parts) == 1 and path.suffix.lower() in {".py", ".ps1", ".bat", ".cmd"}:
        return True

    return False


def iter_source_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".ps1", ".bat", ".cmd"}:
            continue
        if is_production_source(path, root):
            yield path


def dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def string_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        pieces: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pieces.append(value.value)
            else:
                pieces.append("{dynamic}")
        return "".join(pieces)
    return None


def path_expression_value(node: ast.AST) -> str | None:
    direct = string_value(node)
    if direct is not None:
        return direct

    if isinstance(node, ast.Call):
        call_name = dotted_name(node.func).lower()
        if call_name in {"path", "pathlib.path", "purepath", "pathlib.purepath"} and node.args:
            return path_expression_value(node.args[0])

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = path_expression_value(node.left)
        right = path_expression_value(node.right)
        if left is not None and right is not None:
            return f"{left.rstrip('/\\')}/{right.lstrip('/\\')}"

    return None


def normalized_json_target(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.replace("\\", "/")
    if normalized.lower().endswith((".json", ".jsonl")):
        return normalized
    return None


def target_from_writer_call(node: ast.Call) -> str | None:
    name = dotted_name(node.func).lower()
    leaf = name.rsplit(".", 1)[-1]

    # Path('runtime/state.json').write_text(...)
    if isinstance(node.func, ast.Attribute) and leaf in {
        "write_text", "write_bytes", "touch", "replace", "rename", "to_json"
    }:
        value = path_expression_value(node.func.value)
        target = normalized_json_target(value)
        if target:
            return target

    # open('runtime/state.json', ...), json.dump(..., open(...))
    if leaf == "open" and node.args:
        return normalized_json_target(path_expression_value(node.args[0]))

    # json.dump(payload, file_handle) cannot always recover the path statically,
    # but direct string/path arguments are still detected.
    for arg in list(node.args) + [kw.value for kw in node.keywords]:
        target = normalized_json_target(path_expression_value(arg))
        if target:
            return target

    return None


def inspect_python(path: Path, root: Path) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    source = path.read_text(encoding="utf-8", errors="replace")
    result: dict[str, Any] = {
        "path": rel,
        "sha256": sha256_text(source),
        "definitions": [],
        "process_calls": [],
        "writer_calls": [],
        "json_targets": [],
        "main_entrypoint": False,
        "parse_error": None,
    }
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        result["parse_error"] = f"{exc.msg}:{exc.lineno}"
        return result

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result["definitions"].append({
                "name": node.name,
                "kind": type(node).__name__,
                "line": getattr(node, "lineno", None),
            })
        elif isinstance(node, ast.Call):
            name = dotted_name(node.func).lower()
            leaf = name.rsplit(".", 1)[-1]
            if leaf in PROCESS_LEAVES or any(
                token in name for token in ("subprocess.", "multiprocessing.", "os.system")
            ):
                result["process_calls"].append({
                    "call": name,
                    "line": getattr(node, "lineno", None),
                })
            if leaf in WRITER_LEAVES:
                result["writer_calls"].append({
                    "call": name,
                    "line": getattr(node, "lineno", None),
                })
            target = target_from_writer_call(node)
            if target:
                result["json_targets"].append({
                    "target": target,
                    "line": getattr(node, "lineno", None),
                })
        elif isinstance(node, ast.If):
            try:
                test_text = ast.unparse(node.test)
            except Exception:
                test_text = ""
            if "__name__" in test_text and "__main__" in test_text:
                result["main_entrypoint"] = True

    result["json_targets"] = sorted(
        {json.dumps(item, sort_keys=True): item for item in result["json_targets"]}.values(),
        key=lambda item: (item["target"], item["line"] or 0),
    )
    return result


def historical_truth(root: Path) -> dict[str, Any]:
    runtime_root = root / "runtime"
    if not runtime_root.is_dir():
        return {"source": None, "status": "NOT_FOUND", "boundaries_are_separated": False}

    preferred = [
        runtime_root / "historical_data" / "historical_dashboard.json",
        runtime_root / "historical_data" / "dashboard.json",
        runtime_root / "historical_data_dashboard.json",
    ]
    discovered = list(runtime_root.glob("**/*historical*dashboard*.json"))
    discovered += list(runtime_root.glob("**/historical_data/**/dashboard*.json"))

    candidates: list[Path] = []
    seen: set[Path] = set()
    for path in preferred + discovered:
        if not path.is_file():
            continue
        rel_parts = tuple(part.lower() for part in path.relative_to(root).parts)
        if any(
            part.startswith(("pytest_temp", "pytest-", "test_", "tmp_"))
            or part in {"architecture_intelligence_certification", ".pytest_cache"}
            for part in rel_parts
        ):
            continue
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(path)

    scored: list[tuple[int, float, Path, dict[str, Any]]] = []
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        discovery = payload.get("history_discovery") or {}
        score = sum(
            value is not None
            for value in (
                payload.get("coverage_start_utc"),
                payload.get("coverage_end_utc"),
                payload.get("next_start_utc"),
                discovery.get("earliest_available_utc"),
                payload.get("quality_status"),
                payload.get("batches_completed"),
                payload.get("total_dataset_bytes"),
            )
        )
        try:
            modified = path.stat().st_mtime
        except OSError:
            modified = 0.0
        scored.append((score, modified, path, payload))

    if not scored:
        return {"source": None, "status": "NOT_FOUND", "boundaries_are_separated": False}

    _, _, path, payload = max(scored, key=lambda item: (item[0], item[1]))
    discovery = payload.get("history_discovery") or {}
    broker_start = discovery.get("earliest_available_utc")
    dataset_start = payload.get("coverage_start_utc")
    checkpoint = payload.get("next_start_utc")
    return {
        "source": path.relative_to(root).as_posix(),
        "status": payload.get("status"),
        "quality_status": payload.get("quality_status"),
        "broker_history_start_utc": broker_start,
        "dataset_start_utc": dataset_start,
        "dataset_end_utc": payload.get("coverage_end_utc"),
        "checkpoint_next_start_utc": checkpoint,
        "boundaries_are_separated": all(
            value is not None for value in (broker_start, dataset_start, checkpoint)
        ),
        "missing_intervals": payload.get("missing_intervals"),
        "batches_completed": payload.get("batches_completed"),
        "total_dataset_bytes": payload.get("total_dataset_bytes"),
    }


def build_report(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    definitions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    hashes: dict[str, list[str]] = defaultdict(list)
    json_targets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    components: list[dict[str, Any]] = []
    entrypoints: list[str] = []
    launchers: list[dict[str, Any]] = []
    python_count = 0
    script_count = 0

    for path in iter_source_files(root):
        rel = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8", errors="replace")
        hashes[sha256_text(source)].append(rel)

        if path.suffix.lower() == ".py":
            python_count += 1
            inspected = inspect_python(path, root)
            for definition in inspected["definitions"]:
                name = definition["name"].lower()
                if any(term in name for term in TERMS):
                    definitions[name].append({
                        "path": rel,
                        "kind": definition["kind"],
                        "line": definition["line"],
                    })
            for target in inspected["json_targets"]:
                json_targets[target["target"]].append({
                    "path": rel,
                    "line": target["line"],
                })
            categories = [term for term in TERMS if term in rel.lower()]
            if categories:
                components.append({
                    "path": rel,
                    "categories": categories,
                    "main_entrypoint": inspected["main_entrypoint"],
                    "process_call_count": len(inspected["process_calls"]),
                    "writer_call_count": len(inspected["writer_calls"]),
                    "json_targets": inspected["json_targets"],
                })
            if inspected["main_entrypoint"]:
                entrypoints.append(rel)
            if inspected["process_calls"]:
                launchers.append({"path": rel, "calls": inspected["process_calls"]})
        else:
            script_count += 1
            entrypoints.append(rel)
            calls = [
                {"line": line_number, "text": line.strip()[:300]}
                for line_number, line in enumerate(source.splitlines(), start=1)
                if any(
                    token in line.lower()
                    for token in ("start-process", "python ", "python.exe", "pythonw")
                )
            ]
            if calls:
                launchers.append({"path": rel, "calls": calls})

    exact_duplicates = [
        {"sha256": digest, "paths": sorted(paths), "count": len(paths)}
        for digest, paths in hashes.items()
        if len(paths) > 1
    ]
    repeated_definitions = [
        {"definition": name, "locations": locations, "count": len(locations)}
        for name, locations in sorted(definitions.items())
        if len({location["path"] for location in locations}) > 1
    ]
    shared_targets = [
        {
            "target": target,
            "writers": writers,
            "writer_count": len({writer["path"] for writer in writers}),
        }
        for target, writers in sorted(json_targets.items())
        if len({writer["path"] for writer in writers}) > 1
    ]

    blockers: list[str] = []
    if repeated_definitions:
        blockers.append("repeated_intelligence_or_engine_definitions_require_review")
    if shared_targets:
        blockers.append("multiple_source_files_reference_same_json_target")
    if exact_duplicates:
        blockers.append("exact_duplicate_source_files_detected")
    if launchers:
        blockers.append("process_launchers_require_single_runtime_authority_review")

    return {
        "schema_version": "afip-runtime-intelligence-audit.v1.2",
        "generated_at_utc": now_utc(),
        "project_root": str(root),
        "status": "REVIEW_REQUIRED" if blockers else "PASS",
        "blockers": blockers,
        "summary": {
            "python_files_scanned": python_count,
            "script_files_scanned": script_count,
            "component_files": len(components),
            "entrypoints": len(set(entrypoints)),
            "process_launchers": len(launchers),
            "exact_duplicate_groups": len(exact_duplicates),
            "repeated_definition_groups": len(repeated_definitions),
            "shared_json_target_groups": len(shared_targets),
        },
        "historical_data_truth": historical_truth(root),
        "component_inventory": sorted(components, key=lambda item: item["path"]),
        "entrypoints": sorted(set(entrypoints)),
        "process_launchers": launchers,
        "exact_duplicate_files": exact_duplicates,
        "repeated_intelligence_definitions": repeated_definitions,
        "shared_json_targets": shared_targets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only AFIP Runtime Architecture and Intelligence audit."
    )
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    output_dir = root / "runtime" / "architecture_intelligence_certification"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(root)
    report_path = output_dir / "audit_report.json"
    summary_path = output_dir / "audit_summary.txt"

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary_path.write_text(
        "\n".join(
            [f"Status: {report['status']}"]
            + [f"{key}: {value}" for key, value in report["summary"].items()]
            + [f"Report: {report_path}"]
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "summary": report["summary"],
                "historical_data_truth": report["historical_data_truth"],
                "report_path": str(report_path),
                "summary_path": str(summary_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
