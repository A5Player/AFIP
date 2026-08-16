"""Operate the A37 incremental research pipeline without execution authority."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

# Direct-script compatibility: Python otherwise exposes only the tools folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from afip.final_integration.continuous_research import ContinuousResearchPipeline


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=("run-once","status"));parser.add_argument("--project-root",required=True)
    args=parser.parse_args();pipeline=ContinuousResearchPipeline(Path(args.project_root))
    result=pipeline.run_once() if args.command=="run-once" else (
        json.loads(pipeline.state_path.read_text(encoding="utf-8")) if pipeline.state_path.exists() else
        {"status":"NOT_STARTED","execution_authority":"NONE","orders_sent":False})
    print(json.dumps(result,indent=2,ensure_ascii=False));return 1 if result.get("status")=="ERROR" else 0


if __name__=="__main__":raise SystemExit(main())
