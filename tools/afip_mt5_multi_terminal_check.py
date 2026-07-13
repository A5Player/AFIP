from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager

def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP isolated MT5 multi-terminal connection check")
    parser.add_argument("--config", default="config/four_profile_demo.json")
    parser.add_argument("--profiles", nargs="*", default=None)
    parser.add_argument("--reconnect-attempts", type=int, default=1)
    args = parser.parse_args()
    report = MT5MultiTerminalConnectionManager(args.config).check(args.profiles, max(0, args.reconnect_attempts))
    print(json.dumps(report, indent=2, default=str))
    print("Execution: LOCKED_SIMULATION_ONLY | NO_ORDER_SENT")
    bad = {"BLOCKED", "DISCONNECTED", "DEGRADED", "ERROR"}
    return 2 if report["validation_errors"] or any(p["connection_status"] in bad for p in report["profiles"] if p["enabled"]) else 0

if __name__ == "__main__":
    raise SystemExit(main())
