"""AFIP A25 read-only full-system integration and authority audit."""
from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    check_id: str
    status: str
    reason: str
    evidence: tuple[str, ...] = ()


REQUIRED_PATHS = (
    "afip/production_runtime_authority.py",
    "afip/operational_runtime.py",
    "afip/dashboard_ui/split_runtime.py",
    "afip/historical_replay_research/runtime.py",
    "afip/exit_outcome_research/a16_contract.py",
    "afip/exit_outcome_research/a16_core.py",
    "afip/exit_evidence_research/a20_holding_exit.py",
    "afip/exit_evidence_research/a21_holding_exit_producer.py",
    "afip/exit_evidence_research/a22_walk_forward.py",
    "afip/exit_evidence_research/a23_completion.py",
    "afip/exit_evidence_research/a24_tp_volume.py",
)

RESEARCH_MODULES = (
    "afip/exit_outcome_research/a16_contract.py",
    "afip/exit_outcome_research/a16_core.py",
    "afip/exit_outcome_research/a16_r_ladder.py",
    "afip/exit_evidence_research/a16_evidence.py",
    "afip/exit_evidence_research/a16_bridge.py",
    "afip/exit_evidence_research/a16_completion.py",
    "afip/exit_evidence_research/a17_replay_intake.py",
    "afip/exit_evidence_research/a18_observability.py",
    "afip/exit_evidence_research/a20_holding_exit.py",
    "afip/exit_evidence_research/a21_holding_exit_producer.py",
    "afip/exit_evidence_research/a22_walk_forward.py",
    "afip/exit_evidence_research/a23_completion.py",
    "afip/exit_evidence_research/a24_tp_volume.py",
)

FORBIDDEN_RESEARCH_IMPORT_PREFIXES = (
    "MetaTrader5", "afip.execution", "afip.demo_execution_gateway",
    "afip.protected_execution", "afip.mt5_execution",
)

DATASET_MARKERS = (
    "a16_exit_evidence_observations", "a16_exit_policy_rankings",
    "a17_exit_replay_intake_runs", "a18_research_runtime_status",
    "a20_holding_exit_observations", "a22_holding_exit_validation_observations",
    "a22_holding_exit_validation_results", "a23_holding_exit_certifications",
    "a24_tp_volume_decisions", "a24_tp_volume_outcomes", "a24_tp_volume_summaries",
)


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.append(node.module)
    return tuple(values)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(("git", *args), cwd=root, check=False,
                               text=True, capture_output=True)
    return completed.stdout.strip() if completed.returncode == 0 else "UNAVAILABLE"


