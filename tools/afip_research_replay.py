from __future__ import annotations
import argparse, importlib, json
from pathlib import Path
from afip.research_replay_engine import ReplayEngine, ReplayPolicy

def load_rows(path):
    p = Path(path)
    if p.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data["events"]

def load_callable(spec):
    module_name, function_name = spec.split(":", 1)
    return getattr(importlib.import_module(module_name), function_name)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--decision-function", required=True, help="module:function")
    parser.add_argument("--output", required=True)
    parser.add_argument("--policy", default="config/research_replay_engine/policy.json")
    args = parser.parse_args()
    policy = ReplayPolicy(**json.loads(Path(args.policy).read_text(encoding="utf-8")))
    report = ReplayEngine(policy).run(load_rows(args.input), load_callable(args.decision_function))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Replay status: {report['status']}")
    print(f"Processed events: {report['processed_event_count']}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
