from __future__ import annotations
import argparse, json
from pathlib import Path
from afip.research_dashboard import build_research_dashboard

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="runtime/dashboard/afip_research_dashboard.html")
    args = parser.parse_args()
    report = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_research_dashboard(report), encoding="utf-8")
    print(f"Research dashboard generated: {output}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