def audit(root: Path) -> dict[str, object]:
    root = root.resolve()
    findings: list[Finding] = []
    missing = tuple(path for path in REQUIRED_PATHS if not (root / path).is_file())
    findings.append(Finding("SOURCE_TOPOLOGY", "PASS" if not missing else "FAIL",
                            "required integration source paths are present" if not missing
                            else "required integration source paths are missing", missing))

    syntax_errors: list[str] = []
    for relative in REQUIRED_PATHS:
        path = root / relative
        if path.is_file():
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=relative)
            except (SyntaxError, UnicodeError) as exc:
                syntax_errors.append(f"{relative}: {exc}")
    findings.append(Finding("SOURCE_PARSE", "PASS" if not syntax_errors else "FAIL",
                            "required source parses successfully" if not syntax_errors
                            else "source parse failures detected", tuple(syntax_errors)))

    authority_violations: list[str] = []
    for relative in RESEARCH_MODULES:
        path = root / relative
        if not path.is_file():
            authority_violations.append(f"missing:{relative}")
            continue
        for imported in _imports(path):
            if any(imported == prefix or imported.startswith(prefix + ".")
                   for prefix in FORBIDDEN_RESEARCH_IMPORT_PREFIXES):
                authority_violations.append(f"{relative} imports {imported}")
    findings.append(Finding("RESEARCH_EXECUTION_ISOLATION",
                            "PASS" if not authority_violations else "FAIL",
                            "research path has no execution/MT5 imports" if not authority_violations
                            else "research path crosses execution authority", tuple(authority_violations)))

    runtime_path = root / "afip/historical_replay_research/runtime.py"
    runtime_text = runtime_path.read_text(encoding="utf-8") if runtime_path.is_file() else ""
    missing_datasets = tuple(value for value in DATASET_MARKERS if value not in runtime_text)
    findings.append(Finding("APPEND_ONLY_DATASET_CHAIN", "PASS" if not missing_datasets else "FAIL",
                            "A16-A24 evidence datasets share the append-only registry" if not missing_datasets
                            else "research datasets are absent from the append-only registry", missing_datasets))

    init_text = _read(root, "afip/exit_evidence_research/__init__.py") if (
        root / "afip/exit_evidence_research/__init__.py").is_file() else ""
    exports = ("A20HoldingExitResearch", "A21HoldingExitEvidenceProducer",
               "A22WalkForwardValidator", "A23HoldingExitCompletion", "A24TPVolumeResearch")
    missing_exports = tuple(value for value in exports if value not in init_text)
    findings.append(Finding("RESEARCH_PUBLIC_CONTRACT", "PASS" if not missing_exports else "FAIL",
                            "holding/exit research stages are publicly connected" if not missing_exports
                            else "holding/exit public exports are incomplete", missing_exports))

    dashboard_text = _read(root, "afip/dashboard_ui/split_runtime.py") if (
        root / "afip/dashboard_ui/split_runtime.py").is_file() else ""
    dashboard_markers = ("A20–A23 Holding & Exit Research",
                         "A24 TP Buffer & Volume-Aware Exit Research",
                         "execution authority: NONE", "no automatic promotion")
    missing_dashboard = tuple(value for value in dashboard_markers if value not in dashboard_text)
    findings.append(Finding("READ_ONLY_DASHBOARD_CHAIN", "PASS" if not missing_dashboard else "FAIL",
                            "dashboard exposes persisted research without authority" if not missing_dashboard
                            else "dashboard research contract is incomplete", missing_dashboard))

    a24_text = _read(root, "afip/exit_evidence_research/a24_tp_volume.py") if (
        root / "afip/exit_evidence_research/a24_tp_volume.py").is_file() else ""
    safety_markers = ("MT5_TICK_VOLUME", "future_data_used", "no_order_sent",
                      "automatic_promotion_allowed", 'execution_authority: str = "NONE"',
                      "a22_holding_exit_validation_observations")
    missing_safety = tuple(value for value in safety_markers if value not in a24_text)
    findings.append(Finding("A24_DECISION_OUTCOME_SAFETY", "PASS" if not missing_safety else "FAIL",
                            "A24 preserves volume provenance, leakage and authority guards"
                            if not missing_safety else "A24 safety markers are incomplete", missing_safety))

    test_names = tuple(f"tests/test_a{number}" for number in range(16, 25))
    test_inventory = tuple(path.name for path in (root / "tests").glob("test_a*.py")) if (
        root / "tests").is_dir() else ()
    missing_test_stages = tuple(prefix for prefix in test_names
                                if not any(name.startswith(Path(prefix).name) for name in test_inventory))
    findings.append(Finding("A16_A24_TEST_CONTINUITY", "PASS" if not missing_test_stages else "FAIL",
                            "A16-A24 test stages are present" if not missing_test_stages
                            else "research stage tests are missing", missing_test_stages))

    failed = tuple(item.check_id for item in findings if item.status != "PASS")
    return {
        "schema": "afip.a25.full_system_integration_audit.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root), "git_head": _git(root, "rev-parse", "HEAD"),
        "git_branch": _git(root, "branch", "--show-current"),
        "status": "PASS" if not failed else "FAIL",
        "execution_authority_changed": False,
        "source_modified_by_audit": False,
        "automatic_repair_performed": False,
        "failed_checks": failed,
        "findings": [asdict(item) for item in findings],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = audit(Path(args.project_root))
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 1 if args.strict and report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
