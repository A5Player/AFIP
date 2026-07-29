from __future__ import annotations
import argparse, json
from pathlib import Path
from afip.final_production_certification import FinalProductionCertificationRuntime


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default="runtime/certification/afip_v1_final_production_certification.json")
    args=parser.parse_args()
    result=FinalProductionCertificationRuntime(args.project_root).evaluate()
    out=Path(args.project_root)/args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "source_contract_status": result["source_contract_certification"]["status"], "output": str(out)}, ensure_ascii=False, indent=2))
    return 0 if result["source_contract_certification"]["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
