from __future__ import annotations
import argparse, json, time
from pathlib import Path
from afip.final_integration import (
    ArchitectureRegistry, FinalIntegrationRuntime, UnifiedDashboardAuthority, UnifiedResearchEngine
)
from afip.final_integration.io import atomic_json, utc_now


def _sleep_until(stop: Path, seconds: int) -> None:
    for _ in range(max(1, seconds)):
        if stop.exists():
            return
        time.sleep(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=(
        "start", "stop", "status", "dashboard", "dashboard-forever",
        "research-once", "research-forever", "architecture",
    ))
    parser.add_argument("--root", default=".")
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    runtime = FinalIntegrationRuntime(root)

    if args.command == "start":
        value = runtime.start().as_dict()
    elif args.command == "stop":
        value = runtime.stop().as_dict()
    elif args.command == "status":
        value = runtime.status().as_dict()
    elif args.command == "dashboard":
        value = {"dashboard": str(UnifiedDashboardAuthority(root).build())}
    elif args.command == "architecture":
        value = ArchitectureRegistry(root).inspect().as_dict()
    elif args.command == "research-once":
        value = UnifiedResearchEngine(root).run_once()
    elif args.command == "dashboard-forever":
        from afip.dashboard_ui.dashboard_authority import DashboardAuthority
        authority = DashboardAuthority()
        stop = root / "runtime/control/final_integration/stop_dashboard_runtime.flag"
        status_path = root / "runtime/control/final_integration/dashboard_runtime_status.json"
        cycles = 0
        try:
            authority.build_all(root / "runtime/dashboard", project_root=root)
            while not stop.exists():
                started = time.perf_counter()
                paths = authority.build_live(root / "runtime/dashboard", project_root=root)
                cycles += 1
                atomic_json(status_path, {
                    "schema_version": "afip-dashboard-background.v1",
                    "status": "RUNNING",
                    "cycle": cycles,
                    "updated_at_utc": utc_now(),
                    "duration_seconds": round(time.perf_counter() - started, 3),
                    "refresh_interval_seconds": max(2, args.interval),
                    "pages": {key: str(path.relative_to(root)) for key, path in paths.items()},
                    "execution_authority": False,
                    "order_send_called": False,
                    "blocks_trading": False,
                })
                _sleep_until(stop, max(2, args.interval))
            value = {"status": "STOPPED", "cycles": cycles}
        except Exception as exc:
            value = {"status": "ERROR", "cycles": cycles, "reason": f"{type(exc).__name__}: {exc}"}
            atomic_json(status_path, {**value, "updated_at_utc": utc_now(), "execution_authority": False})
    else:
        engine = UnifiedResearchEngine(root)
        stop = root / "runtime/control/final_integration/stop_research_runtime.flag"
        cycles = 0
        while not stop.exists():
            engine.run_once()
            cycles += 1
            _sleep_until(stop, max(5, args.interval))
        value = {"status": "STOPPED", "cycles": cycles}

    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))
    return 0 if value.get("status") != "ERROR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
