"""Refresh live MT5 profile snapshots and rebuild the four-page dashboard."""
from __future__ import annotations
import argparse, time
from pathlib import Path
from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager
from afip.dashboard_ui.launcher import launch_three_dashboards


def run_once(root: Path) -> None:
    manager = MT5MultiTerminalConnectionManager(root / 'config' / 'four_profile_demo.json')
    report = manager.check(reconnect_attempts=1)
    print(f"🔌 MT5 live snapshot: {report['connected_profiles']}/{report['checked_profiles']} connected", flush=True)
    launch_three_dashboards(root / 'runtime' / 'dashboard', project_root=root)
    print(f"📊 Dashboard updated: {root / 'runtime' / 'dashboard' / 'afip_dashboard.html'}", flush=True)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--interval-seconds', type=int, default=10)
    parser.add_argument('--once', action='store_true')
    args=parser.parse_args(); root=Path(args.root).resolve()
    if args.once:
        run_once(root); return 0
    while True:
        started=time.monotonic()
        try: run_once(root)
        except KeyboardInterrupt: return 0
        except Exception as exc: print(f"⛔ Dashboard refresh failed: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(max(2, args.interval_seconds-(time.monotonic()-started)))
if __name__=='__main__': raise SystemExit(main())
