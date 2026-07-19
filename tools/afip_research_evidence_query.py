from __future__ import annotations
import argparse, json
from pathlib import Path
from afip.research_evidence_consumer import EvidenceConsumer, EvidenceQuery

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--pattern-id", required=True)
    parser.add_argument("--market-regime", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--volatility-band", required=True)
    parser.add_argument("--trading-cost-band", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("top_overall", [])
    result = EvidenceConsumer(rows).query(EvidenceQuery(
        args.pattern_id, args.market_regime, args.session,
        args.volatility_band, args.trading_cost_band
    ))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
