from __future__ import annotations
import argparse, json
from pathlib import Path
from afip.walk_forward_research import WalkForwardPolicy, WalkForwardResearchEngine

def load_rows(path: Path):
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data["trades"]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--policy", default="config/walk_forward_research/policy.json")
    args = parser.parse_args()
    policy = WalkForwardPolicy(**json.loads(Path(args.policy).read_text(encoding="utf-8")))
    report = WalkForwardResearchEngine(policy).run(load_rows(Path(args.input)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Walk-forward status: {report['status']}")
    print(f"Windows: {report['window_count']}")
    print(f"Output: {output}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
