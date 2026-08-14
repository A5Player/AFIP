"""A26 fail-closed end-to-end operational evidence classifier.

Read-only: no MT5 import, subprocess launch, scheduler, order or source write.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


@dataclass(frozen=True)
class StageProof:
    stage_id: str
    status: str
    reason: str
    evidence: tuple[str, ...]
    execution_performed: bool = False


STAGES = (
    ("MARKET_DATA", ("afip/pipeline/real_market_data_intelligence_wiring.py", "afip/historical_data_manager/history_runtime.py")),
    ("INTELLIGENCE", ("afip/pipeline/modular_intelligence_pipeline.py", "afip/fusion/intelligence_fusion_core.py")),
    ("DECISION_TRACE", ("afip/decision/unified_decision_engine.py", "afip/decision/decision_traceability.py")),
    ("RISK_AND_CAPITAL_GATES", ("afip/execution_safety/capital_aware_protection_guard.py", "afip/position/position_sizer.py")),
    ("PROTECTED_EXECUTION_BOUNDARY", ("afip/execution/protected_simulation_order_builder.py", "afip/decision_execution_flow/decision_execution_runtime.py")),
    ("POSITION_CARE", ("afip/position_care_runtime/runtime.py",)),
    ("HOLDING_EXIT_RESEARCH", ("afip/exit_evidence_research/a20_holding_exit.py", "afip/exit_evidence_research/a24_tp_volume.py")),
    ("RESEARCH_VALIDATION", ("afip/exit_evidence_research/a22_walk_forward.py", "afip/exit_evidence_research/a23_completion.py")),
    ("DASHBOARD", ("afip/dashboard_ui/split_runtime.py",)),
)


def _load_a25(root: Path):
    path=root/"tools/afip_a25_full_system_integration_audit.py"
    spec=importlib.util.spec_from_file_location("afip_a25_runtime_audit",path)
    if spec is None or spec.loader is None: raise RuntimeError("A25 audit cannot be loaded")
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def _tests_for(root: Path, tokens: tuple[str, ...]) -> tuple[str, ...]:
    names=tuple(path.name for path in (root/"tests").glob("test_*.py"))
    return tuple(name for name in names if any(token in name for token in tokens))[:20]


def build_proof(root: Path) -> dict[str, Any]:
    root=root.resolve();a25=_load_a25(root).audit(root)
    stages: list[StageProof]=[]
    token_map={
      "MARKET_DATA":("market_data","historical_data"),"INTELLIGENCE":("intelligence","fusion"),
      "DECISION_TRACE":("decision","trace"),"RISK_AND_CAPITAL_GATES":("capital","position_siz","risk"),
      "PROTECTED_EXECUTION_BOUNDARY":("execution_gateway","protected_simulation","decision_execution"),
      "POSITION_CARE":("position_care",),"HOLDING_EXIT_RESEARCH":("holding_exit","a24"),
      "RESEARCH_VALIDATION":("a22","a23"),"DASHBOARD":("dashboard",)}
    for stage_id,paths in STAGES:
        missing=tuple(path for path in paths if not (root/path).is_file())
        tests=_tests_for(root,token_map[stage_id])
        status="TESTED" if not missing and tests else "BLOCKED"
        evidence=tuple(paths)+tests if status=="TESTED" else missing or ("matching_test_evidence_missing",)
        stages.append(StageProof(stage_id,status,
            "source and regression evidence present" if status=="TESTED" else "local proof evidence incomplete",evidence))
    stages.extend((
      StageProof("MT5_TERMINAL_BINDING","DEMO_PROOF_REQUIRED","requires manual MT5 and broker session evidence",("XM","GOLD#","manual terminal")),
      StageProof("BROKER_ORDER_LIFECYCLE","DEMO_PROOF_REQUIRED","cannot be proven by an offline audit",("order result code","SL/TP acknowledgement","close acknowledgement")),
      StageProof("LIVE_SLIPPAGE_AND_FILL","LIVE_PROOF_REQUIRED","requires explicitly authorized real-market observation",("spread","slippage","partial fill","latency")),
      StageProof("LIVE_PROFITABILITY","LIVE_PROOF_REQUIRED","software tests cannot certify profitability",("sample size","drawdown","cost-adjusted expectancy")),
    ))
    internal_failed=tuple(item.stage_id for item in stages if item.status=="BLOCKED")
    return {"schema":"afip.a26.end_to_end_operational_proof.v1",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),"project_root":str(root),
      "status":"PASS_WITH_EXTERNAL_PROOF_REQUIRED" if not internal_failed and a25["status"]=="PASS" else "BLOCKED",
      "live_trading_certified":False,"profitability_certified":False,"orders_sent":False,
      "mt5_imported":False,"source_modified":False,"a25_status":a25["status"],
      "internal_failed_stages":internal_failed,"stages":[asdict(item) for item in stages]}


def main(argv: Iterable[str]|None=None)->int:
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--project-root",required=True)
    parser.add_argument("--output");parser.add_argument("--strict",action="store_true");args=parser.parse_args(argv)
    report=build_proof(Path(args.project_root));encoded=json.dumps(report,indent=2,ensure_ascii=False)
    if args.output:
        output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(encoded+"\n",encoding="utf-8")
    print(encoded);return 1 if args.strict and report["status"]=="BLOCKED" else 0


if __name__=="__main__": raise SystemExit(main())
