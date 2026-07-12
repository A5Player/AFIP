"""
AFIP CLI launcher.

Official runtime entry point for AFIP V1.

Commands:
    python afip.py
    python afip.py simulate
    python afip.py mt5-check
    python afip.py run-locked-simulation [interval_seconds] [maximum_cycles]
"""

from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parent


def _load_cli_main(module_name: str, filename: str):
    cli_path = ROOT / "afip" / "cli" / filename
    spec = importlib.util.spec_from_file_location(module_name, cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load AFIP CLI module: {cli_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.main


def _load_cli_simulate_main():
    return _load_cli_main("afip_cli_simulate", "simulate.py")


def _load_cli_mt5_check_main():
    return _load_cli_main("afip_cli_mt5_check", "mt5_check.py")


def _print_help() -> None:
    print("AFIP — Automated Financial Intelligence Platform")
    print("Official command launcher: python afip.py <command>")
    print("")
    print("Available commands:")
    print("  simulate        Run safe simulation pipeline")
    print("  mt5-check       Check real MT5 data connection fallback safely")
    print("  run-locked-simulation  Run continuous locked simulation acceptance")
    print("  help            Show this help")


def main():
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "simulate"

    if command in ("help", "-h", "--help"):
        _print_help()
        return

    if command == "simulate":
        simulate_main = _load_cli_simulate_main()
        simulate_main()
        return

    if command in ("mt5-check", "mt5-data-check"):
        symbol = sys.argv[2] if len(sys.argv) > 2 else "GOLD#"
        mt5_check_main = _load_cli_mt5_check_main()
        mt5_check_main(symbol=symbol)
        return

    if command in ("run-locked-simulation", "locked-simulation"):
        from afip.locked_simulation_runtime import LockedSimulationConfig, LockedSimulationRunner

        interval_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
        maximum_cycles = int(sys.argv[3]) if len(sys.argv) > 3 else None
        config = LockedSimulationConfig(
            interval_seconds=interval_seconds,
            maximum_cycles=maximum_cycles,
        )
        print("=== AFIP Version 1.0 — Locked Simulation Runtime ===")
        print(f"Interval  : {config.interval_seconds} sec")
        print(f"Max Cycles: {config.maximum_cycles or 'UNLIMITED'}")
        print("Execution : LOCKED_SIMULATION_ONLY")
        print("Order     : NO_ORDER_SENT")
        print("Stop      : Ctrl+C")
        summary = LockedSimulationRunner(config).run()
        print(f"Completed : {summary.completed_cycles} cycles")
        print(f"Failures  : {summary.failed_cycles}")
        print("Execution : LOCKED_SIMULATION_ONLY | NO_ORDER_SENT")
        return

    print(f"Unknown AFIP command: {command}")
    print("Available commands: simulate, mt5-check, run-locked-simulation, help")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
