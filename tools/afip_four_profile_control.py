from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from afip.four_profile_operations import FourProfileOperationalRuntime, FourProfileSupervisor

def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP four-profile locked-simulation operations")
    parser.add_argument("command", choices=("status", "prepare", "launch-mt5", "start-selected", "stop-selected", "restart-selected", "start-all", "stop-all"))
    parser.add_argument("--config", default="config/four_profile_demo.json")
    parser.add_argument("--profiles", nargs="*", default=None)
    args = parser.parse_args()
    operations = FourProfileOperationalRuntime(args.config)
    supervisor = FourProfileSupervisor(args.config)
    if args.command == "status": report = supervisor.status()
    elif args.command == "prepare": report = operations.prepare_isolation(args.profiles)
    elif args.command == "launch-mt5": report = operations.launch_mt5(args.profiles)
    elif args.command == "start-selected": report = supervisor.start(args.profiles)
    elif args.command == "stop-selected": report = supervisor.stop(args.profiles)
    elif args.command == "restart-selected": report = supervisor.restart(args.profiles)
    elif args.command == "start-all": report = supervisor.start()
    else: report = supervisor.stop()
    print(json.dumps(report.as_dict(), indent=2, default=str))
    print("Execution: LOCKED_SIMULATION_ONLY | NO_ORDER_SENT")
    return 0 if not report.validation_errors else 2

if __name__ == "__main__": raise SystemExit(main())
