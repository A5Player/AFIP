from __future__ import annotations

import argparse
import signal
import time
from pathlib import Path

from afip.dashboard_ui.dashboard_authority import DashboardAuthority
from afip.final_integration.io import atomic_json, utc_now

_STOP = False


def _stop(*_: object) -> None:
    global _STOP
    _STOP = True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--fast-interval", type=float, default=10.0)
    parser.add_argument("--full-interval", type=float, default=60.0)
    # Backward-compatible alias used by older launchers.
    parser.add_argument("--interval", type=float, default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    fast_interval = max(5.0, float(args.interval if args.interval is not None else args.fast_interval))
    full_interval = max(fast_interval, float(args.full_interval))

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _stop)
        except Exception:
            pass

    status_path = root / "runtime/dashboard/dashboard_monitor_status.json"
    authority = DashboardAuthority()
    fast_cycles = 0
    full_cycles = 0
    last_full_started = 0.0

    while not _STOP:
        cycle_started = time.monotonic()
        try:
            # Full build is deliberately infrequent.  It refreshes profiles,
            # intelligence, cross-market and control-center pages.
            due_full = last_full_started == 0.0 or (cycle_started - last_full_started) >= full_interval
            if due_full:
                authority.build_all(output_directory=root / "runtime/dashboard", project_root=root)
                full_cycles += 1
                last_full_started = cycle_started
                build_scope = "FULL"
            else:
                # Fast build refreshes only Home, Research and Data Loading.
                authority.build_live(output_directory=root / "runtime/dashboard", project_root=root)
                fast_cycles += 1
                build_scope = "FAST"

            atomic_json(status_path, {
                "status": "RUNNING",
                "cycles": fast_cycles + full_cycles,
                "fast_cycles": fast_cycles,
                "full_cycles": full_cycles,
                "last_build_scope": build_scope,
                "dashboard": str(root / "runtime/dashboard/afip_dashboard.html"),
                "updated_at_utc": utc_now(),
                "refresh_interval_seconds": fast_interval,
                "fast_refresh_interval_seconds": fast_interval,
                "full_refresh_interval_seconds": full_interval,
                "execution_authority": False,
                "order_send_called": False,
            })
        except Exception as exc:
            atomic_json(status_path, {
                "status": "ERROR",
                "cycles": fast_cycles + full_cycles,
                "fast_cycles": fast_cycles,
                "full_cycles": full_cycles,
                "reason": f"{type(exc).__name__}:{exc}",
                "updated_at_utc": utc_now(),
                "refresh_interval_seconds": fast_interval,
                "fast_refresh_interval_seconds": fast_interval,
                "full_refresh_interval_seconds": full_interval,
                "execution_authority": False,
                "order_send_called": False,
            })

        elapsed = time.monotonic() - cycle_started
        time.sleep(max(0.2, fast_interval - elapsed))

    atomic_json(status_path, {
        "status": "STOPPED",
        "cycles": fast_cycles + full_cycles,
        "fast_cycles": fast_cycles,
        "full_cycles": full_cycles,
        "updated_at_utc": utc_now(),
        "refresh_interval_seconds": fast_interval,
        "fast_refresh_interval_seconds": fast_interval,
        "full_refresh_interval_seconds": full_interval,
        "execution_authority": False,
        "order_send_called": False,
        "pid": None,
        "process_id": None,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
