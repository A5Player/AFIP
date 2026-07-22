"""AFIP live dashboard service.

Refreshes read-only MT5 account health and regenerates the four dashboard pages.
It never sends orders or changes execution authority.
"""
from __future__ import annotations

from pathlib import Path
import time

from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager
from .launcher import launch_three_dashboards
from .home import HOME_FILENAME


def run_live_dashboard(
    output_directory: str | Path = "runtime/dashboard",
    interval_seconds: int = 10,
    config_path: str | Path = "config/four_profile_demo.json",
) -> None:
    interval = max(5, int(interval_seconds))
    output = Path(output_directory)
    while True:
        started = time.perf_counter()
        try:
            report = MT5MultiTerminalConnectionManager(config_path).check(reconnect_attempts=0)
            print(
                f"MT5 live snapshot: {report['connected_profiles']}/{report['checked_profiles']} connected",
                flush=True,
            )
        except Exception as exc:
            print(f"MT5 live snapshot failed: {type(exc).__name__}: {exc}", flush=True)
        try:
            p1, p2, p3 = launch_three_dashboards(output, project_root=Path.cwd())
            elapsed = time.perf_counter() - started
            print(
                f"Dashboard updated in {elapsed:.2f}s: {p1.parent / HOME_FILENAME}",
                flush=True,
            )
        except Exception as exc:
            print(f"Dashboard build failed: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(interval)
