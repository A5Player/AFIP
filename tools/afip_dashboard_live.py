from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from afip.dashboard_ui.live_service import run_live_dashboard

def main() -> int:
    parser=argparse.ArgumentParser(description='AFIP live four-page dashboard')
    parser.add_argument('--root', default='.')
    parser.add_argument('--interval', type=int, default=10)
    parser.add_argument('--config', default='config/four_profile_demo.json')
    args=parser.parse_args()
    root=Path(args.root).resolve()
    import os
    os.chdir(root)
    run_live_dashboard(root/'runtime'/'dashboard', args.interval, root/args.config)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
