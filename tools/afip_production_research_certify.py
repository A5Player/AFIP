from __future__ import annotations
import argparse, json
from pathlib import Path
from afip.production_research_certification import CertificationPolicy, ProductionResearchCertification

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--walk-forward", required=True)
    parser.add_argument("--ranking", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--policy", default="config/production_research_certification/policy.json")
    args = parser.parse_args()
    policy = CertificationPolicy(**read(args.policy))
    report = ProductionResearchCertification(policy).certify(read(args.dataset), read(args.walk_forward), read(args.ranking))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Production research certification: {report['status']}")
    return 0 if report["status"] == "CERTIFIED" else 2
if __name__ == "__main__":
    raise SystemExit(main())
