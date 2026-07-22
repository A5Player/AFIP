from __future__ import annotations
import argparse, json, time
from pathlib import Path
from afip.phase_v_major import PhaseVMajorRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP Phase V historical-to-live research runtime")
    parser.add_argument("command", choices=("run-once", "run-forever", "status", "arm-live", "disarm-live"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    runtime = PhaseVMajorRuntime(Path(args.root))
    if args.command == "run-once":
        print(json.dumps(runtime.run_once().as_dict(), ensure_ascii=False, indent=2)); return 0
    if args.command == "status":
        path = runtime.status_path
        print(path.read_text(encoding="utf-8") if path.exists() else json.dumps({"status":"NOT_STARTED"}, indent=2)); return 0
    if args.command == "arm-live":
        print(runtime.arm_live(args.confirmation)); return 0
    if args.command == "disarm-live":
        print(json.dumps({"disarmed": runtime.disarm_live()})); return 0
    config = runtime.config(); interval = max(60, int(config["continuous_interval_seconds"]))
    stop = runtime.root / "runtime/control/stop_phase_v_major.flag"
    stop.parent.mkdir(parents=True, exist_ok=True)
    while not stop.exists():
        runtime.run_once()
        for _ in range(interval // 5):
            if stop.exists(): break
            time.sleep(5)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
