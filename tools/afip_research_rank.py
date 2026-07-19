from __future__ import annotations
import argparse, json
from pathlib import Path
from afip.research_ranking import RankingPolicy, ResearchRankingEngine

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--policy", default="config/research_ranking/policy.json")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("results", [])
    policy = RankingPolicy(**json.loads(Path(args.policy).read_text(encoding="utf-8")))
    report = ResearchRankingEngine(policy).rank(rows, args.limit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Evaluated: {report['evaluated_count']}")
    print(f"Certified candidates: {len(report['top_overall'])}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
